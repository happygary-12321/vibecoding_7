"""Serial-only profiling tools. No parallel physics backend is implemented here.

Checkpoint pickle files are trusted local artifacts, never arbitrary downloads.
All file writes are confined to hw7/evidence/profile_serial. See PROFILE.md.
"""
import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager, nullcontext
import cProfile
from dataclasses import asdict
from datetime import datetime, timezone
import functools
import hashlib
import importlib.metadata
import io
import json
import locale
import os
from pathlib import Path
import pickle
import platform
import pstats
import statistics
import subprocess
import sys
import tempfile
import time
import traceback

from . import world as physics, manifolds as patches
from .model import Options
from .scene import make_scene

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT/'hw7/evidence/profile_serial'
PHYSICS_FILES = ('__init__.py', 'math3.py', 'model.py', 'collision.py', 'manifolds.py',
                 'solver.py', 'world.py', 'scene.py', 'falling_objects.py', 'rendering.py', 'parallel.py')


def confine_native_temporary_files():
    # SciPy/Qhull creates a temporary error stream for every constructed hull.
    # Set this before ANY measured Hull call, including discarded warmups.
    path = OUTPUT/'native_tmp'
    path.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(path)
    os.environ['TMP'] = os.environ['TEMP'] = str(path)
    return str(path)


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding='utf-8')
    temporary.replace(path)


def sources():
    paths = sorted(set((ROOT/'Hw5').glob('*.py')) | set((ROOT/'hw7').glob('*.py')))
    hashes = {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p.read_bytes()) for p in paths}
    physical = {k: v for k, v in hashes.items() if k.startswith('Hw5/') or k in {'hw7/'+f for f in PHYSICS_FILES}}
    return dict(hashes=hashes, source_id=sha(json.dumps(hashes, sort_keys=True).encode()),
                physics_source_id=sha(json.dumps(physical, sort_keys=True).encode()))


def command_output(command):
    try:
        p = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=15)
        return dict(command=command, returncode=p.returncode, stdout=p.stdout.strip(), stderr=p.stderr.strip())
    except Exception as exc:
        return dict(command=command, error=repr(exc))


def runtime():
    versions = {}
    for package in ('numpy', 'scipy', 'matplotlib', 'psutil', 'threadpoolctl', 'cython', 'numba'):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    result = dict(python=sys.version, executable=sys.executable, platform=platform.platform(),
                  logical_cpu_count=os.cpu_count(), versions=versions, native_temp_directory=tempfile.gettempdir(),
                  thread_environment={k: os.environ.get(k) for k in
                                      ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
                                       'NUMEXPR_NUM_THREADS', 'OMP_DYNAMIC', 'OMP_PROC_BIND')})
    try:
        import psutil
        result['physical_cpu_count_psutil'] = psutil.cpu_count(logical=False)
        result['effective_affinity'] = psutil.Process().cpu_affinity()
        battery = psutil.sensors_battery()
        result['battery'] = None if battery is None else dict(percent=battery.percent, power_plugged=battery.power_plugged)
    except (ImportError, AttributeError, OSError) as exc:
        result['optional_psutil_error'] = repr(exc)
    return result


def metadata(args, opts):
    return dict(created_utc=stamp(), exact_command=[sys.executable, *sys.orig_argv[1:]],
                arguments=vars(args), options=asdict(opts), seed=args.seed, source=sources(), runtime=runtime(),
                git_head=command_output(['git', 'rev-parse', 'HEAD']),
                output_mode='physics-only; no rendering, snapshots or GUI',
                timing_scope='sum of unprofiled/profiled wall spans around step_world and report append; '
                             'excludes imports, checkpoint load/preparation, warmup, counters/graph analysis and evidence I/O',
                reports_retained=True, frame_sampling=False)


def digest(world, reports=()):
    return sha(pickle.dumps((world, tuple(reports)), protocol=5))


def save_checkpoint(folder, world, opts, seed, preparation_seconds, provenance):
    payload = pickle.dumps(dict(world=world, options=opts, seed=seed), protocol=5)
    name = f'step_{world.step_count:06d}'
    path = folder/(name+'.pickle')
    path.write_bytes(payload)
    atomic_json(folder/(name+'.json'), dict(step=world.step_count, time=world.time,
                preparation_physics_seconds=preparation_seconds, sha256=sha(payload),
                physics_source_id=provenance['physics_source_id'], prepared_from_step=0,
                genuine_simulation=True, includes_contact_cache=True, cache_manifolds=len(world.cache),
                seed=seed, options=asdict(opts)))
    return str(path.relative_to(ROOT)).replace('\\', '/')


def load_checkpoint(path, opts, seed, *, compatibility=None):
    p = (ROOT/path).resolve()
    if not p.is_relative_to(OUTPUT.resolve()):
        raise ValueError('load only trusted checkpoints beneath hw7/evidence/profile_serial')
    record = json.loads(p.with_suffix('.json').read_text(encoding='utf-8'))
    payload = p.read_bytes()
    current = sources()
    compatible = record['physics_source_id'] == current['physics_source_id']
    if not compatible and compatibility is not None:
        approval = json.loads(Path(compatibility).read_text(encoding='utf-8-sig'))
        compatible = (approval['historical_physics_source_id'] == record['physics_source_id']
                      and approval['approved_current_physics_source_id'] == current['physics_source_id']
                      and approval['approved_current_hashes'] == current['hashes'])
    if sha(payload) != record['sha256'] or not compatible:
        raise ValueError('checkpoint content/source hash mismatch')
    if not record['genuine_simulation'] or record['prepared_from_step'] != 0 or not record['includes_contact_cache']:
        raise ValueError('missing genuine-state/cache provenance')
    data = pickle.loads(payload)
    if data['options'] != opts or data['seed'] != seed:
        raise ValueError('checkpoint options/seed mismatch')
    if (record['options'] != json.loads(json.dumps(asdict(opts))) or record['seed'] != seed
            or data['world'].step_count != record['step'] or len(data['world'].cache) != record['cache_manifolds']):
        raise ValueError('checkpoint manifest/world mismatch')
    if compatibility is not None:
        record = dict(record, explicit_compatibility=str(compatibility), loaded_with_physics_source_id=current['physics_source_id'])
    return data['world'], record


class Telemetry:
    """Nested inclusive AND exclusive timings. Only exclusive values add to total."""
    def __init__(self):
        self.stack, self.inclusive, self.exclusive, self.calls = [], Counter(), Counter(), Counter()
        self.methods = Counter()
        self.last_elapsed = {}
        self.pair_costs = []
        self.phase_active = False
        self.saved_bindings = []
        self.solver_sample = None

    def push(self, name):
        self.stack.append([name, time.perf_counter_ns(), 0])

    def pop(self):
        name, start, children = self.stack.pop()
        elapsed = time.perf_counter_ns()-start
        self.inclusive[name] += elapsed
        self.exclusive[name] += elapsed-children
        self.calls[name] += 1
        self.last_elapsed[name] = elapsed
        if self.stack:
            self.stack[-1][2] += elapsed

    @contextmanager
    def span(self, name):
        self.push(name)
        try:
            yield
        finally:
            self.pop()

    def phase(self, name):
        if self.phase_active:
            self.pop()
        self.phase_active = name is not None
        if name is not None:
            self.push(name)

    def wrap(self, module, attr, name):
        original = getattr(module, attr)
        @functools.wraps(original)
        def wrapped(*args, **kwargs):
            label = name
            if name == 'detect':
                label = 'detect_trial' if kwargs.get('enrich', True) else 'detect_corrected_diagnostics'
            with self.span(label):
                if name == 'solver_total':
                    if self.solver_sample is None and args[1]:
                        self.solver_sample = args
                    try:
                        result = original(*args, **kwargs, observer=self.phase)
                    finally:
                        self.phase(None)
                else:
                    result = original(*args, **kwargs)
                if name == 'narrow_kernel':
                    self.methods[result.method] += 1
            if name == 'manifold_total':
                self.pair_costs.append(dict(step=args[0].state.step_count, a=args[0].id, b=args[1].id,
                                           diagnostic=not kwargs.get('enrich', True),
                                           seconds=self.last_elapsed[label]/1e9))
            return result
        self.saved_bindings.append((module, attr, original))
        setattr(module, attr, wrapped)

    def __enter__(self):
        for module, attr, name in ((physics, 'step_world', 'step_total'),
                                  (physics, 'advance', 'free_kick'), (physics, 'detect', 'detect'),
                                  (physics, 'world_aabb', 'aabb'), (physics, 'sweep_bounds', 'sweep_prune'),
                                  (physics, 'narrow_phase', 'manifold_total'),
                                  (patches, 'distance_or_penetration', 'narrow_kernel'),
                                  (physics, 'solve_contacts', 'solver_total')):
            self.wrap(module, attr, name)
        return self

    def __exit__(self, *exc):
        for module, attr, original in reversed(self.saved_bindings):
            setattr(module, attr, original)

    def result(self):
        total = self.inclusive['step_total']
        return dict(inclusive_seconds={k: v/1e9 for k, v in self.inclusive.items()},
                    exclusive_seconds={k: v/1e9 for k, v in self.exclusive.items()},
                    exclusive_percent_of_step={k: 100*v/total if total else 0 for k, v in self.exclusive.items()},
                    calls=dict(self.calls), witness_methods=dict(self.methods),
                    pair_costs=self.pair_costs,
                    exclusive_sum_seconds=sum(self.exclusive.values())/1e9,
                    note='Inclusive categories are nested: do NOT add them. Exclusive categories partition step_total; '
                         'step_total exclusive is pose/prediction/cache/validation/state-report construction and wrapper residual.')


def contact_graph(report, static_ids):
    weights = Counter((r.a, r.b) for r in report.impulses)
    parent = {}
    def find(i):
        parent.setdefault(i, i)
        if parent[i] != i:
            parent[i] = find(parent[i])
        return parent[i]
    for a, b in weights:
        dyn = [i for i in (a, b) if i not in static_ids]
        for i in dyn:
            find(i)
        if len(dyn) == 2:
            parent[find(dyn[1])] = find(dyn[0])
    islands = Counter()
    colors = []
    for (a, b), weight in sorted(weights.items()):
        dyn = {i for i in (a, b) if i not in static_ids}
        islands[find(min(dyn))] += weight
        for used in colors:
            if used.isdisjoint(dyn):
                used.update(dyn)
                break
        else:
            colors.append(set(dyn))
    total = sum(weights.values())
    return dict(pair_count=len(weights), row_count=total, islands=len(islands),
                island_row_weights=sorted(islands.values(), reverse=True), colors=len(colors),
                largest_island_row_share=max(islands.values(), default=0)/total if total else 0.)


def profile_export(profiler, folder, name):
    profiler.dump_stats(str(folder/(name+'.prof')))
    stats = pstats.Stats(profiler)
    functions = []
    for (file, line, func), (primitive, calls, self_time, cumulative, callers) in stats.stats.items():
        functions.append(dict(file=file, line=line, function=func, primitive_calls=primitive,
                              calls=calls, self_seconds=self_time, cumulative_seconds=cumulative))
    atomic_json(folder/(name+'_functions.json'), sorted(functions, key=lambda x: x['cumulative_seconds'], reverse=True))
    for sort in ('cumulative', 'tottime'):
        stream = io.StringIO()
        pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats(sort).print_stats(45)
        (folder/(name+'_'+sort+'.txt')).write_text(stream.getvalue(), encoding='utf-8')


def run_interval(start, opts, steps, mode, folder, name, max_seconds=None, journal_every=30, targets=(), seed=7, provenance=None):
    world, reports, graphs, samples = start, [], [], []
    telemetry = Telemetry() if mode in ('stages', 'combined') else None
    profiler = cProfile.Profile() if mode in ('cprofile', 'combined') else None
    elapsed, completed, error, paths = 0., 0, None, []
    static_ids = {b.id for b in start.bodies if b.static}
    status = 'running'
    record = dict(status=status, complete=False, requested_steps=steps, start_step=start.step_count,
                  completed_steps=0, mode=mode, physics_seconds=0., graphs=[], steps=[])
    atomic_json(folder/(name+'.json'), record)
    try:
        with telemetry if telemetry else nullcontext():
            if start.step_count in targets:
                paths.append(save_checkpoint(folder/'checkpoints', world, opts, seed, elapsed, provenance))
            for i in range(steps):
                t0 = time.perf_counter_ns()
                if profiler:
                    profiler.enable()
                try:
                    world, report = physics.step_world(world, opts)
                    reports.append(report)
                finally:
                    if profiler:
                        profiler.disable()
                    elapsed += (time.perf_counter_ns()-t0)/1e9
                completed += 1
                graphs.append(contact_graph(report, static_ids))
                samples.append(dict(step=world.step_count, candidates=report.candidates, manifolds=report.manifolds,
                                    rows=len(report.impulses), corrected_depth=report.penetration_after))
                if world.step_count in targets:
                    paths.append(save_checkpoint(folder/'checkpoints', world, opts, seed, elapsed, provenance))
                if completed % journal_every == 0 or completed == steps:
                    atomic_json(folder/(name+'.json'), dict(record, completed_steps=completed, physics_seconds=elapsed,
                                end_step=world.step_count, checkpoint_paths=paths, steps=samples, graphs=graphs))
                    print(json.dumps(dict(event=name, completed=completed, requested=steps, world_step=world.step_count,
                                          physics_seconds=elapsed)), flush=True)
                if max_seconds is not None and elapsed >= max_seconds and completed < steps:
                    status = 'partial_budget'
                    break
            else:
                status = 'complete'
    except BaseException as exc:
        status = 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed'
        error = dict(type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc())
    finally:
        if profiler:
            profile_export(profiler, folder, name)
        if provenance is not None and status != 'complete':
            paths.append(save_checkpoint(folder/'checkpoints', world, opts, seed, elapsed, provenance))
        record.update(status=status, complete=status == 'complete', completed_steps=completed,
                      end_step=world.step_count, physics_seconds=elapsed, steps=samples, graphs=graphs,
                      checkpoint_paths=paths, error=error, world_digest=digest(world),
                      reports_digest=digest(world, reports), telemetry=telemetry.result() if telemetry else None,
                      candidate_sum=sum(s['candidates'] for s in samples), manifold_sum=sum(s['manifolds'] for s in samples),
                      row_sum=sum(s['rows'] for s in samples), max_corrected_depth=max((s['corrected_depth'] for s in samples), default=0.))
        atomic_json(folder/(name+'.json'), record)
        if telemetry and telemetry.solver_sample is not None:
            (folder/(name+'_solver_input.pickle')).write_bytes(pickle.dumps(telemetry.solver_sample, protocol=5))
    return world, tuple(reports), record


def main(argv=None):
    confine_native_temporary_files()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inventory', 'prepare', 'measure', 'validate'))
    parser.add_argument('--label', required=True, help='new unique evidence subdirectory; never overwrite old runs')
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--dt', type=float, default=1/480)
    parser.add_argument('--velocity-iterations', type=int, default=120)
    parser.add_argument('--split-iterations', type=int, default=20)
    parser.add_argument('--checkpoint')
    parser.add_argument('--steps', type=int, default=60)
    parser.add_argument('--mode', choices=('plain', 'stages', 'cprofile', 'combined'), default='plain')
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--warmup-steps', type=int, default=0)
    parser.add_argument('--targets', default='0,240,600,1440')
    parser.add_argument('--max-seconds', type=float)
    parser.add_argument('--journal-every', type=int, default=30)
    args = parser.parse_args(argv)
    if any(v < 0 for v in (args.steps, args.warmup_steps)) or args.repeats < 1 or args.journal_every < 1:
        parser.error('invalid step/repetition/journal count')
    if args.max_seconds is not None and args.max_seconds <= 0:
        parser.error('max-seconds must be positive')
    if not args.label or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in args.label):
        parser.error('label must contain only letters, digits, underscore or hyphen')
    opts = Options(dt=args.dt, velocity_iterations=args.velocity_iterations, split_iterations=args.split_iterations)
    folder = OUTPUT/args.label
    folder.mkdir(parents=True, exist_ok=False)
    (folder/'checkpoints').mkdir()
    meta = metadata(args, opts)
    atomic_json(folder/'metadata.json', meta)
    try:
        if args.action == 'inventory':
            inventory = runtime()
            if os.name == 'nt':
                inventory['windows_processor'] = command_output(['powershell', '-NoProfile', '-NonInteractive', '-Command',
                    'Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json'])
                inventory['active_power_scheme'] = command_output(['powercfg', '/getactivescheme'])
            inventory['unknown'] = ['thermal/throttling history', 'controlled background load', 'per-core performance classes',
                                    'actual native-library thread counts (environment alone is insufficient)']
            atomic_json(folder/'inventory.json', inventory)
            print(json.dumps(inventory, indent=2), flush=True)
            return 0
        load_start = time.perf_counter()
        start, checkpoint_meta = load_checkpoint(args.checkpoint, opts, args.seed) if args.checkpoint else (make_scene(args.seed), None)
        meta.update(checkpoint_metadata=checkpoint_meta, checkpoint_load_or_scene_setup_seconds=time.perf_counter()-load_start)
        atomic_json(folder/'metadata.json', meta)
        if args.action == 'prepare':
            targets = tuple(sorted(set(int(x) for x in args.targets.split(','))))
            if targets[0] < start.step_count or targets[-1] > 2880:
                raise ValueError('preparation targets must be chronological and at most accepted step 2880')
            _, _, record = run_interval(start, opts, targets[-1]-start.step_count, args.mode, folder, 'prepare',
                                        args.max_seconds, args.journal_every, targets, args.seed, meta['source'])
            return 0 if record['complete'] else 2
        if args.action == 'validate':
            plain_world, plain_reports, p = run_interval(start, opts, args.steps, 'plain', folder, 'reference')
            staged_world, staged_reports, s = run_interval(start, opts, args.steps, 'combined', folder, 'instrumented')
            equality = dict(world_exact=plain_world == staged_world, reports_exact=plain_reports == staged_reports,
                            contains_collision=any(r.impulses for r in plain_reports),
                            reference_digest=p['reports_digest'], instrumented_digest=s['reports_digest'],
                            complete=p['complete'] and s['complete'])
            equality['passed'] = all(equality[k] for k in ('world_exact', 'reports_exact', 'contains_collision', 'complete'))
            atomic_json(folder/'validation.json', equality)
            print(json.dumps(equality, indent=2), flush=True)
            return 0 if equality['passed'] else 1
        if args.warmup_steps:
            _, _, warmup = run_interval(start, opts, args.warmup_steps, 'plain', folder, 'warmup')
            if not warmup['complete']:
                return 1
        records = []
        for repeat in range(args.repeats):
            _, _, record = run_interval(start, opts, args.steps, args.mode, folder, f'run_{repeat:02d}',
                                        args.max_seconds, args.journal_every, provenance=meta['source'])
            records.append(record)
            if not record['complete']:
                break
        times = [r['physics_seconds'] for r in records if r['complete']]
        complete = len(records) == args.repeats and all(r['complete'] for r in records)
        baseline = dict(complete=complete, mode=args.mode, raw_seconds=times,
                        median_seconds=statistics.median(times) if times else None,
                        min_seconds=min(times) if times else None, max_seconds=max(times) if times else None,
                        sample_stdev_seconds=statistics.stdev(times) if len(times) > 1 else None,
                        warmup_policy=f'{args.warmup_steps} discarded steps from the same immutable start; reset before each repeat',
                        exact_replay=len({r['reports_digest'] for r in records if r['complete']}) <= 1)
        atomic_json(folder/'measurements.json', baseline)
        print(json.dumps(baseline, indent=2), flush=True)
        return 0 if complete else 2
    except BaseException as exc:
        atomic_json(folder/'failure.json', dict(complete=False, type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc()))
        traceback.print_exc()
        return 130 if isinstance(exc, KeyboardInterrupt) else 1


if __name__ == '__main__':
    raise SystemExit(main())
