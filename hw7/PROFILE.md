# HW7 profiling and measured parallel collision intervals

## Part 5 — complete-example matched results, 2026-11-05

**Whole-example acceleration is demonstrated for this fixed seed-7 scene on this
computer: median unprofiled stepping speedup 2.827684x**, with exact complete
World/contact-cache/StepReport agreement and unchanged physical acceptance limits
passing on all six runs. Eight spawned workers, batch four, serial threshold zero.
This closes the full-scene performance gate; HW7 submission remains unfinished
until the student's reflection, real Git history and verified packaging are done.

### All six complete trials

Actual sequential order is shown; none failed, interrupted, resumed in pieces or
discarded. Every trial completed 2880 steps/6 simulated seconds.

| Trial | Backend | Raw stepping seconds | Cold invocation seconds |
| --- | --- | --- | --- |
| full_serial_r0 | serial | 1047.9100364 | 1056.8112320 |
| full_parallel_r0 | 8 workers / batch 4 | 381.9162382 | 388.4043114 |
| full_parallel_r1 | 8 workers / batch 4 | 376.7153257 | 383.2620153 |
| full_serial_r1 | serial | 1066.6222320 | 1075.2671255 |
| full_serial_r2 | serial | 1066.8177625 | 1075.8132584 |
| full_parallel_r2 | 8 workers / batch 4 | 377.2070056 | 383.9497146 |

| Stepping statistic (s) | Serial | Parallel |
| --- | --- | --- |
| Median | 1066.6222320 | 377.2070056 |
| Min..max | 1047.9100364..1066.8177625 | 376.7153257..381.9162382 |
| Sample standard deviation (n=3) | 10.8603760 | 2.8713560 |
| Cold invocation median | 1075.2671255 | 383.9497146 |
| Cold invocation sample SD | 10.8166174 | 2.7916415 |

S = 1066.6222320 / 377.2070056 = **2.827684047x**; configured-worker efficiency
S/8 = .353460506. Cold median speedup = **2.800541541x**. The largest parallel
sample is far below the smallest serial sample; this improvement exceeds the
observed repeat variability. No interval ratio, profiler time, IPC echo, estimated
bound or historical 1151-second frame-sampled observation enters this calculation.

### Exact correctness and physical acceptance

Every complete canonical digest, including final World/cache and ALL 2880 reports:
`d8200d8e082505b79ba235cc1aca6a1d11f9757d02ad4ecd6c47e7ff166d5965`.
All six trusted saved replay files passed checksum, digest and acceptance replay.
Realized initial/final states and Options also match the old accepted serial
state exactly (its runtime remains excluded from the benchmark).

- Exactly 30 dynamic bodies (ten per shape), five unchanged static bin records,
  IDs 0..34, initially empty cache, all clocks synchronized; final time
  5.99999999999982 s and 2880 steps.
- All final positions/velocities/angular velocities/quaternions finite;
  maximum quaternion norm error 2.220446049250313e-16.
- Actual nonzero body-body impulse rows 58,754; body-bin rows 117,759. These
  count rows, not unique impacts.
- Maximum corrected penetration .016251535173982926 m, final
  .0011646418555887605 m, final-two-second maximum .0012887548119564218 m.
  Original .03 m transient/.01 m final-window limits pass unchanged.
- Independent analytic extents put every final body within x/z +/-2.01 m,
  bottom y>=-.01 m, top y<=2.41 m; no outside IDs. All five bin bodies unchanged.
- Residual motion remains: maximum linear speed .3882520607141568 m/s and
  kinetic energy .49507033512501347 J. No complete-rest claim.

### Matched scope and separately measured overhead

Each fresh trial used seed 7, dt=1/480, 120 physical/20 split sweeps and identical
Options, true geometry, both detection barriers and retained reports. No frames,
snapshots, GUI, sleeping or production change. Thirty real collision steps from
the genuine step-600 checkpoint were discarded, then the entire world/cache
reset to the identical seed-7 step-zero state. One parallel pool persisted across
warmup and every measured timestep. Serial and parallel requested native limits
OMP/OpenBLAS/MKL/NumExpr=1 before native imports; recorded affinity was 0..23
at preflight and each trial's runtime snapshot.
CPython 3.12.10, NumPy 2.3.5, SciPy 1.17.1, Matplotlib 3.10.8; AC power.

Stepping is ONE continuous unprofiled perf_counter wall span, including dispatch,
IPC, gathering, synchronization, both collision barriers and ordered serial
impulses/cache updates. Identical 120-step progress writes are included in both
timers: measured journal I/O was only .04198–.06180 s per full run and was not
subtracted. Loading/setup/readiness, discarded warmup, final hashes/JSON/pickle
export/acceptance and shutdown are outside stepping. This new scope is explicitly
matched and distinct from the historical output-free interval timings.

| Parallel trial | Pool spawn/import/readiness (s) | Discarded warmup (s) | Shutdown (s) |
| --- | --- | --- | --- |
| r0 | .3791065 | 2.6313856 | .0599697 |
| r1 | .3750637 | 2.5970350 | .0592954 |
| r2 | .3941092 | 2.6911439 | .0622029 |

Serial discarded warmups: 5.1133625, 5.4384231, 5.2153901 s; no worker startup or
shutdown. Post-run state/report export, hashes and acceptance took 2.7295–3.2556 s
per trial. Cold timers surround the whole child invocation: process/imports,
setup, readiness, warmup, stepping, teardown and final output/audit; they exclude
the wrapper's own JSON write and the later independent replay checks.

Every parallel trial performed **268,543 real worker pair queries in 69,314
batches**, 2880 trial plus 2880 diagnostic barriers, with all eight PIDs doing
physics. All nonempty candidates went to workers (serial_pairs=0); 462 empty
barriers stayed local. PID-level work distributions/completion orders and pool
readiness/exit status are retained. Every pool joined; final process inventory
found no Python process running.

### Evidence, commands and limits

[comparison.json](evidence/full_scene/comparison.json) contains full-precision
samples/statistics, overhead, identity, dispatch and physical results;
[REPORT.md](evidence/full_scene/REPORT.md) is the short table. Each of
`evidence/full_scene/full_serial_r0..2/` and `full_parallel_r0..2/` contains
metadata.json, record.json, journal.json, cold_invocation.json, realized.json,
acceptance.json, replay.pickle and replayed_acceptance.json. Exact argv, production
and harness hashes, runtime/affinity/options/completion status are recorded.
cohort.json records preflight/checkpoint compatibility; schedule.json and logs/
retain the actual sequence; historical_state_agreement.json records all-six
agreement with the historical accepted states. Journals are earlier incomplete
snapshots; final records plus wrapper exit=0 and replay audits certify completion.

The audited evidence-only runner was necessary because the prepared Part 4 tool
saved only hashes. It leaves production/Hw5/Part 4 tools and the old script
unchanged. Four short harness checks passed before timing. Its exact root commands:

```powershell
python -B -m hw7.evidence.full_scene.runner preflight
python -B -m hw7.evidence.full_scene.schedule
python -B -m hw7.evidence.full_scene.summarize
python -B -m hw7.evidence.full_scene.runner replay --label full_parallel_r0
```

The schedule skips complete compatible trials; it does not rerun them. Never run
the old full script alongside it. No partial attempts exist in this cohort. No
full cProfile/rendering benchmark, installation, commit, push or package occurred.
This is one fixed scene/seed/machine: broader seeds and long-term behavior, live
GUI interaction and independent thermal/background-load/native-thread-count
control remain limitations. No further performance adjustment is needed for this
demonstrated gain; eight workers/batch four is the verified whole-scene setting.

## Historical Part 4 results — 2026-11-05

Persistent spawned pair-query workers are implemented in parallel.py and connected
to both world.py detection barriers and falling_objects.py. Real workers call
unchanged narrow_phase; the parent retains ordered impulses/cache updates. Default
threshold=0 dispatches every nonempty candidate set. Exact short-run correctness
passed; **whole-example acceleration has not yet been demonstrated**. No full
2880-step timing series, long acceptance rerun or complete cProfile was launched.

Evidence: [comparison.json](evidence/parallel_pilot/comparison.json),
[REPORT.md](evidence/parallel_pilot/REPORT.md), tests_v1/v2/v3 logs/JSON,
validation_v1/validation_v3, screen_v1, and all repeat_* directories under
evidence/parallel_pilot/. No previous raw records were overwritten.

### Method and correctness gate

`python -B -m hw7.parallel_checks tests_v3` passed 48 tests, zero failures/errors/
skips, 5.3200469 s. Genuine cached step-389/600/1440 worlds passed content/options/
seed/cache checks with the explicit compatibility_v3.json source mapping. All
original arithmetic/model/collision/manifold/solver/scene/Hw5 hashes are unchanged;
world/CLI dispatch interfaces changed. The manifest pins every current top-level
source hash and refuses later mismatches. Historical serial world/report pickle
digests reproduced exactly, then direct Python World/cache/report equality passed
against four spawned workers on all three 30-step intervals. All screen/repeat
canonical dataclass value digests equal the validated serial reference; no
tolerance or model/iteration/diagnostic change was introduced. Canonical hashes
avoid mistaking pickle object-sharing differences for numerical differences.

Each run uses seed 7, 30 dynamic/five static bodies, h=1/480, 120 physical/20 split
sweeps, identical Options, both collision barriers and retained StepReports, with
no frames, GUI or rendering. Time is unprofiled perf_counter wall time around the
entire stepping/report loop, including dispatch, IPC, scheduling, canonical gather
and synchronization. Setup/loading, warmup, final hashing/output and shutdown
are outside this timer and recorded separately. Four discarded steps warm the
same genuine starting state; measured trials reset the complete immutable world/
cache. A fresh pool is reused through warmup and all measured timesteps.

The screen tried 2/4/8 workers with batch sizes 4/8 once per interval. Batches of
four offered more schedulable chunks; batches of eight consistently lost to four
at 4/8 workers. All results remain in screen_v1/results.json. Serial and both
promising batch-4 settings then received THREE new trials per interval; order was
serial/4/8, 8/4/serial, serial/4/8. run_repeats.ps1 records the exact sequential
commands and caller cold totals. No competing configurations ran concurrently.

### Matched interval measurements (seconds)

Every row spans ONLY 30 steps, .0625 simulated seconds. Speedup is the ratio of
the fresh serial median to the parallel median, not the old Part 3 observations.

| Interval | Workers/batch | Raw unprofiled times | Median / sample SD | Speedup |
| --- | --- | --- | --- | --- |
| 389..419 | serial | 12.6433017, 12.5864567, 13.1268164 | 12.6433017 / .2969305 | 1.000x |
| 389..419 | 4/4 | 4.5984833, 4.6139579, 4.5568106 | 4.5984833 / .0295575 | 2.749x |
| 389..419 | 8/4 | 3.7392719, 3.6147029, 3.6541155 | 3.6541155 / .0636689 | 3.460x |
| 600..630 | serial | 5.7040663, 5.7273241, 5.6695913 | 5.7040663 / .0290475 | 1.000x |
| 600..630 | 4/4 | 2.7347167, 2.6927825, 2.7306732 | 2.7306732 / .0231320 | 2.089x |
| 600..630 | 8/4 | 2.6700993, 2.6722559, 2.6576842 | 2.6700993 / .0078647 | 2.136x |
| 1440..1470 | serial | 14.9351282, 14.8250897, 14.3579822 | 14.8250897 / .3064298 | 1.000x |
| 1440..1470 | 4/4 | 5.0691963, 5.1243991, 4.8760941 | 5.0691963 / .1303784 | 2.925x |
| 1440..1470 | 8/4 | 4.2089745, 4.1804853, 4.1894319 | 4.1894319 / .0145693 | 3.539x |

Single-screen times (serial; 2/4, 2/8, 4/4, 4/8, 8/4, 8/8), retained even when
inferior: dense 12.8343345; 6.8848425, 6.8711361, 4.6444099, 4.9991070,
3.8231377, 5.0642636. Continuing impacts 6.6762701; 3.1498365, 3.2486884,
2.8089563, 2.9858093, 2.7054686, 3.0244069. Pile 15.1906273; 7.6310920,
9.0566445, 5.3438031, 6.2252372, 4.2069109, 4.9666228. These single samples
selected configurations; repeated medians above support the reported gains.

### Lifecycle, overhead and limitations

All recorded pools completed readiness and joined every owned process. The
stationary split fixture retained exactly zero physical kinetic energy. Tests
cover success, worker kernel error, parent interruption, startup failure, dead
worker/transport errors and deterministic reduction with reverse consumption.
CLI smoke `python -B -m hw7.falling_objects --headless --steps 0 --backend parallel
--workers 2 --batch-size 3 --json hw7/evidence/parallel_pilot/cli_zero.json` passed;
its zero work is not performance evidence. Final live inventory found no Python
processes. Failed development attempts remain recorded, not relabeled as passes.

Across repeats, four-worker readiness/startup was .3137–.3239 s and shutdown
.0374–.0533 s; eight-worker startup .3613–.3791 s and shutdown .0535–.0651 s.
Startup includes spawn/native imports/readiness, not merely constructing a pool.
Every measured trial records 30 predicted and 30 diagnostic calls. Real worker
pair calls per interval were 1650 / 2121 / 3420, identical across counts/repeats;
the dense sample used seven of eight configured workers because its batches do
not fill eight slots. PID-level actual work and completion orders are retained.

Caller cold totals include Python startup/imports, checkpoint loading/provenance,
warmup, physics, final hashes, shutdown and output (not the wrapper's own JSON
write). Median cold seconds serial / four / eight workers: dense 14.1173 / 5.8691
/ 4.8642; continuing impacts 6.7706 / 3.8243 / 3.8617; pile 16.8286 / 6.5297 /
5.6790. Thus eight workers slightly lose to four in the SHORT impact invocation
despite faster stepping. Raw cold/trial/warmup/startup/shutdown samples and their
scopes are in comparison.json and each cold_invocation.json.

Benchmarks request OMP/OpenBLAS/MKL/NumExpr thread limits of one in the parent
before native imports and in every child. Runtime/version/affinity/battery and
environment are recorded per invocation. Parent and workers confine native
temporaries under parallel_pilot/native_tmp (per-worker folders). Actual native
thread pools, temperature, foreground interference and filesystem/security costs
were not independently measured; no exact causality is inferred from variance.

Preliminary recommendation: **8 workers, batch size 4, threshold 0** for the final
whole-scene candidate; four workers/batch four is a lower-overhead alternative.
No threshold/shape-based scheduling heuristic was tuned. Empty free-fall sets
stay local; few cheap nonempty queries may lose to IPC. The short intervals do
not establish phase weighting over 2880 steps, whole-scene correctness or a
whole-scene speedup. No bound/echo measurement is used as acceleration evidence.
There is no unresolved observed numerical mismatch, and no compiled rewrite was
started. Full matched comparison, final history/reflection/packaging remain open.

### Exact next full-scene commands — prepared, NOT executed

From the repository root, the following two module commands collect three runs
per mode with a 30-step discarded collision warmup and a reset to seed-7 step 0:

```powershell
python -B -m hw7.parallel_pilot measure --label final_serial --scenes full --backend serial --steps 2880 --warmup-steps 30 --repeats 3
python -B -m hw7.parallel_pilot measure --label final_parallel --scenes full --backend parallel --workers 8 --batch-size 4 --steps 2880 --warmup-steps 30 --repeats 3 --reference-label final_serial
```

Prefer the prepared evidence/parallel_pilot/final_matched.ps1 for sequential
alternating backend order and external cold timers. It performs the same three
full runs/backend with labels final_serial_r0..2 and final_parallel_r0..2 and
checks parallel value digests against final_serial_r0. Exact invocation on this
computer (process-only script policy exception; no permanent policy change):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File hw7/evidence/parallel_pilot/final_matched.ps1 -Python 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe'
```

Do not run both alternatives or overwrite labels. This long series has not been
launched. Source changes invalidate the pinned checkpoint compatibility approval;
review compatibility and rerun short correctness before future timings.

## Preserved Part 3 profiling record — 2026-11-04

Part 3, measured on the actual computer, 2026-11-04. Completed: hardware inventory, pilot, genuine cached-state preparation, representative cProfile/stage profiles, repeated unprofiled interval baselines, instrumentation validation and startup/serialization probes. **The complete 2880-step cProfile and repeated full-scene baseline remain pending. No parallel physics backend or measured parallel speedup exists.** Recommend a persistent process pool for batched narrow-phase/manifold queries, with canonical gathering and the existing serial impulse solver. The measurements and limits of this recommendation follow below.

The resumed default acceptance run completed successfully: 2880 steps/6 s at the fixed settings below, with finite/contact/penetration/containment checks passing. Its physics-loop observation was **1151.3943472 s**, including reports, corrected-pose diagnostics and 30 Hz frame sampling; final Agg snapshot rendering was .8160687 s. This is not a warmed repeated physics-only baseline (frame_stride was 16, not None), and an initial-scene render was checked separately during the acceptance work. Do not infer a speedup or stage share from that observation. It motivated the controlled interval measurements below, which preserve the numerical work and use evidence/serial_default.json and default_audit.json as correctness provenance.

## Observed environment

| Item | Observation |
| --- | --- |
| OS | `Windows-11-10.0.26300-SP0` from Python platform.platform() |
| Interpreter | `C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe` |
| Python | CPython 3.12.10, MSC v.1943, 64 bit AMD64 |
| CPU model | Intel(R) Core(TM) Ultra 9 275HX, Windows Win32_Processor |
| Logical processors | 24 from both Python os.cpu_count() and Windows NumberOfLogicalProcessors; .NET Environment.ProcessorCount also returned 24 |
| Physical cores | 24 from Windows Win32_Processor.NumberOfCores and psutil.cpu_count(logical=False); not inferred from logical count |
| Effective process affinity | Logical IDs 0..23, all 24 available |
| Power | Battery query: 100%, power_plugged=true. Active scheme GUID c4cf2f28-9877-4339-87e1-3c7d1d7f529d, named 性能 (performance) |
| Observed thread settings | OMP_NUM_THREADS, OPENBLAS_NUM_THREADS, MKL_NUM_THREADS, NUMEXPR_NUM_THREADS, OMP_DYNAMIC and OMP_PROC_BIND were unset |
| Distribution metadata | NumPy 2.3.5; Matplotlib 3.10.8; SciPy 1.17.1; psutil 7.2.2; PyVista 0.49.0 |
| Not found in this profiling inventory | Numba, Cython, threadpoolctl; no packages were installed |

Raw inventory and commands: [inventory_confined/inventory.json](evidence/profile_serial/inventory_confined/inventory.json). Windows and psutil independently agree on physical/logical counts. Core performance classes, thermal/throttling history, turbo behavior, memory bandwidth, controlled background load and actual native-library thread counts are unknown. Unset environment variables do not establish a native thread count. The initial inventory had a stdout-decoding problem in the localized power-plan name; inventory_confined corrects it. Hw5 source is unchanged. Interpreter/hardware access used approved outside-sandbox execution; all retained profiling outputs are under hw7/evidence/profile_serial.

## Reproducibility, scope and completion

Each run directory contains metadata.json with exact interpreter/argv, every numerical Options field, seed, checkpoint/load information, versions, output mode, source file SHA-256 values and aggregate source identifiers. HEAD is still 2c4b36c and is NOT sufficient to identify this uncommitted code. The measured physics source ID is `5740562222ed7b3ad9956979ee0e2718e39adaa48e9c653681ed0edea3154a10`; see each metadata.json for the complete file map and evolving profiling-tool source ID. Hashes cover Hw5 Python files and top-level hw7 Python modules. Cached states reject content/source/seed/options mismatches.

Primary measurements are headless, frame_stride=None, with no Matplotlib imports, snapshot or GUI. Report retention and corrected-pose collision diagnostics are included consistently. `physics_seconds` sums perf_counter_ns wall spans around step_world plus report append; import/setup, checkpoint loading, discarded warmup, counters/graph analysis, checkpoint/evidence writes and final hashes are outside those spans. This scope differs from the historical 1151 s Part 2 run's frame sampling. Preparation costs are separate. cProfile costs locate bottlenecks; only `plain` wall timings are speed baselines. Stage timing is optional and itself has overhead/noise; it is not a replacement speed baseline. [Python's profiler documentation](https://docs.python.org/3.12/library/profile.html) specifically warns against benchmarking Python versus native code using profiler times.

Preparation lineage is genuine simulation, never the saved Part 2 final world: seed 7/step 0 -> 240 -> 600 -> 960 -> 1200 -> 1440, preserving the full contact cache. Known persisted preparation spans were 0..600: 82.631286 s; 600..960: 94.4553415 s; 960..1440: 191.1003827 s. Thus at least 368.1870102 s of preparation step time is recorded, excluding checkpoint I/O/setup and unknown work lost after the interrupted run's last checkpoint. Metadata links the parents and hashes. State 389 came independently from the budgeted profile starting at seed 7/step 0; its 45.342076 s profiled preparation is also excluded from its interval measurements.

An early pilot/preparation used SciPy's default system temporary-file location. Function profiling exposed this, and subsequent commands explicitly set tempfile.tempdir/TMP/TEMP to profile_serial/native_tmp. Preparation was stopped with nonzero status and resumed from the last complete step-960 checkpoint. The early records are retained, with interrupted_external/complete=false on the stopped preparation; no work beyond its last checkpoint is claimed. No outside-file cleanup was performed. All interval baselines below use the confined directory. Native temporary-file location can affect performance and must match between future backends.

## Measurements actually completed

The initial 30-step pilot had unprofiled median .0984998 s and combined cProfile/stage elapsed .3878358 s (3.94x observation, not a universal overhead factor). After fixing temp confinement, the following four fixed intervals were measured sequentially. Each unprofiled baseline has three resets to its identical immutable starting world/cache and four discarded warmup steps. Warmup does not advance the measured start. No duplicate worlds were run concurrently to claim throughput acceleration.

| Interval / labels | Simulated step/time range | Raw plain wall seconds (3 runs) | Median / sample stdev (s) | Separate cProfile wall (s) |
| --- | --- | --- | --- | --- |
| Free fall: free_* | 0..30 / 0..0.0625 s | .0981013, .0862518, .0888735 | .0888735 / .0062241 | .3775604 |
| Dense-impact sample: peak_* | 389..419 / .810417.. .872917 s | 14.3891300, 14.0789681, 14.3094633 | 14.3094633 / .1610772 | 21.0784433 |
| Continuing impacts: impacts_* | 600..630 / 1.25..1.3125 s | 4.6480750, 4.6967277, 4.7177635 | 4.6967277 / .0357446 | 11.1498027 |
| Later pile: pile_* | 1440..1470 / 3..3.0625 s | 15.9091579, 17.0314607, 15.5676890 | 15.9091579 / .7658103 | 25.9803729 |

Raw references: each `evidence/profile_serial/{label}_plain/measurements.json` and `run_00..02.json`; matching `{label}_cprofile/run_00.prof`, `_functions.json`, `_cumulative.txt`, `_tottime.txt`. [summary.json](evidence/profile_serial/summary.json) indexes all raw runs, including warmups/tests/partial records, which must not be pooled with the baselines. The cProfile/median ratios differ by interval (about 4.25, 1.47, 2.37, 1.63), illustrating why profiler time is not speed measurement. Stage runs also differ from plain runs; no precise overhead causality or thermal condition is inferred.

The requested full profile was attempted with `--steps 2880 --mode cprofile --max-seconds 45`. It completed **389/2880 steps**, measured **45.342076 s**, then saved a genuine cached checkpoint and partial stats. [full_profile_budgeted/run_00.json](evidence/profile_serial/full_profile_budgeted/run_00.json) is `partial_budget`, complete=false; measurements.json has no full-run median. The module returns 2 on a budget stop (the PowerShell command wrapper reported nonzero 1); the short harness test checks the module's return value. A complete full profile was judged impractical in this step after observing overhead on the already slow scene. **Full-scene cProfile, a repeated full-scene unprofiled baseline, formal rendering-only measurements and any serial/parallel comparison remain pending. No interval was extrapolated and relabeled as measured full-scene runtime.**

## Bottlenecks and available task sizes

These are exclusive percentages from separate stage-timed observations, not cProfile shares or independent benchmark speed measurements. Exclusive values sum to 100%; inclusive manifold/detect/solver totals contain children and MUST NOT be added to those children. Pair timing covers BOTH trial collision detection and corrected-pose diagnostics.

| Exclusive category | Free fall | Dense-impact sample | Continuing impacts | Later pile (granular run) |
| --- | --- | --- | --- | --- |
| AABB + SAP | 29.80% | .20% | .46% | .20% |
| Narrow-phase kernel (analytic/GJK/EPA) | 0% | 90.76% | 83.52% | 86.25% |
| Manifold/cache work excluding kernel | 0% | 1.92% | 2.40% | 2.09% |
| Physical impulses | .23% | 5.27% | 10.30% | 9.33% |
| Split impulses | .04% | .37% | .59% | .54% |
| Other: kick, pose/cache updates, validation, setup, dispatch, reports and timer residual | 69.93% | 1.49% | 2.73% | 1.59% |

Detailed exclusive/inclusive seconds and calls are in peak_stages/run_00.json, impacts_stages/run_00.json, pile_stages/run_00.json and pile_granular/run_00.json. The latter repeats pile stage measurement with per-pair costs (15.9725982 s versus the earlier 17.2024563 s); the stage mix agrees closely. The residual step category includes prediction/pose/cache/state-report construction and wrappers, rather than falsely claiming separate exact timings for each inline statement.

Trial candidates/manifolds/solver rows per step: dense sample 27.5/27.0/61.93; continuing impacts 35.33/19.6/45.9; pile 57/52/101.7. Actual timed pair calls over the two barriers were 55 per step in the dense sample and 114 per step in the pile. Dense mean/max pair duration: 7.906/93.337 ms; pile: 4.125/72.857 ms. Many cheap analytic queries coexist with expensive EPA pairs, so load balance matters and one giant batch per worker is risky. Fixed row-visit budgets remain 120 physical and 20 split sweeps; graphs are measured diagnostics, not a new scheduling algorithm.

Function evidence: [dense profile](evidence/profile_serial/peak_cprofile/run_00_cumulative.txt), [continuing impacts](evidence/profile_serial/impacts_cprofile/run_00_cumulative.txt), [pile](evidence/profile_serial/pile_cprofile/run_00_cumulative.txt). Dense sample: 2,507 EPA calls, 18,809 simplex reductions, 66,120 Minkowski support calls and 15,639 tempfile.mkstemp calls; continuing impacts: 930/13,508/32,603/6,546; pile: 2,060/15,884/58,886/16,923. The fixed iteration limits are in metadata. Support calls and hull/error-stream counts are practical work proxies, NOT exact GJK/EPA iteration counts (they include seeding/enrichment). These counts were not converted into fictional iteration statistics.

In those cProfile runs, EPA cumulative times were 14.879/6.279/17.107 s respectively; tempfile.mkstemp cumulative times 4.600/2.015/5.201 s. The underlying nt.open self times were 4.015/1.770/4.545 s. These nested function times overlap EPA and cannot be added. EPA self time also includes untraced Cython/native hull-constructor work, not just Python arithmetic. [SciPy 1.17.1 _qhull.pyx](https://raw.githubusercontent.com/scipy/scipy/v1.17.1/scipy/spatial/_qhull.pyx) constructs a MessageStream for each hull; [MessageStream source](https://raw.githubusercontent.com/scipy/scipy/v1.17.1/scipy/_lib/messagestream.pyx) falls back to tempfile.mkstemp when an in-memory stream is unavailable. The observed Windows file calls establish that fallback here; the cause of individual file-open latency (filesystem/security/load) was not measured.

## Recommendation and estimated bounds

**Primary: persistent Windows-spawn process pool for batched narrow-phase/manifold queries in this ONE world.** Leave SAP, velocity kicking, physical/split sweeps and pose updates in the parent. For each detection barrier send immutable trial bodies/previous per-pair cache and candidate batches; workers call the unchanged narrow_phase. Gather into canonical (a,b)/point order before the existing serial solver and cache update. Repeat after pose correction for diagnostic detection, with its original enrich flag. Detection reads bodies even when pairs share one dynamic body; impulses mutate shared velocities and must remain ordered. Do not parallelize dependent impulse rows or pipeline across a state dependency.

Start experiments with 2,4,8 workers and batches around 4–8 pairs, mixing expensive shape pairs; choose counts by actual scaling, not 24-core inventory. A threshold can keep empty/cheap free-fall detection serial. Reuse workers across timesteps; never spawn per pair/step. Transmit exact pickled immutable state values initially rather than accidentally renormalizing quaternions in a new reconstruction path. Keep returned manifolds/caches deterministic and verify all physical results. Cap worker/native-library thread counts consistently across comparison modes to prevent oversubscription, recording actual settings; current measurements did not silently impose such caps.

[ipc_world/ipc.json](evidence/profile_serial/ipc_world/ipc.json): one real spawn took .357854 s to readiness; ten reused-worker round trips of a 25,832-byte genuine world/cache payload had median .4283 ms (range .3273–1.0656 ms). Local pickle dump/load medians are about .1266/.1154 ms. This was an ECHO worker, not parallel physics, and does not measure a multiworker executor or actual result payload. Even so, 4.1–7.9 ms mean pair jobs versus sub-millisecond round-trip overhead supports coarse batching; 4-pair batches amortize message cost better than scalar/support-point tasks. Shared-file I/O contention, stragglers, parent serialization and two barriers per step can still reduce gains substantially.

**Fallback: a native compiled batch of analytic support/GJK/EPA/manifold work with GIL-releasing threads**, if process IPC/load balance or shared temporary-file I/O limits the primary. This would require a verified compiler/toolchain and declared dependency/build steps (Numba/Cython are currently absent), and full geometric revalidation. Removing repeated wrapper/error-stream overhead and compiling loops is a REWRITE/COMPILATION improvement; compare that optimized kernel at one thread versus multiple threads separately to attribute additional parallel improvement. [Cython's native parallelism documentation](https://cython.readthedocs.io/en/stable/src/userguide/parallelism.html) describes OpenMP/nogil requirements. No compiled kernel is implemented here.

[CPython 3.12 threading](https://docs.python.org/3.12/library/threading.html) explains why ordinary Python CPU threads cannot generally run Python loops simultaneously; [multiprocessing](https://docs.python.org/3.12/library/multiprocessing.html) documents spawn/pickling and bypassing the GIL. SciPy releases the GIL around some native Qhull calls, but that does not establish a GIL-free whole pair pipeline: support/simplex/manifold loops and object handling remain Python. cProfile cannot quantify the exact GIL-free fraction. Existing-kernel threads could help native/I/O portions, but are not assumed to scale this complete kernel.

Parallelizing impulse islands is not the first target: the pile snapshot had eight islands, but one held 65.45% of serial island-solve time. Serial decomposition matched dynamic velocities and impulse reports exactly; full solve median .0438041 s, largest island .0282134 s ([pile_islands/islands.json](evidence/profile_serial/pile_islands/islands.json)). Even ideal island parallelism has a stage speed ceiling about 1.55x there, on a stage that is only around 10% of the pipeline. Graph-colored sweeps also add repeated barriers and can change Gauss-Seidel order. They do not address the measured dominant cost.

For target fraction p, the ideal source-based pipeline estimate is `S(P)<=1/((1-p)+p/P)` before IPC/imbalance. Measured pair durations give a stronger per-interval lower time bound: keep measured other work serial and, for EACH detection phase, use `max(sum(pair_times)/P,max(pair_time))`. [parallel_bounds.json](evidence/profile_serial/parallel_bounds.json) records the derivation inputs/results:

| Interval | Measured detection target fraction | Ideal 4-worker pipeline ceiling with pair imbalance | Ideal 8-worker ceiling with pair imbalance | Infinite-worker Amdahl ceiling ignoring imbalance |
| --- | --- | --- | --- | --- |
| Dense sample | 92.68% | 3.28x | 4.33x | 13.66x |
| Later pile | 88.34% | 2.96x | 3.74x | 8.58x |

At 24 workers the modeled imbalanced ceilings are still only 4.34x/3.74x. These are optimistic estimates from serial interval costs, assuming concurrency does not change task costs; batching, IPC and filesystem contention can only worsen this simple model. **There is no measured whole-six-second stage fraction or defensible measured whole-scene speedup bound yet.** If the full example has a similar phase mix, the table suggests an approximately 3x four-worker or 4x eight-worker upper scale, not a promised result. It is not a measured full-scene runtime or speedup. Complete whole-scene measurements are required to replace that conditional estimate.

## Instrumentation correctness and failures

Steps 240..300, including real collisions, produced exactly equal plain and combined-instrumented World, contact cache and StepReport tuples. Cross-mode final-world/report hashes also agree for all four measured intervals: [cross_mode_agreement.json](evidence/profile_serial/cross_mode_agreement.json). The 18 short profiling/solver tests passed, including wrapper restoration on failure, stage partition sums, static-body graph handling and a budget-stop test requiring nonzero return and saved incomplete profile. Completed long Part 2 suites were not repeated.

All run records begin complete=false; final status distinguishes complete, partial_budget, interrupted and failed. Journals/checkpoints are incremental. An external hard stop cannot guarantee a final profiler dump; the interrupted preparation preserves the latest step-960 checkpoint/journal and an explicit operator interruption note. Existing labels are refused instead of overwritten. The initial stdout-decoding and native-temp-confinement fixes are recorded in LOG; historical Part 2 evidence was not overwritten.

## Fixed workload and timing protocol

Use SPEC's realized seed-7 initial state: exactly 30 finite-mass bodies (ten prisms, ten spheres, ten analytic cylinders), five static bin prisms, **h=1/480 s, 2880 steps, T=6 s**, gravity `(0,-9.81,0)`, e=.15, mu=.4, **120 physical/20 split sweeps**, .03 m row correction-depth cap, identical geometry/correction tolerances. These revised Part 2 settings follow documented timestep/manifold convergence checks; the 240 Hz development run exceeded the transient penetration limit and is not the accepted workload. No sleeping, different shape approximation, fewer contacts, reduced diagnostics, altered timestep or stopping early in either comparison. Save scene/config JSON and exact Git revision/runtime so all results are attributable. Any further correctness revision requires a new shared serial baseline.

1. Revised practical future protocol: import/setup once, perform a short discarded collision-containing warmup (for example 30 steps from the genuine step-600 checkpoint), then reset the initial seed-7 world/cache. Reuse persistent workers across timesteps/runs, reporting their startup separately. No whole-scene warmup is required; the old seven-full-run plan is superseded. Current interval measurements used four discarded steps as recorded above.
2. Collect THREE complete unprofiled 2880-step physics-only runs PER backend for the eventual primary serial/parallel comparison. Do not launch them automatically in this Part 3 step. Include identical diagnostics/report retention, frame_stride=None, precision, iterations and model settings; exclude imports/construction/output/rendering. Save all samples, median, min/max, sample dispersion and exact source/config. Alternate backend order, reset physical/cache state between runs and keep library/native-thread settings equal. Speedup uses unprofiled wall time, not cProfile or summed worker CPU time.
3. Collect a separate cProfile run (not included in benchmark timings), sorted by cumulative and self time. Add coarse stage timers/counters for broad phase, GJK/EPA calls/iterations/failures, manifold enrichment, physical solver, split solver, pose updates, validation and packaging of states. Instrumentation overhead must be the same in both compared timing modes; profile-heavy runs remain separate. Examine early free fall, dense impacts and settled pile separately, keeping the whole 6 s scene as primary metric.
4. Rendering remains separate and unbenchmarked here. Later generate identical saved poses at 30 Hz (181 frames including t=0), fixed 1280x720 Agg output, 16 display segments and fixed camera. Use one untimed render warmup and three repeated rendering-only measurements, separating drawing from PNG encoding/I/O. End-to-end and GUI playback costs are separate; no rendering time may change dt or count as physics speedup.
5. Record cold process startup, pool startup, data serialization/copying, optional JIT/native compilation, memory, and shutdown separately. Also report total single-invocation headless time including setup/startup so steady-state gains do not hide overhead. Pool reuse means across timesteps of ONE world, not simultaneous independent scenes.
6. On the actual computer record AC/battery mode, power profile, foreground load, CPU affinity/worker count, runtime/library thread settings and thermal conditions. Alternate or randomize paired serial/parallel trial order after warmup, repeat if variance is large, and retain outliers with explanations. Avoid claiming all 24 cores are equally fast. Serial and parallel must use the same dependency versions, precision, checks and output settings.

## Implementation decision gate

The primary recommendation and fallback above are based on measurements; neither is implemented or proven faster. Thirty bodies have at most 435 dynamic pairs plus 150 dynamic-static pairs before broad phase. Before implementing, review source/hash/config, full-profile/baseline gaps, deterministic gather protocol and worker lifecycle. The alternatives originally considered remain useful implementation constraints:

| Candidate | When it might fit; costs and correctness requirements |
| --- | --- |
| Persistent process pool for pair detection/manifold proposals | Could bypass the CPython GIL if analytic GJK/EPA and manifold generation dominate. Batch candidates into a few coarse deterministic chunks, broadcast one compact immutable pose snapshot per step, reuse workers. Windows spawn, pickling/copies, result volume and timestep barriers may overwhelm 30 bodies. Gather results in canonical pair order and update the cache in the parent. Never send each scalar support operation as a task. |
| Threads over native kernels that release the GIL | Potentially lower overhead if a measured hot stage can be expressed in NumPy/native compiled code. Pure Python CPU threads do not bypass the usual CPython 3.12 GIL. NumPy calls on tiny vectors may be slower and release behavior must be verified for actual kernels. Numba is absent; do not assume availability, compatible versions, or free compilation. Compare one-thread and many-thread versions of the same optimized kernel to isolate actual parallel gain from algorithmic rewriting. |
| Deterministic graph coloring or independent contact islands | Only if coupled impulse iterations dominate and profile justifies it. Rows sharing a dynamic body are dependent and cannot mutate velocities concurrently. Build a conflict graph with a whole manifold as a unit; static bin sharing alone is not a data conflict, but shared dynamic bodies are. Solve independent colors concurrently with barriers; fixes an explicit color order in BOTH serial/parallel variants. A dense pile may have one island and many colors, giving little parallelism. Changed ordering needs fresh correctness validation. |

Also consider batching independent per-body force kicks/bounds only if their measured fraction can yield a useful gain. These stages are small at N=30. Do not choose process/thread/native/GPU technology based on core count alone. Do not parallelize separate seeded worlds or duplicate scenes as a substitute for accelerating this single simulation. Do not run dependent normal/tangent or pseudo rows concurrently without a proven scheduling method.

For each experiment measure worker counts 1,2,4,8 and further counts only if justified by scaling; use fixed reused workers and avoid native-thread oversubscription in process workers. Include serial gather/cache work and all IPC in physics timings. Shared-memory/native data layouts are options if copying is a demonstrated bottleneck, not a preselected implementation. If all candidates lose, preserve the measurements, revise granularity/layout/kernel approach and profile again. Assignment completion requires demonstrated improvement on the actual example; a slower result cannot be relabeled a speedup or hidden behind throughput of independent worlds.

## Required eventual results

| Quantity | Serial | Parallel |
| --- | --- | --- |
| Git revision / backend / worker count | Pending | Pending |
| Same-scene correctness result and tolerances | Part 2 accepted; short instrumentation checks exact | Not implemented/tested |
| Raw interval wall times / variability | Three repetitions per interval, above | Unmeasured |
| Three complete full-scene wall times / median / variability | Pending | Pending |
| Cold total invocation / worker setup / optional compilation | Unmeasured | Unmeasured |
| Rendering-only and end-to-end timings | Unmeasured | Unmeasured |
| IPC overhead / stage shares | Echo probe and interval stage shares measured; full-scene shares pending | No backend measurement |
| Speedup S = median(serial)/median(parallel) | — | Unmeasured |

Report absolute seconds, sample dispersion, speedup, and parallel efficiency S/p where meaningful. Require repeatable S>1 exceeding observed timing noise plus passing TEST_PLAN agreement/physics criteria; report uncertainty or paired confidence interval. Retain unsuccessful experiments and explanations. Distinguish improvement over original Python baseline from improvement of parallel over the identical optimized single-worker algorithm. Store future benchmark harness, profiles, raw JSON, and logs under `hw7/`; do not overwrite older assignments' performance/history records.
