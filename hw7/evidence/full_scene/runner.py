"""Part 5 full-scene trial. Physics untouched; all retained output under hw7/."""
import os
from hw7.parallel import THREAD_LIMITS
os.environ.update(THREAD_LIMITS)  # Before any SciPy/NumPy import.

import argparse
from contextlib import nullcontext
from dataclasses import asdict
import json
from pathlib import Path
import pickle
import sys
import tempfile
import time
import traceback
from hw7 import profiling as p
from hw7.parallel import ParallelDetector
from hw7.parallel_pilot import MANIFEST, STATES
from hw7.model import Options
from hw7.scene import make_scene
from hw7.world import step_world, RunResult
from hw7.falling_objects import summary
from .audit import accept

OUTPUT = p.ROOT/'hw7/evidence/full_scene'
COHORT = OUTPUT/'cohort.json'


def harness_hashes():
    paths = sorted(OUTPUT.glob('*.py'))
    return {str(path.relative_to(p.ROOT)).replace('\\', '/'): p.sha(path.read_bytes()) for path in paths}


def configure():
    directory = OUTPUT/'native_tmp/parent'
    directory.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(directory)
    os.environ['TMP'] = os.environ['TEMP'] = str(directory)


def identity():
    return dict(source=p.sources(), harness_hashes=harness_hashes(), options=asdict(Options(dt=1/480)),
                seed=7, steps=2880, warmup_steps=30, workers=8, batch_size=4, serial_threshold=0,
                thread_limits=THREAD_LIMITS, journal_every=120,
                timing_scope='One continuous unprofiled wall span around 2880 step_world/report appends; '
                             'includes both barriers, IPC, dispatch/gather/synchronization, ordered solver, '
                             'and identical 120-step progress JSON/console writes. No resumed segments. '
                             'Excludes setup/loading, pool readiness, 30-step warmup, final hashes, '
                             'acceptance, realized-state/report export and shutdown.',
                output_mode='reports retained; no frames/snapshots/rendering/sleeping',
                warmup_policy='30 discarded steps from genuine step-600 cache; reuse workers; reset '
                              'to identical seed-7 step-0 world and EMPTY initial cache')


def verify_cohort():
    expected = json.loads(COHORT.read_text(encoding='utf-8'))['identity']
    current = json.loads(json.dumps(identity()))
    if expected != current:
        raise ValueError('cohort source/configuration drift: use a newly audited cohort, never mix results')
    return current


def preflight():
    configure()
    import numpy, scipy, matplotlib
    approval = json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert approval['approved_current_hashes'] == p.sources()['hashes']
    assert approval['approved_current_physics_source_id'] == p.sources()['physics_source_id']
    opts = Options(dt=1/480)
    warm, checkpoint = p.load_checkpoint(STATES['impacts'], opts, 7, compatibility=MANIFEST)
    assert warm.step_count == 600 and warm.cache
    initial = make_scene(7)
    original = json.loads((p.ROOT/'hw7/evidence/serial_default.json').read_text(encoding='utf-8'))
    assert json.loads(json.dumps(asdict(initial))) == original['initial']
    assert len(initial.bodies) == 35 and sum(not b.static for b in initial.bodies) == 30
    assert len([b for b in initial.bodies if b.static]) == 5 and not initial.cache
    record = dict(identity=identity(), runtime=p.runtime(), checkpoint=checkpoint,
        created_utc=p.stamp(), interpreter=sys.executable, python=sys.version,
        imported_versions=dict(numpy=numpy.__version__, scipy=scipy.__version__, matplotlib=matplotlib.__version__),
        initial_value_digest=p.sha(json.dumps(asdict(initial), sort_keys=True).encode()),
        initial_matches_accepted_seed7=True, accepted_original_options_match=original['options'] == json.loads(json.dumps(asdict(opts))),
        existing_complete_trials=[], production_physics_changed=False,
        audited_equivalent_reason='Original script has right schedule but lacks incremental journal and '
                                 'saved state/reports/acceptance output; new evidence-only runner adds those '
                                 'outside timing, except identical small progress writes inside stepping span.')
    assert record['accepted_original_options_match']
    if COHORT.exists():
        verify_cohort()
        return
    p.atomic_json(COHORT, record)
    print(json.dumps(record, indent=2), flush=True)


def canonical(world, reports):
    # Exactly the canonical representation used in Part 4.
    values = [asdict(world), [asdict(r) for r in reports]]
    return p.sha(json.dumps(values, sort_keys=True, allow_nan=False).encode())


def stepping(start, opts, steps, pool, journal=None):
    world, reports, journal_io = start, [], 0.
    started = time.perf_counter()
    for index in range(steps):
        world, report = step_world(world, opts, backend='parallel' if pool else 'serial', detector=pool)
        reports.append(report)
        if journal is not None and ((index+1) % 120 == 0 or index+1 == steps):
            io_start = time.perf_counter()
            state = dict(status='running', complete=False, physics_complete=False, pid=os.getpid(),
                         requested_steps=steps, completed_steps=index+1, world_step=world.step_count,
                         stepping_elapsed_seconds=time.perf_counter()-started, updated_utc=p.stamp(),
                         max_penetration_so_far=max(r.penetration_after for r in reports))
            p.atomic_json(journal, state)
            print(json.dumps(state), flush=True)
            journal_io += time.perf_counter()-io_start
    elapsed = time.perf_counter()-started
    return world, tuple(reports), elapsed, journal_io


def run(label, backend, reference):
    configure()
    cohort = verify_cohort()
    if not label.replace('_', '').isalnum():
        raise ValueError('invalid trial label')
    folder = OUTPUT/label
    folder.mkdir(exist_ok=False)
    opts, initial = Options(dt=1/480), make_scene(7)
    started = time.perf_counter()
    record = dict(label=label, backend=backend, status='starting', complete=False, physics_complete=False,
                  command=[sys.executable, *sys.orig_argv[1:]], identity=cohort, runtime=p.runtime(),
                  initial_cache_manifolds=len(initial.cache), initial_step=0, seed=7, steps=2880,
                  created_utc=p.stamp(), pid=os.getpid(), resumed=False)
    p.atomic_json(folder/'metadata.json', record)
    p.atomic_json(folder/'record.json', record)
    pool = ParallelDetector(8, 4, 0) if backend == 'parallel' else None
    try:
        expected_runtime = json.loads(COHORT.read_text())['runtime']
        assert record['runtime'].get('effective_affinity') == expected_runtime.get('effective_affinity')
        assert all(record['runtime']['thread_environment'][k] == v for k, v in THREAD_LIMITS.items())
        warm_start, checkpoint = p.load_checkpoint(STATES['impacts'], opts, 7, compatibility=MANIFEST)
        record['warmup_checkpoint'] = checkpoint
        with pool if pool else nullcontext():
            _, _, record['warmup_seconds'], _ = stepping(warm_start, opts, 30, pool)
            before_counts = dict(pool.counts) if pool else {}
            before_pairs = dict(pool.worker_pairs) if pool else {}
            world, reports, elapsed, journal_io = stepping(initial, opts, 2880, pool, folder/'journal.json')
            record.update(physics_seconds=elapsed, journal_io_seconds=journal_io, physics_complete=True,
                          completed_steps=world.step_count, status='postprocessing', complete=False)
            p.atomic_json(folder/'record.json', record)
            if pool:
                record['measured_dispatch'] = {k: v-before_counts.get(k, 0) for k, v in pool.counts.items()}
                record['measured_worker_pairs'] = {k: v-before_pairs.get(k, 0) for k, v in pool.worker_pairs.items()}
        # Every final hash/export/acceptance operation is OUTSIDE stepping time.
        post = time.perf_counter()
        result = RunResult(world, reports, (), elapsed, opts.dt)
        realized = dict(summary=summary(result), options=asdict(opts), initial=asdict(initial), final=asdict(world))
        p.atomic_json(folder/'realized.json', realized)
        replay = dict(initial=initial, world=world, reports=reports, options=opts, physics_seconds=elapsed)
        payload = pickle.dumps(replay, protocol=5)
        (folder/'replay.pickle').write_bytes(payload)
        record['replay_sha256'] = p.sha(payload)
        record['value_digest'] = canonical(world, reports)
        record['report_count'] = len(reports)
        assert len(reports) == 2880
        audit = accept(realized)
        # Independently classify actual retained impulse rows by fixed static IDs.
        bb = sum(i.normal_impulse > 1e-10 and i.b < 30 for r in reports for i in r.impulses)
        bw = sum(i.normal_impulse > 1e-10 and i.b >= 30 for r in reports for i in r.impulses)
        assert bb == realized['summary']['body_body_impulse_rows'] and bw == realized['summary']['body_bin_impulse_rows']
        p.atomic_json(folder/'acceptance.json', audit)
        record['acceptance'] = audit
        record['reference'] = reference
        if reference:
            previous = json.loads((OUTPUT/reference/'record.json').read_text(encoding='utf-8'))
            assert previous['complete'] and previous['identity'] == cohort
            record['exact_reference_match'] = record['value_digest'] == previous['value_digest']
            if not record['exact_reference_match']:
                raise AssertionError('FULL SCENE EXACT WORLD/CACHE/REPORT MISMATCH; stop schedule')
        else:
            record['exact_reference_match'] = True
        verify_cohort()
        record.update(final_output_and_audit_seconds=time.perf_counter()-post, complete=True, status='complete',
                      finished_utc=p.stamp())
    except BaseException as exc:
        record.update(complete=False, status='interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed',
                      error=repr(exc), traceback=traceback.format_exc(), finished_utc=p.stamp())
        raise
    finally:
        record['pool'] = pool.statistics() if pool else None
        record['trial_total_seconds'] = time.perf_counter()-started
        p.atomic_json(folder/'record.json', record)
    print(json.dumps(dict(event='trial_complete', label=label, seconds=elapsed, digest=record['value_digest'],
                         accepted=True, exact=record['exact_reference_match'])), flush=True)


def replay(label):
    folder = OUTPUT/label
    record = json.loads((folder/'record.json').read_text(encoding='utf-8'))
    payload = (folder/'replay.pickle').read_bytes()
    assert p.sha(payload) == record['replay_sha256']
    data = pickle.loads(payload)  # Only trusted locally generated evidence.
    result = RunResult(data['world'], data['reports'], (), data['physics_seconds'], data['options'].dt)
    realized = dict(summary=summary(result), options=asdict(data['options']), initial=asdict(data['initial']), final=asdict(data['world']))
    assert canonical(data['world'], data['reports']) == record['value_digest']
    audit = accept(realized)
    path = folder/'replayed_acceptance.json'
    if path.exists():
        assert json.loads(path.read_text(encoding='utf-8')) == audit
    else:
        p.atomic_json(path, audit)
    print(json.dumps(dict(label=label, replayed_acceptance=True, value_digest=record['value_digest'])), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('preflight', 'trial', 'replay'))
    parser.add_argument('--label')
    parser.add_argument('--backend', choices=('serial', 'parallel'))
    parser.add_argument('--reference')
    args = parser.parse_args()
    if args.action == 'preflight':
        preflight()
    elif args.action == 'replay':
        replay(args.label)
    else:
        run(args.label, args.backend, args.reference)
