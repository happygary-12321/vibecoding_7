"""Read-only evidence checks, then new Part 4 summary artifacts. Run from root."""
import json
from pathlib import Path
import statistics

ROOT = Path('hw7/evidence/parallel_pilot')


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    approved = read(ROOT/'compatibility_v3.json')
    rows = []
    for scene in ('peak', 'impacts', 'pile'):
        reference = read(ROOT/'validation_v3'/(scene+'_serial.json'))
        by_worker = {}
        for workers in (0, 4, 8):
            records, cold, meta = [], [], []
            for repeat in range(3):
                folder = ROOT/f'repeat_{scene}_w{workers}_r{repeat}'
                data = read(folder/f'{scene}_w{workers}_b4_r0.json')
                metadata = read(folder/'metadata.json')
                invocation = read(folder/'cold_invocation.json')
                assert read(folder/'results.json')['complete']
                assert data['complete'] and data['status'] == 'complete'
                assert data['steps'] == 30 and data['warmup_steps'] == 4
                assert data['start_step'] == reference['start_step']
                assert data['end_step'] == reference['end_step']
                assert data['value_digest'] == reference['value_digest']
                assert data['workers'] == workers and data['batch_size'] == 4
                assert invocation['exit_code'] == 0
                assert metadata['source']['hashes'] == approved['approved_current_hashes']
                assert metadata['runtime']['thread_environment']['OMP_NUM_THREADS'] == '1'
                if workers:
                    counts = data['measured_dispatch']
                    assert counts['trial_calls'] == counts['diagnostic_calls'] == 30
                    assert counts['worker_pairs'] == counts['candidate_pairs'] > 0
                    assert sum(data['measured_worker_pairs'].values()) == counts['worker_pairs']
                    assert 1 <= len([v for v in data['measured_worker_pairs'].values() if v]) <= workers
                    assert len(data['pool']['ready']) == workers
                    assert data['pool']['all_workers_exited']
                records.append(data)
                cold.append(invocation['cold_invocation_seconds'])
                meta.append(metadata)
            times = [r['physics_seconds'] for r in records]
            item = dict(scene=scene, workers=workers, batch_size=4, raw_seconds=times,
                median_seconds=statistics.median(times), sample_stdev_seconds=statistics.stdev(times),
                cold_invocation_raw_seconds=cold,
                trial_total_raw_seconds=[r['trial_total_seconds'] for r in records],
                warmup_raw_seconds=[r['warmup_seconds'] for r in records],
                startup_raw_seconds=[r['pool']['startup_seconds'] if workers else 0. for r in records],
                shutdown_raw_seconds=[r['pool']['shutdown_seconds'] if workers else 0. for r in records],
                measured_dispatch=[r.get('measured_dispatch') for r in records],
                measured_worker_pairs=[r.get('measured_worker_pairs') for r in records],
                active_workers=[len([v for v in r.get('measured_worker_pairs', {}).values() if v]) for r in records],
                world_cache_reports_exact=True)
            rows.append(item)
            by_worker[workers] = item
        for workers, item in by_worker.items():
            item['speedup'] = by_worker[0]['median_seconds']/item['median_seconds']
            item['cold_invocation_speedup'] = statistics.median(by_worker[0]['cold_invocation_raw_seconds'])/statistics.median(item['cold_invocation_raw_seconds'])
    screen = read(ROOT/'screen_v1/results.json')
    assert screen['complete']
    screen_rows = screen['results']
    for r in screen_rows:
        base = next(v for v in screen_rows if v['scene'] == r['scene'] and v['workers'] == 0)
        r['speedup'] = base['median_seconds']/r['median_seconds']
    report = dict(complete=True, source_approval='compatibility_v3.json', repeats=rows, screen=screen_rows,
        selected=dict(workers=8, batch_size=4, serial_threshold=0),
        scope='Three 30-step (.0625 simulated second) cached intervals, not the complete 2880-step scene.',
        correctness='Historical serial pickle digests reproduced; direct Python serial/parallel equality passed '
                    'in validation_v3. Every screen/repeat canonical value digest exactly equals that reference.',
        timing='Unprofiled entire stepping/report loop, both detection barriers, all IPC/gather/synchronization '
               'and unchanged serial solver; excludes load/setup/warmup/output/rendering, no frame sampling.',
        warmup='4 discarded steps from same genuine starting world, reset physical/cache state before timing; '
               'pool reused across warmup and measured steps; fresh pool per trial.',
        total='Caller cold_invocation includes Python process/imports, checkpoint validation/loading, readiness, '
              'warmup, stepping, digest construction, shutdown, output. It excludes the wrapper JSON write.',
        limitations=['No whole-scene acceleration measurement', 'No inference from historical 1151 s acceptance',
                     'Actual native pool sizes/thermal history/background load not independently controlled',
                     'Startup/temp I/O and trial variance are machine-specific'])
    destination = ROOT/'comparison.json'
    with destination.open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    lines = ['# Part 4 interval comparison', '', report['scope'], '',
        '| Interval | Workers/batch | Raw stepping seconds | Median ± sample SD | Speedup |',
        '| --- | --- | --- | --- | --- |']
    for r in rows:
        raw = ', '.join(f'{v:.7f}' for v in r['raw_seconds'])
        lines.append(f"| {r['scene']} | {r['workers']}/4 | {raw} | {r['median_seconds']:.7f} ± {r['sample_stdev_seconds']:.7f} | {r['speedup']:.3f}x |")
    lines += ['', 'Recommended preliminary setting: 8 workers, batch 4, threshold 0.', '',
              report['correctness'], '', report['timing'], '', report['warmup'], '', report['total'], '',
              'All unsuccessful batch-size/configuration results remain in screen_v1/.', '',
              'No complete 2880-step comparison was run.']
    with (ROOT/'REPORT.md').open('x', encoding='utf-8') as f:
        f.write('\n'.join(lines)+'\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
