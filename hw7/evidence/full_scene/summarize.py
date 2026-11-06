"""Check all six complete full-scene records and create a new summary."""
import json
import statistics
from .runner import OUTPUT, p, verify_cohort, replay


def main():
    cohort = verify_cohort()
    schedule = json.loads((OUTPUT/'schedule.json').read_text())
    assert schedule['complete'] and len(schedule['completed']) == 6
    trials, groups = [], {'serial': [], 'parallel': []}
    for label in schedule['completed']:
        folder = OUTPUT/label
        record = json.loads((folder/'record.json').read_text())
        cold = json.loads((folder/'cold_invocation.json').read_text())
        assert record['complete'] and record['physics_complete'] and record['completed_steps'] == 2880
        assert record['identity'] == cohort and record['acceptance']['accepted']
        assert record['runtime'].get('effective_affinity') == json.loads((OUTPUT/'cohort.json').read_text())['runtime'].get('effective_affinity')
        assert record['exact_reference_match'] and cold['exit_code'] == 0
        assert record['initial_cache_manifolds'] == 0 and not record['resumed']
        assert all(record['runtime']['thread_environment'][k] == v for k, v in cohort['thread_limits'].items())
        if record['pool']:
            assert record['pool']['all_workers_exited'] and len(record['pool']['ready']) == 8
            assert record['measured_dispatch']['trial_calls'] == record['measured_dispatch']['diagnostic_calls'] == 2880
            assert sum(record['measured_worker_pairs'].values()) == record['measured_dispatch']['worker_pairs'] > 0
        replay(label)
        item = dict(label=label, backend=record['backend'], physics_seconds=record['physics_seconds'],
            cold_invocation_seconds=cold['cold_invocation_seconds'], warmup_seconds=record['warmup_seconds'],
            startup_seconds=record['pool']['startup_seconds'] if record['pool'] else 0.,
            shutdown_seconds=record['pool']['shutdown_seconds'] if record['pool'] else 0.,
            journal_io_seconds=record['journal_io_seconds'], trial_total_seconds=record['trial_total_seconds'],
            final_output_and_audit_seconds=record['final_output_and_audit_seconds'],
            measured_dispatch=record.get('measured_dispatch'), measured_worker_pairs=record.get('measured_worker_pairs'),
            value_digest=record['value_digest'], accepted=True, evidence=str(folder.relative_to(p.ROOT)))
        trials.append(item)
        groups[item['backend']].append(item)
    assert len({t['value_digest'] for t in trials}) == 1
    aggregates = {}
    for backend, items in groups.items():
        assert len(items) == 3
        times = [t['physics_seconds'] for t in items]
        cold = [t['cold_invocation_seconds'] for t in items]
        aggregates[backend] = dict(raw_seconds=times, median_seconds=statistics.median(times),
            min_seconds=min(times), max_seconds=max(times), sample_stdev_seconds=statistics.stdev(times),
            cold_raw_seconds=cold, cold_median_seconds=statistics.median(cold),
            cold_sample_stdev_seconds=statistics.stdev(cold))
    speedup = aggregates['serial']['median_seconds']/aggregates['parallel']['median_seconds']
    cold_speedup = aggregates['serial']['cold_median_seconds']/aggregates['parallel']['cold_median_seconds']
    first = json.loads((OUTPUT/schedule['completed'][0]/'acceptance.json').read_text())
    report = dict(complete=True, created_utc=p.stamp(), identity=cohort, trials=trials,
        aggregates=aggregates, speedup=speedup, cold_speedup=cold_speedup,
        parallel_efficiency=speedup/8, acceptance=first, all_six_value_digests_equal=True,
        failed_or_partial_attempts=[str(path.parent.relative_to(p.ROOT)) for path in OUTPUT.glob('full_*/record.json')
            if not json.loads(path.read_text()).get('complete')],
        limitations=['Fixed seed 7 and one scene/machine; no general chaotic-scene guarantee',
            'Native thread limits requested equally; actual library thread counts not independently measured',
            'Continuous stepping timer includes identical 120-step journal writes; measured IO separately',
            'Cold totals include warmup, full report/state export, audit and digests; distinct from stepping',
            'Not the old frame-sampled 1151 s acceptance timing or short interval ratios'])
    with (OUTPUT/'comparison.json').open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    lines = ['# Part 5 complete-scene comparison', '', '| Trial | Backend | Stepping seconds | Cold seconds |',
             '| --- | --- | --- | --- |']
    for t in trials:
        lines.append(f"| {t['label']} | {t['backend']} | {t['physics_seconds']:.7f} | {t['cold_invocation_seconds']:.7f} |")
    lines += ['', f'Median stepping speedup: {speedup:.6f}x; cold invocation speedup: {cold_speedup:.6f}x.', '',
              'All six complete World/cache/report canonical digests match exactly; all saved-state acceptance audits pass.', '',
              'See comparison.json for sample SD/range, raw overhead, dispatch/PID work, scope and limitations.']
    with (OUTPUT/'REPORT.md').open('x', encoding='utf-8') as f:
        f.write('\n'.join(lines)+'\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
