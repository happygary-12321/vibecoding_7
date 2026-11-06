"""Summarize serial evidence and measure decomposition/IPC overhead only.

No worker executes physics: the IPC probe is an echo of trusted local data.
The island probe executes serial fixed-pose solves, never parallel scenes.
"""
import argparse
from collections import Counter, defaultdict
import json
import multiprocessing
from pathlib import Path
import pickle
import statistics
import sys
import time
import traceback
from .profiling import ROOT, OUTPUT, atomic_json, sources, runtime, stamp, confine_native_temporary_files
from .solver import solve_contacts


def trusted(path):
    p = (ROOT/path).resolve()
    if not p.is_relative_to(OUTPUT.resolve()):
        raise ValueError('input must be trusted local profiling evidence')
    return p


def summarize():
    rows = []
    for folder in sorted(OUTPUT.iterdir()):
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob('*.json')):
            data = json.loads(path.read_text(encoding='utf-8'))
            if not isinstance(data, dict) or 'requested_steps' not in data:
                continue
            graphs = data.get('graphs', [])
            steps = data.get('steps', [])
            n = len(steps)
            row = dict(label=folder.name, file=path.name, mode=data.get('mode'), status=data.get('status'),
                       complete=data.get('complete'), start_step=data.get('start_step'), end_step=data.get('end_step'),
                       steps=n, seconds=data.get('physics_seconds'),
                       candidates_per_step=sum(s['candidates'] for s in steps)/n if n else 0,
                       manifolds_per_step=sum(s['manifolds'] for s in steps)/n if n else 0,
                       rows_per_step=sum(s['rows'] for s in steps)/n if n else 0,
                       islands_mean=statistics.mean(g['islands'] for g in graphs) if graphs else None,
                       colors_mean=statistics.mean(g['colors'] for g in graphs) if graphs else None,
                       largest_island_row_share_mean=statistics.mean(g['largest_island_row_share'] for g in graphs) if graphs else None,
                       exclusive_percent=data.get('telemetry', {}).get('exclusive_percent_of_step') if data.get('telemetry') else None,
                       inclusive_seconds=data.get('telemetry', {}).get('inclusive_seconds') if data.get('telemetry') else None,
                       witness_methods=data.get('telemetry', {}).get('witness_methods') if data.get('telemetry') else None)
            rows.append(row)
    atomic_json(OUTPUT/'summary.json', dict(created_utc=stamp(), measurements=rows))
    print(json.dumps(rows, indent=2))
    checks = {}
    for name in ('free', 'impacts', 'pile', 'peak'):
        paths = [OUTPUT/(name+'_'+mode)/'run_00.json' for mode in ('plain', 'stages', 'cprofile')]
        if all(p.is_file() for p in paths):
            values = [json.loads(p.read_text(encoding='utf-8')) for p in paths]
            checks[name] = dict(all_complete=all(v['complete'] for v in values),
                               world_and_report_digests_equal=len({v['reports_digest'] for v in values}) == 1)
    atomic_json(OUTPUT/'cross_mode_agreement.json', checks)
    bounds = {}
    for label in ('peak_stages', 'pile_granular'):
        path = OUTPUT/label/'run_00.json'
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        t = data['telemetry']
        jobs = t.get('pair_costs', [])
        groups = defaultdict(list)
        for job in jobs:
            groups[job['step'], job['diagnostic']].append(job['seconds'])
        total = t['inclusive_seconds']['step_total']
        target = sum(j['seconds'] for j in jobs)
        serial_other = total-target
        bounds[label] = dict(measured_instrumented_seconds=total, target_seconds=target,
            target_fraction=target/total, pair_jobs=len(jobs), mean_job_seconds=target/len(jobs),
            max_job_seconds=max(j['seconds'] for j in jobs),
            ideal_interval_speedup={str(p): total/(serial_other+sum(max(sum(js)/p, max(js)) for js in groups.values()))
                                    for p in (2, 4, 8, 24)},
            amdahl_no_load_imbalance_speedup={str(p): 1/(1-target/total+target/total/p) for p in (2, 4, 8, 24)},
            infinite_worker_amdahl_bound=total/serial_other,
            note='Estimate from measured interval pair-call durations and actual two detection barriers; '
                 'ignores IPC, scheduling, filesystem contention and changing cost under concurrency. '
                 'Not a measured whole-six-second speedup or whole-scene fraction.')
    atomic_json(OUTPUT/'parallel_bounds.json', bounds)


def island_groups(bodies, reports):
    static = {b.id for b in bodies if b.static}
    parent = {}
    def find(i):
        parent.setdefault(i, i)
        if parent[i] != i:
            parent[i] = find(parent[i])
        return parent[i]
    for r in reports:
        dyn = [i for i in (r.a, r.b) if i not in static]
        for i in dyn:
            find(i)
        if len(dyn) == 2:
            parent[find(dyn[1])] = find(dyn[0])
    groups = defaultdict(set)
    for i in parent:
        groups[find(i)].add(i)
    return sorted(groups.values(), key=lambda g: min(g)), static


def island_probe(sample, folder, repeats):
    bodies, manifolds, opts = pickle.loads(trusted(sample).read_bytes())
    full_scratch, full_reports = solve_contacts(bodies, manifolds, opts)
    groups, static = island_groups(bodies, full_reports)
    active_pairs = {(r.a, r.b) for r in full_reports}
    tasks = []
    for group in groups:
        ms = tuple(m for m in manifolds if (m.a, m.b) in active_pairs and ({m.a, m.b}-static) <= group)
        ids = group | {i for m in ms for i in (m.a, m.b)}
        bs = tuple(b for b in bodies if b.id in ids)
        tasks.append((bs, ms, opts))
    durations = [[] for _ in tasks]
    full_times = []
    merged_reports = defaultdict(list)
    for repeat in range(repeats):
        start = time.perf_counter_ns()
        solve_contacts(bodies, manifolds, opts)
        full_times.append((time.perf_counter_ns()-start)/1e9)
        for index, task in enumerate(tasks):
            start = time.perf_counter_ns()
            scratch, reports = solve_contacts(*task)
            durations[index].append((time.perf_counter_ns()-start)/1e9)
            for i in groups[index]:
                for attr in ('v', 'w', 'push_v', 'push_w'):
                    if getattr(scratch[i], attr) != getattr(full_scratch[i], attr):
                        raise AssertionError(f'island decomposition changes {i} {attr}')
            if repeat == 0:
                for report in reports:
                    merged_reports[report.a, report.b].append(report)
    combined = tuple(r for m in manifolds for r in merged_reports.pop((m.a, m.b), ()))
    if combined != full_reports:
        raise AssertionError('island decomposition changes physical/push impulse reports')
    medians = [statistics.median(ts) for ts in durations]
    result = dict(complete=True, sample=sample, dynamic_island_ids=[sorted(g) for g in groups],
                  island_count=len(groups), full_rows=len(full_reports), full_solver_raw_seconds=full_times,
                  full_solver_median_seconds=statistics.median(full_times), island_raw_seconds=durations,
                  island_median_seconds=medians, sum_island_medians_seconds=sum(medians),
                  largest_island_fraction_of_sum=max(medians, default=0)/sum(medians) if medians else 0.,
                  exact_dynamic_velocities_and_impulse_reports=True,
                  ideal_island_stage_seconds={str(p): max(sum(medians)/p, max(medians, default=0)) for p in (2, 4, 8, 24)},
                  note='Serial fixed-pose microbenchmark; no parallel backend or speedup was measured. '
                       'Ideal lower bounds omit IPC/scheduling and include duplicated per-island static setup.')
    atomic_json(folder/'islands.json', result)
    for i, task in enumerate(tasks):
        (folder/f'island_{i:02d}.pickle').write_bytes(pickle.dumps(task, protocol=5))
    print(json.dumps(result, indent=2))


def echo_worker(connection):
    connection.send_bytes(b'ready')
    while True:
        payload = connection.recv_bytes()
        if not payload:
            break
        value = pickle.loads(payload)
        connection.send_bytes(pickle.dumps(value, protocol=5))
    connection.close()


def ipc_probe(sample, folder, repeats):
    value = pickle.loads(trusted(sample).read_bytes())
    payload = pickle.dumps(value, protocol=5)
    dump_times, load_times = [], []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        pickle.dumps(value, protocol=5)
        dump_times.append((time.perf_counter_ns()-start)/1e9)
        start = time.perf_counter_ns()
        pickle.loads(payload)
        load_times.append((time.perf_counter_ns()-start)/1e9)
    context = multiprocessing.get_context('spawn')
    parent, child = context.Pipe()
    process = context.Process(target=echo_worker, args=(child,))
    start = time.perf_counter()
    process.start()
    child.close()
    try:
        if not parent.poll(20) or parent.recv_bytes() != b'ready':
            raise RuntimeError('spawn worker not ready')
        startup = time.perf_counter()-start
        trips = []
        for _ in range(repeats):
            start = time.perf_counter_ns()
            parent.send_bytes(payload)
            if not parent.poll(20):
                raise RuntimeError('echo timeout')
            reply = parent.recv_bytes()
            trips.append((time.perf_counter_ns()-start)/1e9)
            if pickle.loads(reply) != value:
                raise AssertionError('echo payload changed')
        parent.send_bytes(b'')
        process.join(10)
        if process.is_alive() or process.exitcode != 0:
            raise RuntimeError('echo worker did not exit successfully')
    finally:
        if process.is_alive():
            process.terminate()
            process.join(5)
        parent.close()
    result = dict(complete=True, sample=sample, bytes=len(payload), start_method='spawn', workers=1,
                  startup_until_ready_seconds=startup, local_pickle_dump_seconds=dump_times,
                  local_pickle_load_seconds=load_times, reused_worker_roundtrip_seconds=trips,
                  median_roundtrip_seconds=statistics.median(trips),
                  note='Echo only, including pipe transfer and worker unpickle/repickle. No physics executes in the worker; '
                       'this is overhead evidence, not a parallel physics backend or speedup.')
    atomic_json(folder/'ipc.json', result)
    print(json.dumps(result, indent=2))


def main(argv=None):
    confine_native_temporary_files()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('summarize', 'islands', 'ipc'))
    parser.add_argument('--sample')
    parser.add_argument('--label')
    parser.add_argument('--repeats', type=int, default=5)
    args = parser.parse_args(argv)
    if args.action == 'summarize':
        summarize()
        return 0
    if not args.sample or not args.label or args.repeats < 1 or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in args.label):
        parser.error('sample, safe label and positive repeat count are required')
    folder = OUTPUT/args.label
    folder.mkdir(parents=True, exist_ok=False)
    atomic_json(folder/'metadata.json', dict(exact_command=[sys.executable, *sys.orig_argv[1:]], source=sources(), runtime=runtime(), created_utc=stamp()))
    try:
        (island_probe if args.action == 'islands' else ipc_probe)(args.sample, folder, args.repeats)
        return 0
    except BaseException as exc:
        atomic_json(folder/'failure.json', dict(complete=False, error=repr(exc), traceback=traceback.format_exc()))
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
