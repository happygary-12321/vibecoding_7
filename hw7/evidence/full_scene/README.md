# Part 5 full-scene evidence

Run commands from the HW3_submission root with the installed Python 3.12.10
interpreter (or replace `python` below). The production solver, both backends,
all Hw5 files, earlier checkpoint files and the prepared Part 4 script are
unchanged. `cohort.json` pins production and evidence-harness hashes, numerical
settings, runtime, affinity and requested native-thread limits.

```powershell
python -B -m hw7.evidence.full_scene.checks
python -B -m hw7.evidence.full_scene.runner preflight
python -B -m hw7.evidence.full_scene.schedule
# After six complete trials only:
python -B -m hw7.evidence.full_scene.summarize
# Replay a completed saved-state/report audit without rerunning physics:
python -B -m hw7.evidence.full_scene.runner replay --label full_parallel_r0
```

The checks command refuses to overwrite its test log. Preflight verifies an
existing compatible cohort instead of replacing it. The schedule is sequential:
serial 0, parallel 0, parallel 1, serial 1, serial 2, parallel 2. No trial timeout
or healthy-process termination is used. A lock prevents another schedule from
starting. Compatible complete trials are skipped; partial attempts are retained
and a subsequent invocation restarts that trial from step zero under a new
attempt label. An exact mismatch stops the schedule. No partial segments are
combined into a full timing. Do not launch the older final_matched.ps1 alongside
this schedule.

All measured trials start at the realized seed-7 initial world, clock/step zero
and empty cache, with 30 dynamic objects and five static bin prisms. Settings
are dt=1/480, 2880 steps, 120 physical/20 split sweeps, identical Options and
report/diagnostic work. Warmup discards 30 real collision steps from the genuine
step-600 cached world, then resets the complete state/cache. Parallel trials
reuse one eight-worker, batch-four, threshold-zero pool through warmup and all
2880 measured steps. Native thread limits are requested as one in parent and
children before native imports. There are no frames, snapshots, rendering or
sleeping in the trial.

Stepping time is ONE continuous unprofiled perf_counter wall span around the
complete step/report loop. It includes IPC, dispatch, canonical gathering,
synchronization, both detection barriers and ordered solving. Identical progress
JSON/console writes every 120 steps are also included in both paths; their small
I/O time is retained separately without subtracting it. This is a new matched
baseline, distinct from Part 4's output-free short intervals and the old
frame-sampled 1151-second acceptance observation.

Readiness/startup, discarded warmup and shutdown are separate. Realized-state
JSON, all retained World/cache/StepReports in trusted replay.pickle, exact
canonical hashes, acceptance audit and evidence export occur outside stepping
time. The outer subprocess timer also includes Python startup/imports, setup,
warmup, hashes, audits, export and shutdown/output. It excludes its own final
cold_invocation.json write. Each trial retains exact argv, sources, numerical
settings, runtime/affinity, PID work counters and completion status.

`schedule.json` records the active process/label and completed trials. Each
trial's `journal.json` remains explicitly incomplete even if its last saved
step is 2880. Only `record.json` with complete=true plus a successful
cold_invocation.json indicates accepted completed evidence. Per-trial stdout
and errors are in logs/. `realized.json`, `acceptance.json` and replay.pickle
allow audit replay. A final comparison.json/REPORT.md is written only after
all six trials pass source, exact-agreement, acceptance and replay checks.

No full cProfile, rendering benchmark, installation, commit, push or packaging
is part of this stage. Personal reflection remains empty.
