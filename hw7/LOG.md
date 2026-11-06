# HW7 activity log

## 2026-11-04 — Part 1, agent activity

Inspected the repository root, working-tree status and five recent Git subjects. Starting HEAD was `2c4b36c` (Add HW4 testing log transcript and final documentation). Existing status: modified root README.md; untracked Hw5/, hw6/, and MECE 4990 Lecture 6.pdf. These were left in place. Checked AGENTS.md at the root and ancestor directories through D:/, and recursively searched the repository (including hidden entries); no applicable AGENTS.md was found. No nested repository was created and no commit, push, dependency installation or production-physics edit was performed.

Read Hw5 specification/documentation and inspected its source, seven test modules and five examples. Identified reusable immutable solids/inertia, body-frame rigid state, Hamilton quaternion utilities, free-flight velocity kicks and display meshes. Confirmed its one-support ground projection and limited bilateral joint solver do not implement multi-body contact. Audited Python imports: physics depends on standard-library modules and sibling Hw5 source; example visualization imports Matplotlib optionally. Historical documentation links external source documents/images, but no production runtime load of those files was found.

Inspected root requirement lists and obtained a read-only runtime/hardware inventory. Initial sandbox access to Python/Windows processor information failed; an approved read-only command outside the sandbox reported CPython 3.12.10, Windows 11, Intel Core Ultra 9 275HX, 24 logical processors and 24 physical cores from Windows processor fields. Distribution metadata listed NumPy 2.3.5, Matplotlib 3.10.8, SciPy 1.17.1, psutil 7.2.2 and PyVista 0.49.0, with Numba/joblib absent. This was environment inspection, not simulation profiling, dependency import validation, or a performance test.

Consulted primary Bullet implementation sources and Erin Catto's Contact Manifolds presentation, linked in SPEC.md. Wrote a design using analytic support GJK/EPA, finite static bin prisms, deterministic sweep and prune, persistent multi-point manifolds, physical Coulomb impulses and separate pseudo-velocity penetration correction. Wrote independent geometry/impulse/energy/split-impulse checks and a serial-first measurement plan; no final parallelization method or speedup was selected. Created only SPEC.md, TEST_PLAN.md, PROFILE.md, README.md, LOG.md and implementation_plan.md under the new hw7/ directory. Reviewed the documents and repository status for consistency and scope. No planned code, tests, benchmarks or GUI behavior was executed.

## 2026-11-04 — Part 2, agent activity

Rechecked root/ancestor/repository AGENTS.md locations (none found), Git status, all six Part 1 documents and actual Hw5 geometry/rigid/spatial interfaces. All Part 1 files were present. Starting status remained modified root README.md and untracked Hw5/, hw6/, lecture PDF and hw7/. All Part 2 source, tests and evidence are confined to hw7/. Hw5 and unrelated files were not edited. No dependencies were installed, no commits/pushes were made and no nested Git directory was created.

Implemented immutable Body/World/Options, exact rotated bounds and closed-interval sweep and prune; analytic sphere closest-surface contacts and support GJK/EPA for other convex pairs; finite bin/body handling; clipping, cap/generatrix seeds, persistent anchors, four-point reduction and perturbation; world-inertia physical/friction impulses and separate push/turn correction; fixed endpoint order; 30-body deterministic scene; headless/JSON CLI; saved-frame Matplotlib visualization; and standard-library unittest checks. Existing Hw5 shapes, inertia, quaternion/state validation, free velocity kick and display meshes are imported unchanged. SciPy/Qhull builds internal EPA support hulls, without substituting collision geometry. NumPy/SciPy/Matplotlib requirements and portable commands are declared. Explicit installed import check reported CPython 3.12.10, NumPy 2.3.5, SciPy 1.17.1 and Matplotlib 3.10.8. No auto-install was used.

Design corrections were written into SPEC before each corresponding change: robust hull seeding/reconstruction instead of manual EPA horizon maintenance; exact sphere-solid and certified finite prism-face branches; corrected incident-face clipping/shallower patch acceptance; removal of fictitious curved-side area patches; tilted cylinder-cap seeding; 120 alternating physical sweeps after 30/60-sweep stack drift; .03 m row correction depth cap; and fixed 480 Hz example stepping after 240 Hz exceeded transient penetration targets. No resting/stacking/full-scene penetration acceptance limit was enlarged to obtain a pass. The only test-oracle correction was replacing exact float equality for the sphere bound `1-.7` with the previously planned 1e-12 roundoff budget: binary arithmetic yields .30000000000000004 whereas literal .3 is a different representable float. The analytic geometric expectation remains .3 m.

Actual interpreter for commands below: `C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe`, invoked with `-B -m ...` from repository root. Access required approved outside-sandbox execution because sandbox access to the installed interpreter was denied. Bytecode was disabled. `hw7.verify` confines temporary files and Matplotlib cache to hw7/evidence and saves actual command/version/verbose names, counts and output.

| Executed command/module | Observed development result |
| --- | --- |
| `unittest -v hw7.tests.test_geometry` | 19 tests: one exact-float-bound assertion failed; corrected as independently explained above. All shape-pair and bin subfixtures passed. |
| `hw7.falling_objects --headless --steps 720 --json hw7/evidence/first_720.json` | First attempt stopped explicitly on perturbed cylinder-pair GJK exhaustion. Fixed cancellation in near-collinear triangle barycentrics, not the iteration cap. Repeated run completed but max corrected penetration .336619 m was unacceptable; preserved first_720.json is FAILED development evidence. |
| `unittest -v hw7.tests.test_geometry hw7.tests.test_solver` | Initial 31 tests passed; after independent OBB SAT addition 32 passed. Later focused verification includes additional independent inertia/friction/invalid-bound fixtures. |
| `unittest -v hw7.tests.test_system.RestingAndStackingTests` | Initial seven-fixture run: two failures (horizontal cylinder final speed .064619 m/s, box horizontal drift >5 mm), one EPA inverted-horizon error in cylinder stack. Single box/sphere/upright cylinder and refinement checks passed. Partial follow-up runs were interrupted after further corrections made them obsolete; no pass is claimed for interrupted runs. |
| `hw7.evidence.diagnose cylinder` | Inspected actual horizontal-cylinder point/impulse records. Removing stale/perturbed fake curved patches reduced one-second physical motion to approximately 1e-9 m/s, without freezing or damping. |
| `hw7.evidence.diagnose stack box 60 2400` | Max depth .00078373 m; top horizontal displacement about .00937 m, still outside 5 mm target. This motivated more converged deterministic sweeps. |
| `hw7.falling_objects --headless --steps 480 --json hw7/evidence/corrected_480.json` | At 240 Hz/30 physical sweeps, two seconds completed, all states finite/no escaped COMs, max corrected depth .0336833 m and final .00541641 m. Transient target failed; this is not accepted final evidence. |
| `hw7.verify --suite hw5` | All **72 existing Hw5 tests passed**, no skips/failures/errors, 7.718 s runner time. Actual names/output in evidence/hw5_tests.log and machine-readable count/version in hw5_tests.json. Existing snapshot tests used confined temporary files and Agg. |
| `hw7.verify --suite hw7` (240 Hz development scene) | **41 tests, one failure, zero errors**, 237.341 s runner time. All four 10 s single-body rest tests and both 10 s stacks passed unchanged limits; only the full-scene transient-depth assertion failed: .0408722 m > .03 m. Preserved as development_240hz_tests.log/json before later verification. |
| `hw7.verify --suite focused` | **35 tests passed**, zero skips/failures/errors, .842 s runner time, including the added anisotropic world-inertia, sticking-friction and invalid-bound checks. Output in focused_tests.log/json. |

During the passing 240 Hz rest/stack checks, single-body maximum corrected depth was .00078125 m; three-box stack .000851177 m with final maximum speed .00027927 m/s; three-cylinder stack .000847273 m with final maximum speed .000464083 m/s. All passed 5 mm horizontal drift/height/finite-state assertions. The sphere refinement independently matched `slop+4*g*h^2`: .00078125 m at 240 Hz and .0002703125 m at 480 Hz. Stationary sphere overlap independently matched .01 -> .00802 m and retained zero physical linear/angular velocities. These are correctness observations, not speed benchmarks.

Refined 480 Hz/3 s automated smoke and full default 480 Hz/6 s CLI verification, final snapshot inspection, and final repository audit are recorded below after completion. Formal cProfile/stage/repeated baseline measurements and all parallel comparisons remain pending. Some correctness runs overlapped in wall-clock execution, so their elapsed times must not be used as a performance baseline. No speedup is claimed. Live GUI interaction, broader random-seed/geometry stress sweeps, clean-environment packaging, real commit history updates and the student's personal paragraph remain future work.

### Refined scene and final test verification

`-B -m hw7.verify --suite hw7` completed with **41 passed, zero failures/errors/skips**, runner elapsed **374.199 s**. This run discovered tests before three additional focused fixtures were added. `-B -m hw7.verify --suite focused` then passed all **35 focused tests**, including the three additions and final stationary-energy/angular-cap/invalid-argument assertions (last elapsed .820 s). Together these runs checked **44 distinct HW7 test methods**, not 76 independent tests. Both print specific verbose names and preserve logs/JSON under evidence/. The final invalid-argument tightening rejects a false Options argument and parallel backend even for zero-step calls; normal physical arithmetic did not change.

The accepted 1440-step 480 Hz smoke covered 3 s, all 30 dynamic bodies and five unchanged bin colliders. All states were finite; maximum quaternion norm residual was 3.33e-16. Maximum corrected penetration was **.0162515352 m**, final depth **.00116379546 m**, and maximum during its final two seconds **.00854309918 m**. Worst pair was IDs (0,6) at step 285. Nonzero physical impulse rows included 28,357 body-body and 37,599 body-bin rows; these count solver rows, not unique impacts. No escaped COM IDs or correction-cap body-steps occurred. Final kinetic energy was 1.54393 J and maximum speed 1.15702 m/s: this 3 s smoke includes continuing motion and is not claimed to be fully settled. Its 228.707 s physics-loop elapsed time was collected during concurrent verification and is not a performance baseline.

### Pause checkpoint — student requested implementation stop

Paused implementation and saved detailed state in [PROGRESS.md](PROGRESS.md). Inspected Git status, HEAD, hw7 files and saved test records without reverting changes. HEAD is still 2c4b36c; unrelated root README/Hw5/hw6/lecture-PDF status is unchanged. No features, tests, installs, commits or pushes were started during this checkpoint. Only hw7/PROGRESS.md and this log were written.

The outstanding command was `-B -m hw7.falling_objects --headless --json hw7/evidence/serial_default.json --snapshot hw7/evidence/falling_objects.png` using the installed Python 3.12.10 interpreter. Neither requested final file was present when paused. Sent Ctrl+C to its specific exec session 36307; the session closed with exit code 1 and no final summary. Its last completed step is unknown, and no completed six-second/snapshot result is claimed. No additional Python process was listed by the checkpoint's process inventory. The saved-default audit has not run, and no HW7 snapshot or live GUI has been verified.

Passing evidence remains: 41-test full refined-scene run, 35-test focused run (44 distinct HW7 methods across their overlapping names), and 72 Hw5 regressions; actual commands/counts/results and earlier failed or interrupted development runs are recorded in PROGRESS/evidence. Formal profiling and parallel comparisons remain pending. Resume by rerunning the interrupted default from its initial state, then run the independent saved-state audit and inspect the PNG before accepting Part 2. Personal reflection below remains empty.

### Resumed from checkpoint

At the student's request, read PROGRESS.md, SPEC.md and this log, rechecked applicable AGENTS.md locations (none found), Git status and HEAD, and inspected current source/CLI/rendering/audit code. HEAD/status are unchanged from the checkpoint. Preserved previous code, failed development records and passing test evidence; did not rerun completed suites. Restarted the previously interrupted `-B -m hw7.falling_objects --headless --json hw7/evidence/serial_default.json --snapshot hw7/evidence/falling_objects.png` from its initial state using the same installed interpreter and numerical settings. Results will be recorded after actual completion, followed by the independent saved-state audit and PNG inspection. No physics edits, installations, commits or parallelization were made during this restart.

### Completed resumed Part 2 acceptance

The restarted command completed with exit code 0:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw7.falling_objects --headless --json hw7/evidence/serial_default.json --snapshot hw7/evidence/falling_objects.png
```

All 2880 steps completed, elapsed simulated time 5.99999999999982 s. The result contains ten prisms, ten spheres, ten cylinders and five static bin solids; every state is finite and maximum final quaternion norm residual is 2.220446049250313e-16. Maximum corrected penetration is .016251535173982926 m (pair 0,6 at step 285), maximum over the final two seconds .0012887548119564218 m, and final .0011646418555887605 m. The .03 m transient/.01 m final-window limits pass unchanged. There are 58,754 body-body and 117,759 body-bin nonzero physical impulse rows (not unique impacts), zero correction-cap body-steps and no escaped COM IDs. Final kinetic energy is .49507033512501347 J and maximum linear speed .3882520607141568 m/s: motion remains, without freezing or deleting bodies. No claim of a motionless pile is made.

Physics-loop elapsed time was 1151.3943471999955 s (about 19 min 11 s), including stepping, contact/corrected-pose diagnostics, report retention and optional 30 Hz frame sampling, excluding imports/scene setup/rendering/JSON I/O. The final snapshot render reported .8160686999908648 s. These single correctness observations expose a substantial runtime limitation; they are not formal profiling, a controlled repeated baseline, or a parallel comparison. No cProfile or parallelization was performed.

An additional independent visual check used `-B -m hw7.falling_objects --headless --steps 0 --snapshot hw7/evidence/initial_scene.png` and exited zero. It advances no physics and is not contact/settling evidence. Viewed both actual 1280x720 PNGs: varied orange prisms, blue spheres, purple finite cylinders, orientation markers, translucent bin floor/walls and world-y-up labels are recognizable; the final scene is in the bin. No live GUI window/playback was tested.

Before executing the existing saved-state audit, strengthened its record checks to require 35 actual records, IDs 0..34 and 30 dynamic bodies, and added the missing upper-rim bound to the independent analytic-extent containment calculation. This changes only acceptance checking, not production physics or numerical settings. The following command exited zero and wrote evidence/default_audit.json with accepted=true and no full-geometry outside IDs:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw7.evidence.audit_default
```

The audit checks dynamic clocks/finite states, unchanged static records, counts/IDs, the unchanged penetration limits and full analytic geometry in x/z +/-2.01 m, bottom y>=-.01 m and top y<=2.41 m. Saved serial_default.json includes actual options and realized initial/final states. Completed test suites were not repeated: their existing passing 44 distinct HW7 method and 72 Hw5 regression records remain the test evidence. Updated SPEC, README, TEST_PLAN, PROFILE, implementation_plan and PROGRESS with actual acceptance/visual results and limitations. Broader geometry/seed stress coverage, live GUI verification, formal profiling, parallel comparisons, clean-environment packaging and authorized real commits remain future work. No production physics, Hw5 or unrelated files were edited during the resumed acceptance work; no dependencies were installed and no commit/push was made.

## Part 3 — measured serial profiling and recommendation, 2026-11-04

Read applicable instruction locations (no AGENTS.md found), git status, PROGRESS/SPEC/README/PROFILE/this log/implementation_plan and actual collision/manifold/solver/world/example APIs. Preserved the root README modification, untracked Hw5/hw6/lecture PDF and hw7.zip; HEAD remains 2c4b36c. No Hw5 edits, dependency installation, commits, push or parallel physics implementation. All retained new evidence is under evidence/profile_serial/; no historical Part 2 evidence was overwritten. The only production solver edit adds optional phase-boundary observer callbacks, without changing arithmetic, iterations or ordering.

Added profiling.py (hardware/source/config metadata, genuine full-cache checkpoints, incremental completion records, plain/stage/cProfile measurement, validation) and profile_analysis.py (aggregation/bounds, echo-worker IPC probe and serial island decomposition). Added four standard-library instrumentation tests. `-B -m unittest -v hw7.tests.test_profiling hw7.tests.test_solver` passed all 18 tests in .179 s in the latest run; it was also run after initial instrumentation. Specific verbose names were printed. Completed Part 2 long suites were not rerun. Short tests check collision-result equality, wrapper restoration after failure, shared-static island handling and return code 2/saved statistics on budget exhaustion.

All commands used `C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe`, CPython 3.12.10, from the root, with -B. Exact argv, versions, numerical Options and source SHA maps are saved in each metadata.json. Hardware inventory independently reported Intel Core Ultra 9 275HX, 24 physical and 24 logical cores, affinity 0..23, plugged-in battery 100% and active localized performance scheme; native thread environment variables were unset. Thermal/background-load history and actual native pool sizes were not measured. NumPy 2.3.5, SciPy 1.17.1, Matplotlib 3.10.8 and psutil 7.2.2 were present; Cython/Numba/threadpoolctl were absent. Localized power-plan decoding was initially wrong; UTF-8 decoding and inventory_confined corrected it.

Executed command groups (all module commands prefixed by the interpreter and -B; exact full argv remains in metadata):

| Command/work | Actual result |
| --- | --- |
| `-m hw7.profiling inventory --label inventory_confined` | Complete hardware/version/affinity/power observation, saved inventory.json. |
| `measure --label pilot_plain --steps 30 --mode plain --repeats 3 --warmup-steps 4`, plus pilot_profile combined | Pilot median .0984998 s; combined .3878358 s. These early runs used native default temp location. |
| `prepare --label states_0600 --targets 0,240,600 --mode stages --journal-every 60` | Completed 0..600, 82.631286 s stepping, genuine world/cache checkpoints. |
| `prepare --label states_1440 --checkpoint ...states_0600/checkpoints/step_000600.pickle --targets 960,1200,1440 --mode stages --journal-every 120` | Externally interrupted with Ctrl+C/nonzero exit; last saved state 960 and persisted span 94.4553415 s. Updated that new record to interrupted_external/complete=false. Unknown work after last journal is not claimed. |
| `prepare --label states_1440_confined --checkpoint ...states_1440/checkpoints/step_000960.pickle --targets 1200,1440 --mode stages --journal-every 120` | Completed to 1440, 191.1003827 s stepping; full-cache lineage preserved. |
| `validate --label validate_collision --checkpoint ...states_0600/checkpoints/step_000240.pickle --steps 60` | Passed: collision present, exact worlds/reports, plain 1.9841561 s versus combined 4.2187327 s. |
| `measure --label free_plain/impacts_plain/pile_plain/peak_plain --steps 30 --mode plain --repeats 3 --warmup-steps 4` (separate commands, appropriate checkpoints) | All complete. Medians .0888735 / 4.6967277 / 15.9091579 / 14.3094633 s. All raw samples and sample dispersion in PROFILE/measurements.json. |
| Corresponding labels ending `_stages` and `_cprofile`, modes stages/cprofile, one repetition | All complete; cProfile walls .3775604 / 11.1498027 / 25.9803729 / 21.0784433 s. Separate pile_granular stage repeat completed in 15.9725982 s to measure pair imbalance. |
| `measure --label full_profile_budgeted --steps 2880 --mode cprofile --max-seconds 45 --journal-every 30` | Partial budget stop, 389/2880 steps, 45.342076 s; saved stats and full-cache checkpoint. Module returns 2; outer PowerShell wrapper reported nonzero 1. No full-run median/result claimed. |
| `-m hw7.profile_analysis ipc --sample ...states_1440_confined/checkpoints/step_001440.pickle --label ipc_world --repeats 10` | Complete echo-only worker probe, no physics: startup .3578538 s; 25,832-byte payload, median round trip .4283 ms. |
| `-m hw7.profile_analysis islands --sample ...pile_stages/run_00_solver_input.pickle --label pile_islands --repeats 3` | Complete serial decomposition, exact physical/pseudo velocities and impulse reports; eight islands, largest 65.45% of island-solve time. No parallel solver. |
| `-m hw7.profile_analysis summarize` | Saved summary, exact cross-mode digest agreement for all four intervals, and explicitly estimated interval speedup bounds. |

The table abbreviates repeated labels and checkpoint prefixes only for readability; each raw metadata records the executable and every exact argument. Early cProfile exposed SciPy/Qhull MessageStream tempfile.mkstemp/nt.open costs. Initial pilot/preparation inadvertently used the system native temp location. Stopped preparation and added confinement of tempfile.tempdir and process TMP/TEMP to evidence/profile_serial/native_tmp before retained interval baselines; no outside cleanup was attempted. A hard process termination can bypass finalization, so the last journal/checkpoint is the only claimed progress. Aggregation was corrected to sum available step counters for such partial journals. All subsequent commands completed or explicitly reported their budget stop; no command is currently running.

Exclusive collision-heavy stage shares: kernel 83.52–90.76%, manifold/cache excluding kernel 1.92–2.40%, physical impulses 5.27–10.30%, split .37–.59%. Nested cProfile cumulative times are not summed. EPA repeatedly constructs Qhull error streams; observed tempfile calls are significant, but antivirus/filesystem/thermal causality is unknown. Consulted primary Python profiling/threading/multiprocessing docs, SciPy 1.17.1 Qhull/MessageStream source and Cython native parallelism docs; URLs and sourced-versus-design distinctions are in PROFILE.

Recommend persistent spawned workers for batched unchanged narrow-phase/manifold queries at both detection barriers, deterministic parent gathering, existing serial impulses, initially testing 2/4/8 workers. Native GIL-releasing batch kernel is fallback; compilation improvement must be separated from subsequent parallel improvement. Measured pair workloads and IPC support batching, while imbalance/file contention/serialization/barriers remain risks. Optimistic source-based per-interval bounds with measured task imbalance are about 3x at four workers and 3.7–4.3x at eight, before overhead. These are estimates, not speedup measurements or a measured full-scene bound. Full 2880-step profiling, three-run unprofiled full baseline, rendering benchmarks and every parallel comparison remain pending. Updated PROFILE/README/SPEC/PROGRESS/implementation_plan with actual interfaces/results and a practical three-full-run future protocol. The student's section below remains empty.

## Part 4 — deterministic spawned collision backend, 2026-11-05

Read ancestor/root/recursive instruction locations (no AGENTS.md found), Git
status, PROGRESS/SPEC/PROFILE/README/implementation plan/this log and current
world/collision/manifold/solver/profiling/example/test code. HEAD remains 2c4b36c;
root README, Hw5, hw6, lecture PDF and both existing ZIPs were preserved. All
changes/generated evidence are under hw7; no installs, commits, pushes or nested
repository. No agents were delegated. Student reflection remains empty.

Specified the worker/lifecycle/cache protocol in SPEC before implementing.
Added parallel.py: persistent multiprocessing spawn children with importable
top-level workers, one pipe per worker, dynamic consecutive-pair batches and
canonical result gathering. Workers receive immutable exact bodies/options/
previous pair manifolds and original enrich flags. Both detection barriers run
through the backend; all kick/impulse/pose/cache updates remain ordered in the
parent. Pool reuse spans warmup and every step; success, error, startup failure,
unexpected worker exit and parent interruption clean up owned children. No
silent serial fallback. Default threshold zero; counters/PID work totals expose
real dispatch. Workers request one OMP/OpenBLAS/MKL/NumExpr thread and confined
per-worker native temporary folders. Benchmarks apply identical requested limits
in the fresh serial parent before native imports; actual native thread counts
are not independently asserted.

Connected detector interfaces to world.py and backend/worker/batch/threshold
controls to falling_objects.py. Original collision/manifold/solver/model/scene/
Hw5 files are byte-for-byte unchanged. A new optional RunResult metadata field
reports lifecycle statistics outside physical World/StepReport equality. Updated
one existing invalid-backend test literal to `invalid` because parallel is now
supported for simulate; all physical expectations/tolerances are unchanged.

Added parallel_checks.py, tests/test_parallel.py and parallel_pilot.py. The new
measurement tool exposes serial/parallel, workers/batch/threshold, preserves
incremental failed/completed records, records source/runtime/options/native
environment and separates stepping/startup/warmup/shutdown/cold costs. Existing
serial profiler remains available; source checks are still strict by default.
Versioned explicit compatibility_v3.json maps the old source ID to exact current
hashes, whitelisting dispatch-only world/CLI changes among original physical
files. It rejects subsequent source drift. Payload hash/options/seed/cache/step
provenance is still checked; old checkpoints were never rewritten.

All Python commands used `C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe`
with `-B` from the repository root. Sandbox interpreter access failed; approved
outside-sandbox execution was used. Exact argv and sources are in saved metadata.

| Actual command (after interpreter and -B -m) | Result / evidence under evidence/parallel_pilot/ |
| --- | --- |
| `hw7.parallel_checks tests_v1` | 46 passed, 4.756 s; tests_v1.log/.json |
| `hw7.parallel_pilot approve` | Explicit initial compatibility approval, preserved compatibility.json |
| `hw7.parallel_pilot validate --label validation_v1` | Failed before stepping: newly added manifest comparison treated JSON gravity list as unequal to Options tuple. Preserved failure/record/cold files. |
| `hw7.parallel_checks tests_v2` | 48 tests, one error: unexpected child exit raised BrokenPipeError rather than WorkerError. Cleanup occurred; preserved log. |
| `hw7.parallel_checks tests_v3` | 48 passed, zero failures/errors/skips, 5.3200469 s; tests_v3.log/.json |
| `hw7.parallel_pilot approve` after each audited fix | Preserved compatibility_v2.json then final compatibility_v3.json; no approval overwritten |
| `hw7.parallel_pilot validate --label validation_v3` | Complete: genuine 389/600/1440 starts, historical serial digest replay plus direct exact World/cache/report agreement with four workers over 30 steps each |
| `hw7.parallel_pilot screen --label screen_v1 --reference-label validation_v3` | Complete: serial and 2/4/8 workers, batches 4/8; 21 sequential 30-step trials, all exact |
| `run_repeats.ps1` (saved exact Python module argv per trial) | Complete: 27 new trials, serial/4/8 workers, batch 4, three per interval/config, alternating order; each exact and every pool joined |
| `hw7.falling_objects --headless --steps 0 --backend parallel --workers 2 --batch-size 3 --json hw7/evidence/parallel_pilot/cli_zero.json` | CLI/lifecycle smoke passed; no physics or speed claim |

Fixed validation-only tuple/list representation by comparing normalized JSON
options. Fixed production transport error propagation by normalizing broken
pipe/EOF to WorkerError after owned-worker cleanup, without fallback. No observed
numerical difference required tolerance changes. Tests cover all six shape pairs,
cached/enrich flags, spinning nonspherical contacts, both barriers, several
counts/batches, reversed result consumption with distinguishable manifolds,
reuse, invalid inputs, failure/interruption/startup/dead-child cleanup and exactly
zero physical energy in stationary split correction.

Historical serial replay used the original pickle-based world/report digests.
Cross-process comparisons also use canonical exact dataclass value hashes so
pickle alias graphs cannot create a false mismatch. Direct Python equality of
full Worlds/caches/reports was explicitly checked in validation_v3. Every screen
and repeat value digest matches its serial validation reference.

Single-screen times and all repeated raw samples/SD/ratios are in PROFILE.md,
comparison.json and REPORT.md. Fresh serial medians for 389..419 / 600..630 /
1440..1470 were 12.6433017 / 5.7040663 / 14.8250897 s. Four-worker/batch-4
medians 4.5984833 / 2.7306732 / 5.0691963 s: 2.749x / 2.089x / 2.925x.
Eight-worker/batch-4 medians 3.6541155 / 2.6700993 / 4.1894319 s: 3.460x /
2.136x / 3.539x. These are measured SHORT-INTERVAL gains, never whole-scene gains.
Eight-worker/batch-8 screens were slower than batch four and remain preserved.
Four workers slightly beat eight on cold total invocation for continuing impacts,
despite slower stepping. Recommend eight/batch four as the preliminary full-scene
candidate, four/batch four as a lower-overhead alternative; no compiled rewrite.

Real worker pair calls per measured interval were 1650 / 2121 / 3420 with 30 trial
and 30 diagnostic barriers. Every PID's actual work and completion order is saved.
Dense intervals use seven of eight configured workers; other intervals use all
eight. Four-worker startup .3137–.3239 s, shutdown .0374–.0533 s; eight-worker
startup .3613–.3791 s, shutdown .0535–.0651 s. Cold invocation raw timings also
include imports/loading, discarded warmup, hashing/output and teardown. No
1151-second acceptance runtime, cProfile time, IPC echo or estimated bound was
used as a comparison baseline. Native filesystem contention/thermal causes were
not isolated, and full-scene phase weighting remains unknown.

Operational/evidence details: an initial shell-profile-blocked preparation command
was stopped; subsequent commands used -NoProfile. The saved repeat script was
initially blocked by PowerShell execution policy, then ran with an explicitly
approved process-only exception; machine policy was not changed. The report's
first audit incorrectly required every configured worker to receive jobs even
when a phase had fewer batches; corrected to require actual work, all readiness
handshakes, exact pair totals and complete cleanup, and report active-worker
counts. This was a reporting assertion, not a numerical or scheduling failure.
The first short regression created a new budget-test artifact under profile_serial;
it was moved unchanged into parallel_pilot/profiling_tests with relocation.json.
Later regression artifacts go directly there. No pre-Part-4 raw file was modified
or moved. Intentional 1/10-step budget-test records remain explicitly incomplete.

Updated SPEC/README/PROFILE/TEST_PLAN/PROGRESS/implementation_plan and this log.
Final read-only process inventory found no Python process. All Part 4 validation/
screen/repeat commands are finished; failed attempts and old interrupted/budgeted
profiles remain labeled failures/incomplete. No long serial acceptance, full
cProfile or full-scene benchmark series was rerun. Prepared final_matched.ps1
contains sequential alternating 2880-step runs with external cold timers and
exact reference comparison; it was NOT launched. Whole-example acceleration,
broader stress/live GUI/rendering checks, real Git history, the student's own
reflection and final clean-environment packaging remain pending.

## Part 5 — preflight and full-scene schedule started, 2026-11-05

Read applicable root/ancestor/recursive instruction locations (none found), Git
status, PROGRESS/PROFILE/SPEC/README, parallel_pilot.py and final_matched.ps1.
Inspected World/Options/scene, worker lifecycle, summary/digest/reference logic
and the independent Part 2 saved-state audit. HEAD is still 2c4b36c; unrelated
root README/Hw5/hw6/lecture PDF and the existing hw7 (3).zip were preserved.
Part 4 production/Hw5 hashes still exactly match compatibility_v3.json. No
existing complete full-scene labels were found. No commit/push/package/install.

The prepared script has the right sequential alternating schedule, identical
30-step collision warmup/reset and eight-worker/batch-four settings, but its
runner saves only hashes and has no incremental full-run journal. Added an
audited equivalent ONLY under evidence/full_scene/: runner.py, audit.py,
schedule.py, checks.py and summarize.py. Production physics, Part 4 tools and
the prepared script remain unchanged. Cohort.json pins their source hashes plus
every new harness hash/configuration before any timed trial. Documentation and
temporary ignore rules are the only other changes at this starting checkpoint.

`python -B -m hw7.evidence.full_scene.checks` passed four harness checks, zero
failures/errors, .017 s: old acceptance still passes, original limits and
containment/static/nonfinite violations are rejected, and the new serial loop
and canonical digest exactly match the existing implementation. No tolerance
was relaxed and no production bug fix was needed. Saved harness_checks.log/.json.

`python -B -m hw7.evidence.full_scene.runner preflight` passed. Installed
interpreter C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe,
CPython 3.12.10; imported NumPy 2.3.5, SciPy 1.17.1, Matplotlib 3.10.8; CPU
affinity 0..23, 24 physical/logical cores reported by psutil, AC power/100%.
Requested OMP/OpenBLAS/MKL/NumExpr threads are one before native imports in both
parents and children. Actual native pool sizes/thermal/background load are not
independently measured. Genuine cached step-600 warmup passed strict payload,
source-mapping/options/seed/cache checks. Realized initial state and Options
exactly match the accepted seed-7 scene. No other Python process was listed.

Started `python -B -m hw7.evidence.full_scene.schedule` using the installed
interpreter with -B and approved outside-sandbox access. It runs serial_r0,
parallel_r0, parallel_r1, serial_r1, serial_r2, parallel_r2 sequentially. Every
trial starts at step/time zero with 30 dynamic/five static bodies and empty
cache; h=1/480, 2880 steps, 120/20 sweeps, identical Options, both collision
barriers and all StepReports. Parallel pool is persistent across 30 discarded
warmup steps and the entire measured simulation, eight workers/batch four/
threshold zero. No frames, snapshots, GUI, changed geometry or sleeping.

The timing span is one continuous unprofiled wall interval. Identical progress
JSON/console writes every 120 steps are included in both stepping timers and
their I/O cost is also recorded separately, without subtraction. Readiness,
warmup, shutdown and final state/report hashes/export/audits are separate. The
outer cold timer covers process/imports through completed output and teardown.
Realized initial/final JSON and trusted replay.pickle retain the actual final
World/cache and every report for acceptance replay outside stepping time.

Schedule/journal files record incremental progress with complete=false until
physical acceptance and the exact reference digest pass. A mismatch stops the
remaining schedule. A compatible complete trial is never rerun; partial trials
restart from zero under a new attempt label, never splicing timing segments.
The healthy first serial trial is continuing; no full-scene success/speedup is
claimed in this starting record. Final results will be appended after actual
completion. The student reflection remains empty.

## Part 5 — completed full-scene verification and benchmarking, 2026-11-05

The sequential schedule finished with exit code 0. All six trials completed
2880 uninterrupted steps and passed physical acceptance plus the exact canonical
World/cache/all-report reference gate. No failed/partial trial, timeout, healthy
termination, restart or competing benchmark. Actual order and raw wall seconds:

| Label | Stepping | Cold invocation |
| --- | --- | --- |
| full_serial_r0 | 1047.9100364 | 1056.8112320 |
| full_parallel_r0 | 381.9162382 | 388.4043114 |
| full_parallel_r1 | 376.7153257 | 383.2620153 |
| full_serial_r1 | 1066.6222320 | 1075.2671255 |
| full_serial_r2 | 1066.8177625 | 1075.8132584 |
| full_parallel_r2 | 377.2070056 | 383.9497146 |

`python -B -m hw7.evidence.full_scene.summarize` then exited zero after replaying
all six retained pickle checksums, canonical digests and acceptance audits. It
wrote comparison.json and REPORT.md. Serial median 1066.6222320 s (sample SD
10.8603760, min/max 1047.9100364/1066.8177625); parallel median 377.2070056 s
(sample SD 2.8713560, min/max 376.7153257/381.9162382). Ratio of medians
**2.827684047x**, configured-worker efficiency .353460506. Cold medians
1075.2671255/383.9497146 s, ratio 2.800541541x; cold sample SD
10.8166174/2.7916415 s. All samples retained; gain far exceeds observed noise.
Earlier short ratios, estimates, echo/profiler times and historical 1151-second
frame-sampled acceptance were not used as this baseline.

Common complete canonical digest:
d8200d8e082505b79ba235cc1aca6a1d11f9757d02ad4ecd6c47e7ff166d5965.
Each run starts with the same 30 dynamic/5 static seed-7 bodies and empty cache,
uses h=1/480, 2880 steps, 120/20 sweeps and every unchanged Option/barrier/report,
without frames, rendering, snapshots, sleeping or geometry changes. Thirty real
step-600 warmup steps are discarded before a full initial-world/cache reset.
Eight workers/batch four/threshold zero persist through warmup and the full
parallel trial. Native thread requests are one equally; recorded affinity 0..23
for every trial. No production/Hw5/Part 4 source change was required.

Stepping includes all dispatch/IPC/gather/synchronization and identical journal
work in one continuous timer. Included journal I/O .0419800–.0617979 s per full
trial was not subtracted. Raw parallel readiness/startup .3791065/.3750637/
.3941092 s; warmup 2.6313856/2.5970350/2.6911439 s; shutdown .0599697/.0592954/
.0622029 s. Serial warmup 5.1133625/5.4384231/5.2153901 s. Post-run export,
hashes and audit 2.7295–3.2556 s were outside stepping and inside the cold child
timer. Later independent replay checks are outside all original trial timers.

Each parallel trial recorded 268543 actual worker pair queries in 69314 batches,
2880 trial plus 2880 diagnostic calls. All eight PIDs performed physics; the
nonempty serial-pair count is zero, with 462 empty barriers local. Per-PID work
and completion orders are saved. Every pool joined; final read-only process
inventory listed no Python process. No cold-start cost is hidden in a speedup.

All six physical results are identical: 2880 steps and time 5.99999999999982 s;
finite final positions/velocities/angular velocities/quaternions; max quaternion
norm residual 2.220446049250313e-16; all five static records unchanged. Actual
nonzero impulse rows: 58754 body-body, 117759 body-bin, not unique impacts.
Maximum corrected penetration .016251535173982926 m, final
.0011646418555887605 m, last-two-second maximum .0012887548119564218 m pass
the ORIGINAL .03/.01 m limits. Independent analytic extents pass x/z +/-2.01,
bottom -.01, top 2.41 m; no outside IDs. Residual speed .3882520607141568 m/s,
kinetic energy .49507033512501347 J: this is not a motionless-pile claim.
Read-only all-six realized initial/final/cache/option comparisons also match the
old accepted serial state; historical_state_agreement.json saves those checks.

Evidence under hw7/evidence/full_scene/: cohort.json; schedule.json; comparison.json;
REPORT.md; harness_checks.log/.json; historical_state_agreement.json; logs/; and
full_serial_r0..2/full_parallel_r0..2 directories, each with exact metadata/argv,
source/harness hashes, numerical/runtime/affinity settings, final record and
cold timer, realized.json, acceptance.json, full replay.pickle, replayed acceptance
and incremental journal. Complete records plus successful wrapper exits and
replay audits certify completion; earlier incomplete journal snapshots do not
mean a process remains running. Existing partial/budgeted Part 2/3 artifacts
remain historical and unused.

Two post-run PowerShell display/save attempts had a numeric-format and an
unsupported Set-Content parameter error; corrected inspections succeeded and
all benchmark/raw records were unaffected. A documentation patch context miss
was corrected before final verification. None was a physics/benchmark failure.
No full cProfile, extra rendering, dependency install, commit, push or package
was performed. Updated PROFILE (full results first), README (portable commands
and precomputed-playback explanation), PROGRESS, implementation_plan and status
pointers in SPEC/TEST_PLAN. Broader seeds, live GUI and thermal/background/native
pool-size control remain limitations. The whole-example speedup/correctness gate
is now met; student reflection, separately authorized real Git history and final
clean-environment packaging remain required. The personal section stays empty.

## Personal reflection — to be written by the student.
My computer has 24 physical cores and 24 logical processors. Profiling showed that narrow-phase collision detection took most of the runtime, so a persistent process pool made sense for distributing those calculations across cores. Using eight processes with batches of four reduced the full example’s runtime from about 1,067 seconds to 377 seconds, a 2.83× speedup. The part I found most challenging was getting the different shapes to collide and stack reliably, especially when rotated cylinders produced unstable contacts. Looking back, working with the agent was most useful when I broke the task into smaller steps and checked the results before moving on. Profiling also helped me focus on the actual bottleneck instead of assuming that using more cores would automatically make everything faster.
