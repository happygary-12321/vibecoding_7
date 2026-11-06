# HW7 — serial multi-body contact

## Part 5 full-scene commands

**Full-scene verification and benchmarking passed:** all six 2880-step runs
agree exactly in final World/cache and every report, pass the original physical
acceptance limits and replay successfully. With eight workers/batch four,
median stepping is **377.2070056 s parallel vs 1066.6222320 s serial**,
**2.827684x speedup**. Cold median speedup is 2.800542x. Raw samples, ranges,
sample SDs, overhead and limitations are first in [PROFILE.md](PROFILE.md), with
[raw summary](evidence/full_scene/comparison.json). Residual motion remains at
6 s. Reflection, real Git history and verified packaging are still pending;
no commit/push/package was made.

The active complete-scene evidence is under `evidence/full_scene/`; its
README.md describes the audited runner, timing scope, acceptance replay and
resume rules. The prepared Part 4 script remains as history. Use the following
from the repository root, replacing python with the installed interpreter:

```powershell
# Equal requested native limits for standalone examples/tests:
$env:OMP_NUM_THREADS='1'
$env:OPENBLAS_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
$env:NUMEXPR_NUM_THREADS='1'
python -B -m hw7.falling_objects --headless --backend serial
python -B -m hw7.falling_objects --headless --backend parallel --workers 8 --batch-size 4 --serial-threshold 0
python -B -m hw7.parallel_checks tests_new
# Sequential full comparison; skips compatible complete trials when resumed:
python -B -m hw7.evidence.full_scene.schedule
# Read/audit a trusted retained result; no simulation:
python -B -m hw7.evidence.full_scene.runner replay --label full_parallel_r0
```

The benchmark runner itself requests the equal limits before native imports.
Each full trial starts at seed 7, step/time zero with empty contact cache, 30
dynamic bodies/five static solids, dt=1/480, 2880 steps and 120/20 sweeps.
Warmup discards 30 collision steps from the genuine step-600 cached world,
then resets the complete state. Both paths retain reports and both diagnostics,
with no frames/rendering. Parallel uses eight persistent workers, batch four,
threshold zero. All dispatch/IPC/gather/synchronization is inside stepping time.
Identical 120-step progress writes are included and their I/O cost recorded;
startup/readiness, warmup, shutdown and final export/audit costs are separate.

Visual playback (`--show`) currently waits for the entire physics simulation
and saved-frame precomputation before opening the animation window. The saved
30 Hz playback does not control the fixed physics timestep. Full benchmarks
do not open a window or produce snapshots.

## Earlier setup and Part 4 interval work

The solver and falling-objects example support serial detection and a persistent
Windows-spawn parallel collision backend. Thirty finite-mass objects (ten prisms,
ten spheres, ten analytic cylinders) fall into a finite five-solid bin. Both
backends use identical narrow-phase/manifold arithmetic, cache updates and ordered
serial physical/split impulses. Part 4 interval results are preserved in
evidence/parallel_pilot/; Part 5's verified full-scene results are above and first
in PROFILE.md.

## Part 4 commands and lifecycle

From the repository root (replace python with the installed interpreter):

```powershell
python -B -m hw7.falling_objects --headless --backend serial
python -B -m hw7.falling_objects --headless --backend parallel --workers 4 --batch-size 4
python -B -m hw7.parallel_checks tests_new
python -B -m unittest -v hw7.tests.test_parallel
python -B -m hw7.parallel_pilot validate --label validation_new
python -B -m hw7.parallel_pilot screen --label screen_new --reference-label validation_v3
python -B -m hw7.parallel_pilot measure --label serial_new --backend serial --reference-label validation_v3
python -B -m hw7.parallel_pilot measure --label parallel_new --backend parallel --workers 8 --batch-size 4 --reference-label validation_v3
```

Example commands default to the complete 2880-step scene; measurement commands
default to only 30 steps from each genuine cached step-389/600/1440 world. They
never silently run the full benchmark series. Labels must be new. The measurement
tool fixes seed=7, dt=1/480, 120/20 sweeps and includes report retention, both
detection barriers, dispatch/IPC/gather/synchronization; no rendering or frames.
It resets state/cache each trial, discards four warmup steps and separately
records pool readiness/startup, shutdown and total trial cost. Caller wall timers
in retained cold_invocation.json files also include imports, process startup and
result output. Historical 1151-second frame-sampled acceptance is not its baseline.

`parallel.py` uses importable worker functions and explicit spawn processes with
one pipe each. A simulation owns one pool across all steps and both barriers;
direct `step_world(..., backend='parallel', detector=pool)` callers own an active
`with ParallelDetector(...) as pool` context. Workers only query immutable pair
data; parent orders results canonically and performs every velocity/cache update.
Exceptions, dead workers and interruption clean up owned workers and propagate;
there is no failure fallback. `--serial-threshold 0` (default) sends every nonempty
candidate set to workers. Higher thresholds run cheap sets serially; reported
dispatch/worker-PID pair counters reveal actual worker work.

Workers request one OMP/OpenBLAS/MKL/NumExpr thread and use per-worker native temp
folders inside hw7/. The measurement module sets the same environment limits in
the parent before native imports. To apply them also to standalone examples or
direct unittest commands, set OMP_NUM_THREADS, OPENBLAS_NUM_THREADS,
MKL_NUM_THREADS and NUMEXPR_NUM_THREADS to 1 before launching Python. Actual native
thread counts are not independently asserted. No dependencies were installed.

Historical checkpoint loading is still strict by default. Part 4 explicitly
uses evidence/parallel_pilot/compatibility_v3.json, which pins exact current source
hashes and the old source ID, with only audited world/CLI dispatch changes to the
original physics files. Collision/manifold/solver/Hw5 hashes are unchanged. Any
further Python source changes invalidate that approval; do not bypass the check.
The Part 3 profiling CLI does not automatically accept changed-source checkpoints;
use the new tool for these parallel comparisons.

- [SPEC.md](SPEC.md): implemented APIs, deterministic scene, equations and documented design corrections.
- [TEST_PLAN.md](TEST_PLAN.md): independent geometry/physics expectations, implemented test mappings and remaining gaps.
- [PROFILE.md](PROFILE.md): complete-example serial/parallel comparison first, followed by historical interval profiles, hardware and raw evidence.
- [implementation_plan.md](implementation_plan.md): staged implementation and final packaging gates.
- [LOG.md](LOG.md): factual activity, commands/results, failures/fixes and empty student-only reflection section.

## Setup and commands

Run from the existing repository root, keeping Hw5 beside hw7. Tested interpreter: CPython 3.12.10. Existing imports verified: NumPy 2.3.5, SciPy 1.17.1, Matplotlib 3.10.8. SciPy/Qhull triangulates internal EPA support polytopes; it does not replace cylinders with meshes. Matplotlib is optional for headless physics. No packages were installed during this task. To prepare another Python 3.12 environment, install the declared dependencies explicitly:

```text
python -m pip install -r hw7/requirements.txt
```

Portable invocations (replace `python` with your interpreter path if necessary):

```powershell
# Default: seed 7, h=1/480 s, 2880 steps = 6 simulated seconds.
python -B -m hw7.falling_objects --headless
python -B -m hw7.falling_objects --headless --seed 7 --dt 0.0020833333333333333 --steps 2880 --velocity-iterations 120 --split-iterations 20 --json hw7/evidence/run.json
python -B -m hw7.falling_objects --headless --snapshot hw7/evidence/falling_objects.png
python -B -m hw7.falling_objects --show
python -B -m unittest discover -s hw7/tests -p 'test_*.py' -v
# Same verbose tests, plus saved commands/output and confined temporary files:
python -B -m hw7.verify --suite hw7
python -B -m hw7.verify --suite hw5
```

The runnable example is **hw7/falling_objects.py**, invoked as a module so Hw5 imports resolve. Default/headless without --snapshot never imports Matplotlib. --show plays saved 30 Hz frames, after physics has completed, with orientation markers on every dynamic solid. GUI playback cannot change the physics timestep. --snapshot uses Agg without opening a window. Shapes use 16-segment display meshes only; cylinder collision/inertia remain analytic. The generic `Options` API defaults to h=1/240 for small analytical fixtures; the CLI's denser falling scene deliberately uses h=1/480 after the 240 Hz run exceeded its transient penetration target.

The JSON summary reports shape/static counts, simulated time, finite states, quaternion residual, before/after penetration maxima, worst pair/step, 95th percentile of per-step maxima, final and final-two-second penetration, nonzero impulse-row counts, correction caps, final kinetic energy/speed, and escaped COM IDs. `physics_loop_seconds` includes stepping, collision diagnostics, report retention and optional frame sampling. It excludes imports, construction, rendering and output I/O; it is a single correctness-run elapsed time, not a benchmark. Snapshot rendering time is reported separately; --show includes the user's playback/window wait. JSON evidence includes realized initial/final states and numerical options. Snapshot mode retains frames, so compare physics timings only under identical output modes.

Keep outputs under hw7/ and use -B to prevent bytecode in Hw5. The verification wrapper confines temporary files/Matplotlib caches under hw7/evidence. The renderer also defaults its Matplotlib cache there. --json and --snapshot write only explicitly requested paths. No automatic installs, hidden sleeping, teleportation, removal of escaped bodies, or invalid-state suppression.

## Source and numerical limits

`model.py` contains Body/World/Options; `math3.py` internal tuple algebra; `collision.py` bounds/SAP/support/GJK/EPA; `manifolds.py` clipping, cap/line seeds and cache; `solver.py` physical/friction/pseudo rows; `world.py` step order and diagnostics; `scene.py` the scene/bin; `rendering.py` saved-frame visualization; `falling_objects.py` CLI. Tests use standard-library unittest and independent literal formulas, brute-force overlap, Rodrigues and OBB SAT oracles. `verify.py` preserves verbose verification evidence. `evidence/diagnose.py` is a development diagnostic, not a solver backend.

This is a discrete first-order solver without CCD: sufficiently fast bodies can tunnel through thin walls. Finite iteration counts leave residual drift; sampled cap manifolds and near-degenerate EPA can be expensive or fail explicitly. No guarantees for arbitrary high speeds, mass/aspect ratios, deep interpenetration, exact conservation, perfectly motionless stacks, or every seed/timestep. Split correction can change potential energy and anisotropic rotational energy at nonzero physical spin; stationary overlaps retain zero physical velocities in the checked fixtures. Representative profiles, interval pilots and Part 5 repeated full-scene comparisons are complete; exact results and remaining submission work are recorded above. Live GUI interaction is not implied by verified Agg snapshots.

## Serial profiling tools

Run from the repository root. Each label creates a new directory under `hw7/evidence/profile_serial/` and refuses overwrite; change labels when repeating. The tools use existing dependencies, confine native temporary files, record exact argv/runtime/options/source hashes and save incremental completion records. Primary measurements include stepping, collision diagnostics and reports, with no frames, snapshots or GUI. Preparation/loading/warmup/output costs are excluded and recorded separately. Only `plain` wall times are speed baselines; stage and cProfile runs locate costs.

```powershell
python -B -m hw7.profiling inventory --label inventory_new
python -B -m hw7.profiling measure --label pilot_new --steps 30 --mode plain --repeats 3 --warmup-steps 4
# Build genuine intermediate states with the full contact cache; this takes time.
python -B -m hw7.profiling prepare --label states_new --targets 0,240,600 --mode stages --journal-every 60
# Existing trusted local checkpoint from this profiling step:
python -B -m hw7.profiling measure --label impacts_new --checkpoint hw7/evidence/profile_serial/states_0600/checkpoints/step_000600.pickle --steps 30 --mode cprofile --warmup-steps 4
python -B -m hw7.profiling validate --label validation_new --checkpoint hw7/evidence/profile_serial/states_0600/checkpoints/step_000240.pickle --steps 60
python -B -m unittest -v hw7.tests.test_profiling hw7.tests.test_solver
python -B -m hw7.profile_analysis summarize
```

`--mode stages` collects nested inclusive/exclusive stage and pair timing; `combined` also runs cProfile. Preserve the default seed, dt, solver iterations and all Options for comparisons. Checkpoints are pickles: load only trusted locally generated evidence. Their manifests validate content/source/options/seed; they are not portable across arbitrary physics changes. `profile_analysis ipc` is an echo-only worker overhead probe, and `islands` measures serial solver decomposition; neither implements parallel physics.

A future full profile can use `python -B -m hw7.profiling measure --label full_new --steps 2880 --mode cprofile --journal-every 30`. This is a long command. Optional `--max-seconds 45` stops after a complete step, saves partial stats/checkpoint and returns nonzero (2); it does not certify a full run. A future full unprofiled baseline uses `--mode plain --steps 2880 --repeats 3` after the documented short discarded collision warmup policy in PROFILE. Do not automatically launch a sequence of full runs. Failures/interruption remain incomplete and return nonzero; a hard process termination may preserve only the latest journal.

Completed Part 3 measurements and exact commands are linked from [PROFILE.md](PROFILE.md).
They motivated Part 4's implemented persistent pair-query workers. The budgeted
full profile remains incomplete at 389/2880 steps. Part 5 completed the final
full-scene comparison; extra rendering benchmarks were not run. Older Part 3 observations below are
retained with their original timing scope.

## Actual verification

Saved passing evidence covers 44 distinct HW7 unittest methods across a 41-test full run and overlapping 35-test focused run, plus 72 unchanged Hw5 regressions. These completed suites were preserved rather than repeated when resuming. Verbose names/counts are in [LOG.md](LOG.md) and evidence/*_tests.log/json.

The default seed-7 run completed all 2880 steps (6 s) with finite states and unchanged bin bodies. Maximum corrected penetration was .0162515352 m; maximum over the final two seconds was .00128875481 m; final depth was .00116464186 m. The independent [default audit](evidence/default_audit.json) passed record/count/clock, penetration, static-body and full analytic shape-containment checks, including below-rim placement. [Initial](evidence/initial_scene.png) and [final](evidence/falling_objects.png) 1280x720 Agg images were generated and visually inspected. Live --show playback was not tested.

**Runtime limitation:** this one correctness run took 1151.394 s (about 19 min 11 s) in the physics loop with frame sampling/report retention, plus .816 s for the final snapshot render. The default --show command completes physics before opening playback. These are single observations, not formal profiling or a speedup comparison. Maximum final speed was .388252 m/s and kinetic energy .495070 J: some motion remains at 6 s. The example shows falling, impacts and reduced motion; it does not freeze bodies or promise complete rest. The full initial/final states, options and summary are saved in [serial_default.json](evidence/serial_default.json).

Final packaging must include hw7/, every imported Hw5 source dependency (`__init__.py`, `dynamics.py`, `spatial.py`, `geometry.py`, `rigid.py`), declared third-party requirements and the repository's **real root .git history**. A source ZIP or git archive alone omits .git and is insufficient. Clean-environment packaging verification is pending. Hw5 is currently untracked, so a future authorized history stage must explicitly include required source without sweeping in unrelated work. No commit, push or nested repository was created in Part 2. The required personal paragraph in LOG.md must be written by the student without agent drafting assistance.
