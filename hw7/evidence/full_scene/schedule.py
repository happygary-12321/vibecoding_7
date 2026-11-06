"""Sequential resumable full-trial schedule; never resume a partial physics run."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from .runner import OUTPUT, verify_cohort, p


def main():
    identity = verify_cohort()
    lock = OUTPUT/'schedule.lock'
    if lock.exists():
        import psutil
        owner = json.loads(lock.read_text())
        if psutil.pid_exists(owner['pid']):
            raise RuntimeError(f'schedule process {owner["pid"]} already exists; do not benchmark concurrently')
        lock.rename(OUTPUT/f'stale_lock_{time.time_ns()}.json')
    with lock.open('x', encoding='utf-8') as f:
        json.dump(dict(pid=os.getpid(), created_utc=p.stamp()), f)
    schedule = [('serial', 0), ('parallel', 0), ('parallel', 1), ('serial', 1), ('serial', 2), ('parallel', 2)]
    completed = []
    reference = None
    progress = dict(status='starting', complete=False, command=[sys.executable, *sys.orig_argv[1:]],
                    pid=os.getpid(), identity=identity, completed=completed)
    (OUTPUT/'logs').mkdir(exist_ok=True)
    try:
        for index, (backend, repetition) in enumerate(schedule):
            base = f'full_{backend}_r{repetition}'
            attempt = 1
            label = base
            while (OUTPUT/label).exists():
                folder = OUTPUT/label
                record_path = folder/'record.json'
                if record_path.exists():
                    previous = json.loads(record_path.read_text())
                    if 'MISMATCH' in previous.get('error', ''):
                        raise RuntimeError('prior exact mismatch must be investigated before continuing')
                    if previous.get('complete'):
                        if previous['identity'] != identity or previous['backend'] != backend:
                            raise RuntimeError('complete incompatible trial: start a new audited cohort')
                        if not (folder/'cold_invocation.json').exists():
                            raise RuntimeError('completed stepping lacks cold wrapper record; preserve it, do not rerun')
                        completed.append(label)
                        if index == 0:
                            reference = label
                        print(json.dumps(dict(event='skip_compatible_complete', label=label)), flush=True)
                        break
                    import psutil
                    if previous.get('pid') and psutil.pid_exists(previous['pid']):
                        raise RuntimeError('unfinished trial PID still exists: leave healthy run alone')
                attempt += 1
                label = base+f'_attempt{attempt}'
            else:
                cmd = [sys.executable, '-B', '-m', 'hw7.evidence.full_scene.runner', 'trial',
                       '--label', label, '--backend', backend]
                if reference:
                    cmd.extend(['--reference', reference])
                progress.update(status='running', current_label=label, schedule_index=index,
                                completed=completed, command_running=cmd, updated_utc=p.stamp())
                p.atomic_json(OUTPUT/'schedule.json', progress)
                print(json.dumps(dict(event='launch', index=index, label=label, command=cmd)), flush=True)
                start = time.perf_counter()
                with (OUTPUT/'logs'/(label+'.log')).open('x', encoding='utf-8') as log:
                    child = subprocess.Popen(cmd, cwd=p.ROOT, stdout=log, stderr=subprocess.STDOUT)
                    progress['trial_pid'] = child.pid
                    p.atomic_json(OUTPUT/'schedule.json', progress)
                    # No timeout and no termination of a healthy long run.
                    code = child.wait()
                cold = time.perf_counter()-start
                folder = OUTPUT/label
                p.atomic_json(folder/'cold_invocation.json', dict(command=cmd, exit_code=code,
                    cold_invocation_seconds=cold, timer='parent perf_counter around Popen through wait; '
                    'includes process/imports/setup/warmup/physics/audit/export/shutdown/output; '
                    'excludes this wrapper JSON write', finished_utc=p.stamp()))
                if code:
                    raise RuntimeError(f'{label} returned {code}; remaining schedule stopped')
                record = json.loads((folder/'record.json').read_text())
                assert record['complete'] and record['acceptance']['accepted'] and record['exact_reference_match']
                if index == 0:
                    reference = label
                completed.append(label)
                print(json.dumps(dict(event='trial_finished', label=label, physics_seconds=record['physics_seconds'],
                                      cold_seconds=cold, accepted=True, exact=True)), flush=True)
            progress.update(status='between_trials', completed=completed, updated_utc=p.stamp())
            p.atomic_json(OUTPUT/'schedule.json', progress)
        progress.update(status='complete', complete=True, completed=completed, updated_utc=p.stamp())
        p.atomic_json(OUTPUT/'schedule.json', progress)
        return 0
    except BaseException as exc:
        progress.update(status='failed_or_interrupted', complete=False, error=repr(exc), updated_utc=p.stamp())
        p.atomic_json(OUTPUT/'schedule.json', progress)
        raise
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    raise SystemExit(main())
