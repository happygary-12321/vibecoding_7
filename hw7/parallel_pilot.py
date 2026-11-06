"""Unprofiled, sequential same-world correctness and scaling experiments.

Run as a module from the repository root. Existing labels are never overwritten.
"""
import os
from .parallel import THREAD_LIMITS
os.environ.update(THREAD_LIMITS)  # Before importing scipy/numpy in this interpreter.

import argparse
from contextlib import nullcontext
from dataclasses import asdict
import json
from pathlib import Path
import statistics
import sys
import tempfile
import time
import traceback
from . import profiling as provenance
from .model import Options
from .parallel import ParallelDetector
from .scene import make_scene
from .world import step_world

ROOT = provenance.ROOT
OUTPUT = ROOT/'hw7/evidence/parallel_pilot'
MANIFEST = OUTPUT/'compatibility_v3.json'
STATES = {
    'peak': 'hw7/evidence/profile_serial/full_profile_budgeted/checkpoints/step_000389.pickle',
    'impacts': 'hw7/evidence/profile_serial/states_0600/checkpoints/step_000600.pickle',
    'pile': 'hw7/evidence/profile_serial/states_1440_confined/checkpoints/step_001440.pickle',
}


def configure_temp():
    directory = OUTPUT/'native_tmp/parent'
    directory.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(directory)
    os.environ['TMP'] = os.environ['TEMP'] = str(directory)


def approve():
    old = json.loads((ROOT/'hw7/evidence/profile_serial/peak_plain/metadata.json').read_text(encoding='utf-8'))['source']
    current = provenance.sources()
    changed = [key for key, value in old['hashes'].items() if current['hashes'].get(key) != value]
    physical_changed = [key for key in changed if key.startswith('Hw5/') or key in
                        {'hw7/'+f for f in provenance.PHYSICS_FILES}]
    if set(physical_changed) != {'hw7/world.py', 'hw7/falling_objects.py'}:
        raise ValueError(f'unexpected arithmetic source changes: {physical_changed}')
    # This is an explicit audited dispatch-only approval, NOT a general skip-hash flag.
    if MANIFEST.exists():
        raise FileExistsError('compatibility manifest already exists; do not replace historical approval')
    provenance.atomic_json(MANIFEST, dict(historical_physics_source_id=old['physics_source_id'],
        approved_current_physics_source_id=current['physics_source_id'], approved_current_hashes=current['hashes'],
        changed_historical_files=changed, unchanged_arithmetic_files=[k for k in old['hashes'] if k not in changed],
        reason='World changes add detector dispatch/lifecycle and result metadata; CLI adds backend controls. '
               'All original collision/manifold/solver/state/scene/Hw5 arithmetic hashes unchanged. '
               'Replay historical serial 30-step world/report digests before performance trials.',
        historical_source=old))


def load(scene, opts):
    if scene == 'full':
        return make_scene(7), dict(initial_seed=7, step=0)
    return provenance.load_checkpoint(STATES[scene], opts, 7, compatibility=MANIFEST)


def interval(start, opts, steps, detector):
    world, reports = start, []
    started = time.perf_counter()
    for _ in range(steps):
        world, report = step_world(world, opts, backend='parallel' if detector else 'serial', detector=detector)
        reports.append(report)
    seconds = time.perf_counter()-started
    return world, tuple(reports), seconds


def trial(folder, label, scene, workers, batch, steps, warmup, opts, threshold):
    path = folder/(label+'.json')
    record = dict(complete=False, status='starting', scene=scene, workers=workers, batch_size=batch,
                  backend='parallel' if workers else 'serial', steps=steps, warmup_steps=warmup,
                  serial_threshold=threshold)
    provenance.atomic_json(path, record)
    started = time.perf_counter()
    pool = None
    try:
        start, manifest = load(scene, opts)
        record['checkpoint_provenance'] = manifest
        pool = ParallelDetector(workers, batch, threshold) if workers else None
        with pool if pool else nullcontext():
            if warmup:
                # Full-scene trials warm real collisions, then reset to step zero.
                warm_start = load('impacts', opts)[0] if scene == 'full' else start
                _, _, record['warmup_seconds'] = interval(warm_start, opts, warmup, pool)
            before_counts = dict(pool.counts) if pool else {}
            before_pairs = dict(pool.worker_pairs) if pool else {}
            world, reports, elapsed = interval(start, opts, steps, pool)
            record.update(physics_seconds=elapsed, start_step=start.step_count, end_step=world.step_count,
                          world_digest=provenance.digest(world), reports_digest=provenance.digest(world, reports),
                          value_digest=provenance.sha(json.dumps([asdict(world), [asdict(r) for r in reports]],
                                                    sort_keys=True, allow_nan=False).encode()),
                          contains_collision=any(r.manifolds for r in reports))
            if pool:
                record['measured_dispatch'] = {key: value-before_counts.get(key, 0) for key, value in pool.counts.items()}
                record['measured_worker_pairs'] = {key: value-before_pairs.get(key, 0) for key, value in pool.worker_pairs.items()}
        record.update(complete=True, status='complete')
    except BaseException as exc:
        record.update(status='interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed',
                      error=repr(exc), traceback=traceback.format_exc())
        raise
    finally:
        record['trial_total_seconds'] = time.perf_counter()-started
        record['pool'] = pool.statistics() if pool else None
        provenance.atomic_json(path, record)
    print(json.dumps({key: record.get(key) for key in
          ('scene', 'workers', 'batch_size', 'physics_seconds', 'trial_total_seconds', 'complete')}), flush=True)
    return record, world, reports


def compare(record, reference):
    # Pickle encodes object aliasing, which IPC may change without changing a
    # single value. Canonical dataclass JSON encodes values and preserves order.
    exact = (record['value_digest'] == reference['value_digest']) if 'value_digest' in reference else (
             record['world_digest'] == reference['world_digest'] and record['reports_digest'] == reference['reports_digest'])
    if not exact:
        raise AssertionError('exact serial/parallel world/report digest mismatch')
    return exact


def main():
    invocation_started = time.perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('approve', 'validate', 'screen', 'measure'))
    parser.add_argument('--label')
    parser.add_argument('--scenes', default='peak,impacts,pile')
    parser.add_argument('--backend', choices=('serial', 'parallel'), default='parallel')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--batch-size', type=int, default=4)
    parser.add_argument('--serial-threshold', type=int, default=0)
    parser.add_argument('--steps', type=int, default=30)
    parser.add_argument('--warmup-steps', type=int, default=4)
    parser.add_argument('--repeats', type=int, default=3)
    parser.add_argument('--reference-label', help='prior serial/validation label for exact value digest comparison')
    args = parser.parse_args()
    configure_temp()
    if args.action == 'approve':
        approve()
        return 0
    ParallelDetector(args.workers, args.batch_size, args.serial_threshold)
    if args.steps < 1 or args.warmup_steps < 0 or args.repeats < 1:
        parser.error('invalid steps/repeats')
    if not args.label or not args.label.replace('_', '').isalnum():
        parser.error('unique alphanumeric/underscore label required')
    scenes = args.scenes.split(',')
    if any(scene not in (*STATES, 'full') for scene in scenes):
        parser.error('unknown scene')
    if 'full' in scenes and args.steps != 2880:
        parser.error('full scene requires exactly 2880 steps')
    folder = OUTPUT/args.label
    folder.mkdir(exist_ok=False)
    opts = Options(dt=1/480)
    provenance.atomic_json(folder/'metadata.json', dict(command=[sys.executable, *sys.orig_argv[1:]],
        created_utc=provenance.stamp(), source=provenance.sources(), runtime=provenance.runtime(),
        options=asdict(opts), arguments=vars(args), compatibility=str(MANIFEST.relative_to(ROOT)),
        timing_scope='unprofiled perf_counter wall around entire stepping/report loop; includes dispatch, '
                     'IPC, gather, both barriers and serial solver; excludes load/setup/warmup/output/rendering',
        output_mode='headless; reports retained; no frame sampling, rendering or per-step output',
        warmup_policy='discard warmup, reset identical physical world/cache each trial; workers reused within trial',
        invocation_timer_scope='module main through results persistence; process imports/OS startup excluded; '
                               'use external caller wall timer for cold total invocation'))
    results = []
    try:
        for scene in scenes:
            if args.action == 'validate':
                serial, serial_world, serial_reports = trial(folder, scene+'_serial', scene, 0, 4, args.steps, 0, opts, 0)
                if scene != 'full' and args.steps == 30:
                    historical = json.loads((ROOT/f'hw7/evidence/profile_serial/{scene}_plain/run_00.json').read_text())
                    compare(serial, historical)
                parallel, parallel_world, parallel_reports = trial(folder, scene+'_parallel', scene, args.workers, args.batch_size, args.steps, 0, opts, 0)
                compare(parallel, serial)
                if serial_world != parallel_world or serial_reports != parallel_reports:
                    raise AssertionError('direct Python world/report equality failed')
                results.append(dict(scene=scene, historical_serial_exact=True, parallel_exact=True))
                # Save exact equality of full Python values, in addition to digests.
                # Digest includes world/cache and every retained StepReport.
            else:
                configs = [(0, 4), *[(w, b) for w in (2, 4, 8) for b in (4, 8)]] if args.action == 'screen' else [
                    (args.workers if args.backend == 'parallel' else 0, args.batch_size)]
                repeats = 1 if args.action == 'screen' else args.repeats
                samples = {(w, b): [] for w, b in configs}
                reference = None
                if args.reference_label:
                    reference_folder = OUTPUT/args.reference_label
                    candidates = [reference_folder/(scene+'_serial.json'),
                                  reference_folder/(scene+'_w0_b4_r0.json')]
                    reference = json.loads(next(p for p in candidates if p.is_file()).read_text())
                    if not reference['complete'] or reference['steps'] != args.steps:
                        raise ValueError('incomplete or mismatched reference workload')
                # Alternate config order across repetitions when screening; measure
                # supports one backend, with all raw results retained for paired review.
                for repeat in range(repeats):
                    for w, b in configs if repeat % 2 == 0 else list(reversed(configs)):
                        record, _, _ = trial(folder, f'{scene}_w{w}_b{b}_r{repeat}', scene, w, b, args.steps,
                                       args.warmup_steps, opts, args.serial_threshold)
                        if reference is None:
                            reference = record
                        compare(record, reference)
                        if w == 0 and scene != 'full' and args.steps == 30:
                            historical = json.loads((ROOT/f'hw7/evidence/profile_serial/{scene}_plain/run_00.json').read_text())
                            compare(record, historical)
                        samples[w, b].append(record['physics_seconds'])
                for (w, b), times in samples.items():
                    results.append(dict(scene=scene, workers=w, batch_size=b, raw_seconds=times,
                        median_seconds=statistics.median(times),
                        sample_stdev_seconds=statistics.stdev(times) if len(times) > 1 else None,
                        world_and_reports_exact=True))
        provenance.atomic_json(folder/'results.json', dict(complete=True, results=results,
            invocation_main_seconds=time.perf_counter()-invocation_started))
        return 0
    except BaseException as exc:
        provenance.atomic_json(folder/'failure.json', dict(complete=False, error=repr(exc), traceback=traceback.format_exc()))
        raise


if __name__ == '__main__':
    raise SystemExit(main())
