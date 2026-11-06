# HW7 progress — Part 5 full-scene comparison

## Current checkpoint — Part 5 complete, 2026-11-05

All SIX full-scene trials completed uninterrupted, passed the original physical
acceptance limits and have exactly the same complete World/contact-cache/2880-
StepReport canonical digest. All six saved replay checksums/digests/acceptance
audits passed. No failed/partial/interrupted Part 5 trial or concurrent benchmark.
Production/Hw5/Part 4 sources and historical evidence remain unchanged.

| Trial | Raw stepping seconds | Cold invocation seconds |
| --- | --- | --- |
| full_serial_r0 | 1047.9100364 | 1056.8112320 |
| full_parallel_r0 | 381.9162382 | 388.4043114 |
| full_parallel_r1 | 376.7153257 | 383.2620153 |
| full_serial_r1 | 1066.6222320 | 1075.2671255 |
| full_serial_r2 | 1066.8177625 | 1075.8132584 |
| full_parallel_r2 | 377.2070056 | 383.9497146 |

Median serial/parallel stepping 1066.6222320/377.2070056 s gives **2.827684047x
WHOLE-EXAMPLE speedup**. Sample SD 10.8603760/2.8713560 s; min..max
1047.9100364..1066.8177625 / 376.7153257..381.9162382 s. Cold medians
1075.2671255/383.9497146 s, speedup 2.800541541x. All samples retained; gain
exceeds observed variability. No old 1151-second observation, short interval,
profile, echo probe or bound was used as this baseline.

Matched settings: seed 7, 30 dynamic/five static solids, empty initial cache,
dt=1/480, 2880 steps/6 s, 120/20 sweeps, identical Options, both barriers and all
reports, no frames/rendering/sleeping. Thirty discarded collision warmup steps
from the genuine step-600 cache, then reset to the exact accepted initial world.
Eight workers/batch four/threshold zero; one pool through warmup and full run.
Requested native threads=1 equally; recorded affinity 0..23 per trial.

One continuous unprofiled stepping timer includes dispatch/IPC/gather/sync,
solving and identical 120-step journals. Journal I/O .04198–.06180 s was included,
not subtracted. Readiness, warmup, shutdown and final hashes/export/audit are
separate. Parallel startup .3750637.. .3941092 s; shutdown .0592954.. .0622029 s.
Cold timers include the whole child process/imports, setup/warmup, physics,
teardown and output/audit. Each parallel run performed 268543 real worker pair
queries in 69314 batches, 2880 trial +2880 diagnostic barriers, all eight PIDs
active; zero nonempty serial pairs and 462 empty local barriers. Pools joined;
final live inventory showed no Python process.

Acceptance identical for all six: 2880 steps, time 5.99999999999982 s, finite
states, quaternion residual 2.220446049250313e-16; five unchanged static bodies;
58754 body-body/117759 body-bin positive impulse rows. Maximum corrected depth
.016251535173982926 m, final .0011646418555887605 m, final-two-second maximum
.0012887548119564218 m. Original .03/.01 m limits passed. Independent analytic
extents pass x/z +/-2.01, bottom -.01, top 2.41 m with no outside IDs. Residual
speed .3882520607141568 m/s and kinetic energy .49507033512501347 J remain;
no complete-rest claim. Initial/final World/cache/options also match the old
accepted state; its elapsed time is not used in the benchmark.

Evidence: evidence/full_scene/comparison.json and REPORT.md; cohort.json pins
production plus evidence-harness hashes/runtime/checkpoint/configuration;
schedule.json records sequential alternating order. Every full_serial_r0..2 and
full_parallel_r0..2 folder retains metadata.json, record.json, journal.json,
cold_invocation.json, realized.json, acceptance.json, replay.pickle and
replayed_acceptance.json. Logs and historical_state_agreement.json are retained.
Journals are earlier incomplete snapshots; final records, wrapper exit=0 and
replay audits certify completion. Common exact canonical digest:
d8200d8e082505b79ba235cc1aca6a1d11f9757d02ad4ecd6c47e7ff166d5965.

The prepared Part 4 script was inspected/preserved; an audited evidence-only
equivalent was needed for incremental journals and retained states/reports.
Four short harness checks passed before timing; existing 48-test evidence was
preserved. No production bug fix or relaxed tolerance. No install, commit, push,
package, full cProfile or extra rendering benchmark. All requested documents
are updated; source hashes still match the measured cohort.

Remaining: student-authored reflection (still EMPTY), separately authorized real
HW7/Hw5 Git history and final verified packaging with required sources and actual
root .git. HEAD remains 2c4b36c; hw7/Hw5 untracked; unrelated files and hw7 (3).zip
preserved. Broader seeds/extreme geometry/live GUI/thermal/native-pool controls
remain disclosed limitations. Part 5 is complete, HW7 submission is not.
Next audit needs no simulation:
`python -B -m hw7.evidence.full_scene.runner replay --label full_parallel_r0`.
The schedule skips compatible completed trials; do not rerun old full labels.

## Historical Part 5 running checkpoint — 2026-11-05

Latest confirmed completed trial at this checkpoint: full_serial_r0, 2880 steps,
1047.9100364 s stepping / 1056.8112320 s cold invocation, accepted=true. Maximum
corrected depth .0162515352 m; final .00116464186 m; final-two-second maximum
.00128875481 m; full analytic containment passed, all states finite, five static
records unchanged. Residual speed .388252 m/s and kinetic energy .495070 J, not
complete rest. Replay/final state saved; canonical exact reference digest
d8200d8e082505b79ba235cc1aca6a1d11f9757d02ad4ecd6c47e7ff166d5965.
Next confirmed completed trial: full_parallel_r0, 381.9162382 s stepping,
accepted=true and complete World/cache/report digest EXACTLY equal to serial_r0.
Measured worker pair queries=268543; readiness/startup .3791065 s, shutdown
.0599697 s; every worker exited normally. full_parallel_r1 has started. Two of
six trials were complete at that checkpoint. Subsequent confirmed completions:
full_parallel_r1 = 376.7153257 s, full_serial_r1 = 1066.6222320 s, both accepted
and exactly equal to the reference. Four of six are now confirmed complete;
full_serial_r2 then completed in 1066.8177625 s, accepted and exactly equal.
Five of six trials are now confirmed complete; full_parallel_r2 is running.
Final medians/speedup remain pending until its acceptance/reference checks pass.

Preflight and four evidence-harness checks passed. Production/Hw5 source hashes
still exactly match the Part 4 compatibility manifest. No applicable AGENTS.md
was found. Root HEAD remains 2c4b36c; unrelated root README/Hw5/hw6/PDF and the
student's existing hw7 (3).zip are preserved. No installs/commits/push/package.

Evidence-only runner/audit/resumable schedule are under evidence/full_scene/;
they preserve the prepared script and existing Part 4 records. Cohort.json pins
all measured production sources plus the new harness hashes and exact settings.
The old runner saved only hashes, so the new runner saves realized initial/final
JSON and full trusted replay World/cache/StepReports AFTER stepping time. Both
backends include identical 120-step progress writes inside ONE continuous wall
timer, with journal I/O measured separately; no resumed simulation segments.

CPython 3.12.10, NumPy 2.3.5, SciPy 1.17.1, Matplotlib 3.10.8; affinity 0..23,
AC power, requested OMP/OpenBLAS/MKL/NumExpr threads=1. Genuine cached step-600
warmup compatibility passed. Exactly 30 dynamic/five static bodies, seed 7,
dt=1/480, 2880 steps, 120/20 sweeps, identical Options/reports/diagnostics, empty
initial cache and no frames/rendering/sleeping. Warmup is 30 discarded steps
from the step-600 checkpoint, then reset to the exact accepted seed-7 initial
world. Parallel pool: eight workers, batch four, threshold zero, reused through
warmup and all measured timesteps; readiness/shutdown outside stepping time.

Started the sequential schedule `python -B -m hw7.evidence.full_scene.schedule`:
serial_r0, parallel_r0, parallel_r1, serial_r1, serial_r2, parallel_r2. Current
status/completed trial list is evidence/full_scene/schedule.json; per-trial
journal.json is explicitly incomplete until final record.json acceptance/exact
checks pass. Logs are evidence/full_scene/logs/. No full-scene completion or
speedup is claimed at this running checkpoint. Healthy runs have no timeout.
Resume skips compatible complete trials and restarts partial trials under a new
attempt label from step zero, never splicing timings. Exact mismatch stops the
remaining schedule. Personal reflection remains empty.

## Historical Part 4 checkpoint

## Current checkpoint: Part 4 implementation, correctness and interval pilot complete

Persistent spawn collision workers now exist in parallel.py and are connected to
both world.py detection barriers and falling_objects.py. The pool is reused
across timesteps; immutable pair queries use unchanged narrow_phase arithmetic,
dynamic batches and canonical gathering. All physical/split impulses and cache
updates stay ordered in the parent. Worker errors, startup failure, unexpected
exit and interruption clean up owned workers and propagate without fallback.
Backend/workers/batch/threshold controls are exposed; default threshold zero.

| Stage | Current actual status |
| --- | --- |
| Serial implementation/acceptance | Preserved; original arithmetic/Hw5 hashes unchanged, historical serial interval digests reproduced |
| Correctness | 48 short tests passed; exact 30-step World/cache/report agreement on genuine cached steps 389, 600 and 1440; full parallel scene pending |
| Profiling | Part 3 intervals preserved; complete cProfile/repeated full baseline/rendering benchmarks still pending |
| Parallel backend | Implemented persistent Windows-spawn pool, both barriers, lifecycle/dispatch/PID evidence |
| Performance comparison | Matched repeated short intervals demonstrate gains; complete 2880-step acceleration remains unmeasured |
| Documentation | Part 4 actual behavior/results/limitations updated; student reflection empty |
| Git history | Root HEAD 2c4b36c; hw7/Hw5 still untracked; no commits or push |
| Packaging | Not finalized or clean-environment verified; old ZIPs remain incomplete |

Latest short command (root, installed Python 3.12.10):
`C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe -B -m hw7.parallel_checks tests_v3`.
48 passed, zero failures/errors/skips, 5.3200469 s. Evidence:
evidence/parallel_pilot/tests_v3.log/.json. Nine real-spawn tests cover all shape
pairs/cache/enrich flags, rotating nonspherical multistep contacts, both barriers,
different counts/batches, reversed completion consumption, reuse/validation and
success/error/startup/dead-worker/interruption cleanup, plus exact zero physical
energy in stationary split correction. Geometry/solver/profiling regressions
also passed. No long acceptance/full cProfile was repeated.

`parallel_pilot validate --label validation_v3` passed direct exact World/cache/
report equality for all three genuine 30-step starts; current serial digests
also exactly match original Part 3 runs. Historical checkpoints remain immutable.
Explicit compatibility_v3.json pins old/current source IDs and every current
source hash; only audited world/CLI dispatch interfaces changed among original
physics modules. Strict source checking remains the default. No tolerances were
introduced. Every screen/repeat canonical value digest matches that reference.

Screen: serial plus 2/4/8 workers, batches 4/8, 21 sequential trials. Then fresh
serial/4/8-worker batch-4 configurations received three trials each per interval,
alternating order (27 trials). Raw unprofiled stepping seconds:

| Interval | Serial | 4 workers / batch 4 | 8 workers / batch 4 |
| --- | --- | --- | --- |
| 389..419 | 12.6433017, 12.5864567, 13.1268164 | 4.5984833, 4.6139579, 4.5568106 | 3.7392719, 3.6147029, 3.6541155 |
| 600..630 | 5.7040663, 5.7273241, 5.6695913 | 2.7347167, 2.6927825, 2.7306732 | 2.6700993, 2.6722559, 2.6576842 |
| 1440..1470 | 14.9351282, 14.8250897, 14.3579822 | 5.0691963, 5.1243991, 4.8760941 | 4.2089745, 4.1804853, 4.1894319 |

Median speedups: four workers 2.749x / 2.089x / 2.925x; eight workers 3.460x /
2.136x / 3.539x. All are ONLY 30-step/.0625-s intervals, not the full 2880-step
scene. Evidence: parallel_pilot/comparison.json, REPORT.md, screen_v1/ and all
repeat_* directories. PROFILE.md includes SDs, every screen time and overhead.
Same seed/options/dt=1/480/120+20 sweeps, both diagnostics and reports, no frames
or rendering. Physics timer includes dispatch/IPC/gather/synchronization; excludes
load/setup, four discarded warmup steps, final hashes/output and teardown.
Every trial resets the identical world/cache and uses a persistent pool through
warmup/measurement. Parent/child requested native thread limits are one.

Real measured worker pairs: 1650 / 2121 / 3420, with 30 trial and 30 diagnostic
barriers; PID-level actual work retained. Dense intervals use seven of eight
configured workers, others all eight. Four-worker startup .3137–.3239 s and
shutdown .0374–.0533 s; eight-worker startup .3613–.3791 s and shutdown
.0535–.0651 s. Cold invocation medians serial/four/eight: dense 14.1173/5.8691/
4.8642 s, impacts 6.7706/3.8243/3.8617 s, pile 16.8286/6.5297/5.6790 s.
Cold costs include imports/loading/warmup/hashing/output/cleanup; do not confuse
them with steady stepping. Echo IPC, bounds, profiled times and historical
1151-second frame-sampled acceptance were not used as benchmark baselines.

Recommend 8 workers/batch 4/threshold 0 as the preliminary full-scene candidate;
4/batch 4 is a lower-overhead alternative (slightly faster cold short-impact
invocation). Batch-8 inferior screens remain preserved. No observed unresolved
numerical mismatch; cheap-pair IPC costs, full-scene weighting, filesystem/
thermal effects and complete-scene correctness/performance remain unmeasured.
No major compiled rewrite was started.

All commands finished; final live inventory showed no Python process. tests_v2's
transport-type error and validation_v1's JSON list/tuple check failure are fixed
and preserved, not relabeled. Intentional budget-test artifacts remain incomplete;
pre-Part-4 interrupted/budgeted records remain historical. LOG records the
execution-policy/reporting-assertion fixes and relocation of this turn's new
profiling test artifact; no old evidence was overwritten. Only hw7 changed;
unrelated working-tree files/Hw5/ZIPs, empty reflection and real Git history were
preserved. No installs/commits/pushes.

Next concrete action: final matched 2880-step runs with 8/batch 4, exact reference
comparison and cold timers. The exact standalone module commands are in PROFILE;
prefer the prepared alternating-order script below. It has NOT been run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File hw7/evidence/parallel_pilot/final_matched.ps1 -Python 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe'
```

This future series performs three full runs per backend. Whole-example
acceleration, actual HW7 Git commits, student reflection and final verified
packaging are still required before claiming HW7 complete.

## Historical Part 3 checkpoint (records below preserved)

## Status audit — 2026-11-05 (inspection only; supersedes older status summaries)

Checked now from the HW3_submission root: ancestor/root/recursive repository AGENTS.md search (none found), Git status/history, the five requested documents, current CLI/world/solver/model and profiling/analysis/test source, newest raw JSON completion records, test logs, timing metadata/digests, source hashes, ZIP entry lists and the live Python process list. No tests, simulations or benchmarks were run now. Only this checkpoint was edited; historical records below and the student's empty personal reflection are preserved.

| Stage | Actual status |
| --- | --- |
| Serial implementation | Complete for the documented acceptance scope; current source matches the file hashes in peak_plain/metadata.json, including Hw5 dependencies. |
| Correctness | Recorded serial suites/default acceptance passed; broader stress coverage and live GUI remain unverified. No serial/parallel correctness test exists. |
| Profiling | Representative intervals complete; full profile, repeated full-scene plain baseline and formal rendering benchmarks incomplete. |
| Parallel implementation | Absent. falling_objects.py allows only serial; world.step_world/simulate reject other backends. |
| Performance comparison | Absent. Parallel speedup has not yet been demonstrated. |
| Documentation | Substantial serial/profiling documentation exists; final parallel results/finalization pending. Student reflection remains empty. |
| Git history | Root history exists at 2c4b36c; hw7 and Hw5 are untracked, with no HW7 commits. |
| Packaging | Incomplete/unverified. Both root ZIPs omit Hw5 and .git (46 and 269 entries respectively); neither is a self-contained final submission. No fresh extraction/environment check exists. |

There is no implemented worker method/count/batching/lifetime or proven parallel determinism. The recommendation ONLY is persistent Windows-spawn workers, initially 2/4/8 workers and batches around 4–8 pairs, reused across steps; unchanged narrow-phase/manifold queries at both detection barriers, canonical parent gathering/cache updates and ordered serial impulses. profile_analysis.py's spawned worker only echoes data; island decomposition also solves serially.

### Recorded completed checks (not rerun now)

Interpreter prefix for every command below: `C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe -B -m`.

| Exact module/arguments | Recorded result | Evidence |
| --- | --- | --- |
| `unittest -v hw7.tests.test_profiling hw7.tests.test_solver` | Latest reported 18 passed in .179 s. LOG records the result; no retained full unittest-output log/count JSON was found. The newest test_partial directory corroborates the budget-test execution, not all 18 passes. | LOG.md, tests/test_profiling.py; evidence/profile_serial/test_partial_48e18a4d9db54206865d1e35668fe494/ |
| `hw7.verify --suite focused` | 35 passed, 0 failures/errors/skips, .820246 s | evidence/focused_tests.log and .json |
| `hw7.verify --suite hw7` | 41 passed, 0 failures/errors/skips, 374.1995584 s | evidence/hw7_tests.log and .json |
| `hw7.verify --suite hw5` | 72 passed, 0 failures/errors/skips, 7.7182694 s | evidence/hw5_tests.log and .json |

The 41/35 runs cover 44 distinct HW7 methods, not one 44-test run. Historical development_240hz_tests records 41 tests with one failure; it remains superseded failed evidence. The separate completed default command was `hw7.falling_objects --headless --json hw7/evidence/serial_default.json --snapshot hw7/evidence/falling_objects.png`; `hw7.evidence.audit_default` recorded accepted=true. Raw serial_default.json has 2880 steps/6 s, 30 dynamic/5 static bodies; maximum corrected depth .0162515352 m, final .00116464186 m, residual speed .388252 m/s. This is accepted serial behavior, not perfect rest.

### Raw serial wall measurements and comparison limits

Seed 7, 30 dynamic bodies/5 bin prisms, dt=1/480, 120 physical/20 split sweeps and unchanged Options. Every interval is only 30 steps (.0625 simulated seconds), three plain repetitions, four discarded warmup steps and reset to the identical world/cache. Raw seconds, rounded to seven decimals:

| Range | Raw seconds | Evidence directory under evidence/profile_serial/ |
| --- | --- | --- |
| 0..30 | .0981013, .0862518, .0888735 | free_plain/ |
| 389..419 | 14.3891300, 14.0789681, 14.3094633 | peak_plain/ |
| 600..630 | 4.6480750, 4.6967277, 4.7177635 | impacts_plain/ |
| 1440..1470 | 15.9091579, 17.0314607, 15.5676890 | pile_plain/ |

Each directory retains metadata.json, measurements.json and run_00..02.json. Timing is unprofiled wall time around step_world/report append, including both collision diagnostics and serial solver; excludes imports/setup/loading, warmup, graph analysis, output/rendering, with no frames/GUI. Inspected raw World AND report digests agree across plain/stages/cprofile for all four intervals. This verifies instrumentation agreement, not parallel agreement. No parallel timings exist to match scene/dt/step count/options/diagnostics/output mode.

The complete 2880-step serial acceptance observation is 1151.3943472 s, including diagnostics/reports and frame sampling every 16 steps; excludes imports/setup/rendering/JSON. Snapshot render .8160687 s separately. It is a single nonrepeated observation with a different output mode, not a controlled full-scene baseline. Full-profile 45.342076 s is profiled and partial, not a speed baseline. Echo startup .3578538 s and reused round-trip median .0004283 s measure IPC only; neither worker startup nor steady-state PHYSICS timing has been measured for a parallel backend. Estimated bounds are not speedups.

### Live/incomplete work and next action

Read-only Win32_Process inventory now returned no python.exe/pythonw.exe processes. No simulation was started or terminated during this audit. Raw status inspection identifies: full_profile_budgeted/run_00.json partial_budget/complete=false at 389/2880; states_1440/prepare.json interrupted_external/complete=false, saved progress 600..960 (360/840 requested). Later states_1440_confined completed preparation to 1440; it does not complete the earlier command. Both test_partial_* directories intentionally record budget stops at 1/10 steps and are test artifacts, not scene runs. The earlier interrupted default has a later completed replacement; history is retained below. No active Python command was observed; incomplete records stay incomplete.

Blockers to completion: missing parallel physics backend and correctness comparison, missing matched unprofiled full-scene measurements, final history/packaging validation, and student-authored reflection. No missing assignment information is recorded. Next concrete development action, after this inspection-only stop: review/define the deterministic pair-worker input/result/cache protocol and persistent pool lifecycle before implementation, then validate serial/parallel agreement and collect matched full-scene timings with startup separated. Do not launch those commands as part of this audit.

For review upload the current hw7/ tree (including tests and all retained evidence/profile_serial metadata/raw runs/checkpoints, historical failures and images), plus Hw5 source dependencies __init__.py, dynamics.py, spatial.py, geometry.py and rigid.py. Include the real root .git directory if Git history is to be reviewed. The existing ZIPs are not current complete review packages and do not contain this checkpoint.

## Current checkpoint: representative profiling complete

Part 2 acceptance below is preserved. Part 3 added `profiling.py`, `profile_analysis.py`, `tests/test_profiling.py`, optional phase callbacks in `solver.py`, a native-temp ignore rule, instrumentation documentation and new evidence exclusively under `evidence/profile_serial/`. Arithmetic, physics options, scene and solver ordering are unchanged. PROFILE/README/LOG/implementation_plan now describe actual measurements and pending work. Root README, untracked Hw5/hw6/lecture PDF and hw7.zip are preserved; no installs, commits, pushes or Hw5 changes.

Measured machine: Core Ultra 9 275HX, independently reported 24 physical/24 logical cores, affinity 0..23, Python 3.12.10. Four 30-step intervals each have three plain repetitions plus separate cProfile/stage profiles: free fall median .0888735 s; dense impacts (389..419) 14.3094633 s; continuing impacts (600..630) 4.6967277 s; pile (1440..1470) 15.9091579 s. Later states came from genuine simulation with the complete contact cache. Narrow-phase kernels account for 83.5–90.8% of collision-heavy stage time, plus 1.9–2.4% manifold/cache work. Raw timings, exact commands, source hashes and scope are in each run metadata and PROFILE.

Verification: `python -B -m unittest -v hw7.tests.test_profiling hw7.tests.test_solver` passed 18 tests in .179 s (latest run); no completed long correctness suite was repeated. `python -B -m hw7.profiling validate --label validate_collision --checkpoint hw7/evidence/profile_serial/states_0600/checkpoints/step_000240.pickle --steps 60` passed exact world AND report equality with collision present. Plain/stage/cProfile digests also agree for every measured interval. Failure restoration and nonzero partial-budget handling are unit checked.

An early preparation was externally interrupted after its last saved step 960; its journal is explicitly incomplete. SciPy's temporary-file fallback was discovered through profiling; later tools confine tempfile/TMP/TEMP under the evidence directory. Resumed preparation reached step 1440. All commands are now finished; none is running. The full cProfile attempt was budget-stopped at 389/2880 steps in 45.342076 s, saved partial stats/checkpoint and returned nonzero. Full-scene profile, three-run full baseline, rendering timings and all parallel comparisons remain pending. Historical 1151 s acceptance runtime is not a formal baseline.

Recommended next backend: persistent spawned processes batching unchanged pair/manifold queries at both detection barriers, canonical parent gathering and serial impulses; fallback compiled GIL-releasing batch kernel. Echo-only IPC and serial island decomposition probes were measured; no parallel physics backend exists. Optimistic imbalance-aware interval bounds are about 3x at four workers and 3.7–4.3x at eight, before overhead; no measured whole-scene bound or speedup is claimed.

Next concrete step: review the deterministic worker input/result/cache protocol and full-baseline gaps before implementing parallelization. To finish full-scene evidence when practical, use a fresh label for the long command `python -B -m hw7.profiling measure --label full_resume --steps 2880 --mode cprofile --journal-every 30`; use `--mode plain --repeats 3` for the future full wall baseline, with PROFILE's short collision warmup/reset policy. This step deliberately did not launch that long series. `python -B -m hw7.profile_analysis summarize` refreshes aggregation without rerunning physics. Keep native-temp location and numerical/source settings fixed. No missing assignment information blocks the next stage; toolchain availability matters only if the native fallback is chosen.

## Preserved Part 2 acceptance checkpoint

**The resumed Part 2 acceptance work is complete for the documented scope.** The default 2880-step/6 s run completed, the independent saved-state audit passed, and initial/final Agg PNGs were inspected. Maximum corrected penetration .0162515352 m; maximum over the final two seconds .00128875481 m; final depth .00116464186 m. All 30 dynamic bodies' full analytic extents are inside the bin tolerance, and all five bin records are unchanged. Evidence: serial_default.json, default_audit.json, initial_scene.png and falling_objects.png under evidence/. Production physics was unchanged during the resume, and completed passing test suites were not repeated.

The run took 1151.3943472 s (about 19 min 11 s) in the physics loop with diagnostics, reports and frame sampling. It retains motion at 6 s (maximum speed .388252 m/s; kinetic energy .495070 J). This is accepted contact/containment/finite-state evidence, not a promise of complete rest, a formal profiling baseline or a speedup. Live GUI playback, wider stress coverage, formal profiling/parallel work and final packaging/history are still pending. The earlier pause/interruption details are preserved below as history.

## Working tree and scope

Repository: `D:\CodexCLI\vibecoding\HW3_submission`; HEAD remains `2c4b36c` (`Add HW4 testing log transcript and final documentation`). Inspected Git status without reverting anything:

```text
 M README.md
?? Hw5/
?? "MECE 4990 Lecture 6.pdf"
?? hw6/
?? hw7/
```

The root README edit, Hw5/, hw6/ and lecture PDF predated this work and were preserved. All new/modified deliverables are under hw7/. No Hw5 source edits, installs, commits, pushes or nested repository were made. No applicable AGENTS.md was found during the implementation's root/ancestor/repository inspection.

## Implemented features and files

- `model.py`, `math3.py`, `__init__.py`: validated immutable bodies/world/options, static flags, internal tuple algebra. Hw5 solids, inertia, RigidState, quaternion helpers and free-flight kick are imported unchanged.
- `collision.py`: rotation-aware analytic AABBs, closed-interval deterministic sweep and prune; true-shape support maps and witness GJK/EPA. SciPy/Qhull constructs/rebuilds the internal support hull. Exact sphere-solid and certified finite-face branches are documented; cylinders are not replaced with spheres or display meshes. Brute-force overlap exists only in tests.
- `manifolds.py`: local anchor persistence, box clipping, cylinder cap/generatrix seeds, perturbation with original-pose witness mapping, deterministic four-point reduction. Complete planar line/face cases avoid fictitious curved-side patches.
- `solver.py`, `world.py`: physical normal/restitution/Coulomb friction impulses with world inertia/angular response; separate split-impulse push/turn velocities; fixed endpoint ordering; capped pose corrections; per-point impulses and before/after penetration diagnostics. Defaults are 120 alternating physical sweeps and 20 pseudo sweeps, slop .0001 m, beta .2, row depth cap .03 m, per-body translation cap .01 m/rotation cap .05 rad. No parallel backend, sleeping, freezing or teleportation.
- `scene.py`, `falling_objects.py`: exact 30-body scene (ten per shape) and five finite static bin prisms, seed/step/timestep/iteration controls, headless summary and optional realized-state JSON. CLI default is seed 7, h=1/480, 2880 steps = 6 s. Generic Options still defaults to h=1/240 for small fixtures.
- `rendering.py`: Matplotlib saved-frame playback and Agg snapshots, recognizable display meshes and orientation markers. Physics is independent of playback speed. Initial/final Agg images have now been generated and visually inspected; live GUI playback remains unverified.
- `tests/__init__.py`, `tests/test_geometry.py`, `tests/test_solver.py`, `tests/test_system.py`: unittest geometry/broad-phase, independent analytic/SAT oracles, impulses/energy/friction, split correction, rest/stacks and real-contact scene checks.
- `verify.py`: verbose test runner preserving command/version/results; confines temporary files and Matplotlib cache under hw7/evidence.
- `requirements.txt`, `.gitignore`: declared existing NumPy/SciPy/Matplotlib dependencies and ignored generated cache/temp directories. No installation occurred.
- Updated `SPEC.md`, `TEST_PLAN.md`, `README.md`, `PROFILE.md`, `implementation_plan.md`, `LOG.md`. SPEC records design corrections and reasons, including failed development results; PROFILE leaves formal profiling/parallel work pending.
- `evidence/diagnose.py`: development diagnostic; `evidence/audit_default.py`: independently calculates final analytic extents and checks counts/IDs/clocks/static records/finite states/penetration. This audit now passed, including an added upper-rim containment check. The initial pause wrote PROGRESS/LOG only; the resume also updated acceptance documentation/audit and generated the final JSON/PNG evidence, without production physics edits.

## Executed tests and actual results

All commands below used this installed interpreter from the repository root:

```text
C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe
CPython 3.12.10, MSC v.1943, 64-bit AMD64
```

Imports of NumPy 2.3.5, SciPy 1.17.1 and Matplotlib 3.10.8 were verified. Interpreter access required approved execution outside the sandbox; -B disabled bytecode. Formal performance comparisons were not made. Exact verbose test names and command lines are preserved in the referenced logs.

| Actual module command (interpreter prefix above, `-B -m`) | Result / evidence |
| --- | --- |
| `unittest -v hw7.tests.test_geometry` | Initial 19 tests: one failed exact float equality for sphere AABB minimum (`1-.7` versus literal `.3`). Replaced exact equality with the already planned 1e-12 roundoff budget, without changing geometry expectations. |
| `unittest -v hw7.tests.test_geometry hw7.tests.test_solver` | 31 passed; later 32 passed after independent OBB SAT test was added. |
| `unittest -v hw7.tests.test_system.RestingAndStackingTests` | Initial seven-test run: two failures (horizontal cylinder speed, box drift) and one EPA topology error; fixes and superseded partial runs are recorded in LOG. |
| `hw7.verify --suite hw5` | **72 passed; zero failures/errors/skips**, 7.7182694 s. `evidence/hw5_tests.log` and `.json`. Includes existing Hw5 numerical and snapshot regressions; no Hw5 edits. |
| `hw7.verify --suite hw7` with former 240 Hz scene | **41 run; one failure, zero errors**, 237.341 s. Only 30-body transient penetration exceeded .03 m (.0408722 m); all rest/stack fixtures passed. Preserved as `evidence/development_240hz_tests.log` / `.json`. NOT accepted scene evidence. |
| `hw7.verify --suite hw7` with refined 480 Hz scene | **41 passed; zero failures/errors/skips**, 374.1995584 s. `evidence/hw7_tests.log` / `.json`. Tests were discovered before three additional focused methods were added. |
| `hw7.verify --suite focused` | Latest **35 passed; zero failures/errors/skips**, .820246 s. `evidence/focused_tests.log` / `.json`. Includes the three additions (invalid bounds, anisotropic world inertia, sticking friction), explicit zero physical kinetic energy, angular cap, false Options and zero-step backend validation. |

The passing full/focused logs contain **44 distinct HW7 test methods** (verified from verbose names). This is not a claim that one 44-test discovery run occurred. The final argument-validation edits leave normal physics arithmetic unchanged and were checked by the final focused run; the complete long suite was not repeated after those validation-only edits.

The accepted automated 30-body smoke covers **1440 steps/3 s at 480 Hz**: maximum corrected penetration .0162515352 m; final .00116379546 m; maximum in its final two seconds .00854309918 m. All 30 bodies finite; all five static bodies unchanged; no escaped COM IDs. Body-body/bin impulses and all three shape categories are exercised. Its final maximum speed was 1.15702 m/s and kinetic energy 1.54393 J, so it is not fully settled. The separate default six-second acceptance has now also passed as recorded above; no earlier failed development result was relabeled as accepted.

All four single-body rest fixtures and both three-body stacks ran for 10 s at 240 Hz and passed their original limits. Maximum corrected depths: .00078125 m for single bodies, .000851177 m for boxes, .000847273 m for cylinders. Final maximum stack speeds: .00027927 and .000464083 m/s. Sphere timestep refinement matched the independent steady-depth formula `slop+4*g*h^2`; stationary split correction matched .01 -> .00802 m and exactly zero physical velocities/kinetic energy.

Additional completed development commands were `hw7.evidence.diagnose cylinder`, `hw7.evidence.diagnose stack box 60 2400`, and `hw7.evidence.diagnose stack cylinder 120 240`. These inspected contact geometry/convergence; they were not formal tests or benchmarks. `first_720.json` preserves an early unacceptable scene (max corrected penetration .336619 m); `corrected_480.json` preserves a later 240 Hz transient failure (.0336833 m). Do not cite either as final success. See LOG for the initial GJK failure and exact fixes.

## Interrupted work at the earlier pause — historical record

The default command was still outstanding at the earlier pause (it has since been rerun successfully from its initial state):

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw7.falling_objects --headless --json hw7/evidence/serial_default.json --snapshot hw7/evidence/falling_objects.png
```

It used unified exec session **36307** (observed Python PID 17196 before the interruption). At this checkpoint, neither serial_default.json nor falling_objects.png was present. A Ctrl+C stop was sent to that specific session; it closed with exit code **1** and no final summary. No six-second physics time, final state, snapshot or settling result is available. The previous user turn was also deliberately interrupted; the exact last completed simulation step is unknown. Do not treat the interrupted command as a pass or as a restartable saved state.

Earlier superseded development runs were stopped with Ctrl+C: repeated resting/stacking commands (sessions 44069 and 86615) and `hw7.falling_objects --headless --steps 720 --json hw7/evidence/corrected_720.json` (session 30855). No completed corrected_720.json is present; no success is claimed for these partial runs. The original first_720 command first failed on GJK exhaustion, then a repeated completed run wrote the explicitly failed development evidence noted above.

At the pause, `hw7.evidence.audit_default` had not been executed and no HW7 snapshot had been inspected. Both are now complete. Live GUI testing, formal cProfile/stage instrumentation, repeated baseline timing, parallel selection/implementation, clean-environment packaging and final Git commits remain undone.

## Known issues and remaining work

- Six-second contact/penetration/finite/full-shape containment acceptance now passed, with residual physical motion explicitly reported. Arbitrary seeds and longer-term behavior are not certified.
- Serial execution is slow: the resumed default's physics-loop observation is about 19 min 11 s. It includes diagnostics/report retention/frame sampling and is not a controlled warmed/repeated baseline or speedup measurement.
- Discrete stepping can tunnel at high speeds; arbitrary seeds, extreme scales/mass/aspect ratios and deep tangled initial overlap are not validated. Iteration/hull failures are explicit.
- Cap/contact patches are sampled; finite iterations leave residual drift. Broad randomized cylinder depth oracles, systematic cache churn, and a separate HW7 nonspherical free-flight convergence study remain gaps. Existing Hw5 conservation/refinement tests passed.
- Sphere/cylinder free rolling or torsional spin is not artificially suppressed; no claim of perfectly motionless piles. Split pose correction can change potential energy/anisotropic rotational energy at nonzero spin.
- GUI animation is implemented but live interaction remains unverified. Initial/final static Agg snapshots were successfully generated and visually inspected. Requirements declare dependencies, but another clean environment has not been tested.
- Student reflection section in LOG.md remains empty. Real Git history must be included during later authorized packaging; no commits are authorized at this checkpoint.

## Resume acceptance procedure — completed

The resume read the checkpoint, rechecked instructions/Git status, restarted the default **from its initial state**, ran the saved-state audit and inspected both PNGs. The first two commands below completed successfully; the conditional focused command was not needed because production arithmetic did not change. Completed rest/stack/Hw5 suites were not repeated.

```powershell
# From D:\CodexCLI\vibecoding\HW3_submission; acceptance commands completed after resume.
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw7.falling_objects --headless --json hw7/evidence/serial_default.json --snapshot hw7/evidence/falling_objects.png
# Run only after the example successfully writes its final JSON:
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw7.evidence.audit_default
# If code changes are required, start with the fast focused regression checks:
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw7.verify --suite focused
```

Actual default/audit/visual results are recorded in LOG, TEST_PLAN, README, SPEC, PROFILE and implementation_plan. The .03 m transient/.01 m final-window and containment checks passed unchanged. The student's personal-reflection section is empty; no commit, push, install or nested repository was created.

## Next concrete step — formal profiling, not started in Part 2

After the next profiling task is authorized, follow PROFILE.md: recheck the environment/power/affinity conditions, profile the fixed single 30-body scene by stage/cProfile, and then collect controlled warmed/repeated physics-only and separate rendering timings. For example, the planned whole-scene cProfile command is:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m cProfile -o hw7/evidence/serial_default.prof -m hw7.falling_objects --headless
```

This command has NOT been executed; profiling adds overhead to an already slow serial run. Use identical scene, 480 Hz timestep, 2880 steps and 120/20 sweeps for eventual serial/parallel comparisons. Do not choose a final parallel method or claim improvement before measurements. Keep artifacts under hw7/ and preserve unrelated changes and the real root Git history.
