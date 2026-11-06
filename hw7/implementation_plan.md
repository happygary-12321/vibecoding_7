# HW7 staged implementation plan

Updated through Part 5. Serial code, persistent spawn collision workers, unittest
fixtures, CLI and visualization are implemented under hw7/, importing unchanged
Hw5 source. Serial profiles, interval comparisons and the six-trial matched
full-scene results are recorded in PROFILE. Exact complete-scene agreement and
original acceptance passed; whole-example median speedup 2.827684047x. No commits,
pushes, installations or nested repository were created.

Stage status: 1–4 accepted for the documented serial fixtures/default scene;
5 headless/JSON/Agg complete, live GUI unverified; 6 representative profiles
complete for representative scope (extra full cProfile/rendering not part of
Part 5); 7 complete for this seed-7 scene: backend, short checks, interval pilot
and six exact accepted full-scene trials/replays with measured acceleration;
8 real Git history, student reflection and verified packaging pending.
Prior 44-distinct-method HW7/72-test Hw5 records and 2880-step serial acceptance
are preserved. Part 4's short suite records 48 passed without repeating the long
acceptance in Part 4. Part 5 adds four evidence-harness checks and three complete
trials/backend, sequential and alternating, with saved states/reports. Only
factual activity is added to LOG; its personal section is empty.

## 1. Establish the serial foundation

Recheck applicable AGENTS.md and Git status; preserve root README changes, untracked Hw5/hw6 and lecture PDF. Create hw7 package, immutable Body/World/Options and separate static flags. Import inspected Hw5 geometry, RigidState and spatial APIs; keep positive finite geometry masses even for static display/collision shapes. Implement world/body angular frame conversions and a force-kick/predictor adapter using `advance(...,ground=False)`, without inheriting ground correction. Validate clocks, immutable failure behavior and free-flight agreement with the specified adapter ordering. Future outputs and bytecode must stay in hw7/ (`-B` for commands importing Hw5).

Implement deterministic scene generation exactly as SPEC, with 30 finite-mass bodies and five finite static bin colliders. Save realized initial states/config and independently check geometry bounds and initial separation. Build exact rotation-aware AABBs and sweep-and-prune closed-interval endpoint handling. Write the independent brute-force and analytic-bounds tests described in TEST_PLAN. Gate: exact candidate completeness and deterministic pair ordering, including touching and static bodies.

## 2. Implement and validate narrow phase before dynamic piles

Add arbitrary-direction analytic support maps and witness-carrying distance GJK. Implement robust simplex reduction, dimensional tolerances, touching versus enclosing overlap, EPA initialization/expansion/barycentric recovery, deterministic ties and explicit failure diagnostics. Add the analytic sphere-sphere branch. Keep all six unordered shape combinations and bin prism contacts in scope from the start. Do not substitute AABBs or bounding spheres for narrow phase, or display meshes for cylinder geometry.

Write TEST_PLAN's known-gap, rim/cap/corner, rotated, containment, symmetry and degenerate cases; test-local SAT, point-to-solid distances and Rodrigues matrices serve as independent oracles. Gate: all pair types handle separated, touching and penetrating cases; nonconvergence reports an error rather than omitting contact. Use smaller fixtures for development, but retain the shared 30-body example unchanged for final comparison.

## 3. Build manifolds and the physical solver

Implement witness conventions and common physical impulse points, local-anchor cache refresh, prism clipping, perturbation with mapping to original transforms, finite prism-face support-feature seeding and deterministic four-point reduction. Verify resting box/cap/generatrix patch spread and stale-point rejection. Do not confuse persistent geometry with impulse warm starting: baseline accumulated impulses start zero each step.

Add two-body projected sequential impulses with world inertia, angular response, frozen restitution targets/cutoff and Coulomb disk projection. Validate centered unequal/equal masses, off-center hand fixture, static limit, grazing/separating contacts and friction before full simulation. Check isolated fixed-pose momentum and appropriate energy behavior. Gate: analytic fixture expectations pass independently of collision detection, and manifold tests expose the old centroid-only limitation.

## 4. Add split impulse and complete stepping

Implemented separate pseudo velocities/lambdas, slop/beta, row/per-body correction limits, 120 physical/20 pseudo alternating sweeps, translation/world rotation correction, and final body-frame omega conversion. Pseudo terms stay outside physical velocities/restitution/friction. Stationary hand-depth/zero-velocity, rotated overlap, split-disabled, caps and validation fixtures are implemented. The .03 m row depth cap and denser scene timestep follow recorded failures and preserve the original acceptance limits.

Run isolated rest/stacks at h=1/240, refinement fixtures, 1440-step/3 s smoke at h=1/480 and full default 2880-step/6 s scene at h=1/480. Preserve failed 240 Hz development evidence; do not label it accepted. No exact conservation/perfect stacking promise. The serial workload must pass before optimization.

## 5. Provide the runnable example and visualization

Implement `hw7/falling_objects.py` and module CLI per README. Use headless default, explicit show/snapshot modes, fixed 30 Hz state sampling and imported `world_mesh` for display only. Adapt Matplotlib draw logic for all 30 bodies/bin, shape colors, orientation markers and optional contact diagnostics; physics must not depend on GUI clocks. Snapshot smoke testing verifies an actual saved image, followed by visual inspection for correct y-up axes, geometry and bin. Manual GUI playback, if performed, must be recorded separately; do not infer it from a PNG. Gate: clean headless run and repeatable scene/summary, followed by actual renderer verification.

## 6. Profile the serial implementation on the actual computer

Completed hardware/affinity/runtime inventory, pilot, genuine simulated cached checkpoints, free-fall/dense-impact/continuing-impact/later-pile stage and cProfile intervals, three unprofiled timings per interval, exact short collision-run instrumentation agreement and process startup/serialization probes. Source hashes cover uncommitted physics. Evidence is incremental under evidence/profile_serial/. The full cProfile attempt stopped at its 45-second budget after 389/2880 steps; it is explicitly partial. At the Part 3 checkpoint, full-scene stage shares, complete profile, repeated full baseline, rendering-only and cold totals were pending. Part 5 now completes the repeated full baseline and cold invocation measurements; the additional profiling/rendering work was not run. Revised practical protocol: short discarded collision-containing warmup, then three complete runs per backend, with identical diagnostics and no frame sampling. No whole-scene warmup or seven-run sequence is required. Do not extrapolate intervals as measured full runtime.

## 7. Choose, implement and verify parallel acceleration

Part 4 implemented persistent spawned workers for unchanged narrow-phase/manifold
queries at both barriers, dynamic consecutive-pair batches, canonical gathering
and unchanged parent cache/physical/split solving. Explicit lifecycle cleans up
on success/failure/interruption, with no serial fallback. Real-worker tests and
genuine 30-step cached-state exact comparisons passed. Preliminary measurements
screen 2/4/8 workers with batches 4/8; promising batch-4 configurations receive
three sequential, alternating-order repeats alongside fresh serial baselines.
Results, overhead and limitations are retained under evidence/parallel_pilot/.
No compiled-kernel rewrite was needed. Part 5 closed the Stage 7 gate with
three uninterrupted 2880-step trials/backend, matching every World/cache/report
value and passing original physical/containment acceptance. Median serial
1066.6222320 s / parallel 377.2070056 s = 2.827684047x; source/configuration,
dispersion, cold startup and replay evidence are under evidence/full_scene/.
The interval results alone were not used to close this gate.

Run the serial/parallel agreement fixtures and identical 30-body workload under the predeclared tolerances. Gather canonical pair results and deterministic updates; investigate the first mismatch. Repeat warm/cold timings with paired order and report S/variance, rendering and setup separately. If slower, keep that result and revise the approach; do not claim assignment completion until a real repeatable single-example speedup passes correctness. Do not replace this task with parallel duplicate worlds. Gate: actual measured speedup on the user's computer, with dependencies and tradeoffs disclosed.

## 8. Final documentation, history and packaging

Replace future-tense setup with verified commands/dependency versions; complete PROFILE with both measured modes, unsuccessful experiments, raw evidence and limitations. Append factual implementation activity to LOG. Leave the personal section empty for the student to write personally; do not draft, paraphrase or propose wording for it. The student's paragraph is a final human deliverable, not an implementation blocker.

At a later explicitly authorized stage, make real incremental commits in the existing root repository for the completed stages and evidence. Stage only relevant files deliberately; Hw5 source dependencies are currently untracked, so ensure they are included in the final tracked runnable codebase without accidentally including unrelated hw6/PDF/root changes. Do not fake earlier dates/history or rewrite historical records. No commits in Part 1 and no nested hw7/.git.

Package the existing checkout/history so the real root `.git` is included, along with hw7 and every imported source dependency and reproducible external requirements. Verify imports from a fresh extraction/checkout without relying on an author's adjacent files or global undeclared packages; use a package copy under hw7/ for validation artifacts where needed. A history-free source archive is insufficient. Final audit: runnable `hw7/falling_objects.py`, all required source, passing checks, measured PROFILE, factual LOG plus student-authored paragraph, actual Git history, no accidental unrelated file modifications. Report only checks actually executed.

## Open issues and next action

No missing assignment detail blocks work. Part 5 completed the final matched
2880-step unprofiled comparison with identical settings/diagnostics, no frames,
separate startup/cold totals and all saved acceptance replays. No additional
physics timing is needed for this stage. Next is the student's own reflection,
then separately authorized real Git history and final clean-package verification;
do not commit/push/package as part of Part 5.
Broader seeds/extreme geometries, live GUI, full-scene profiles, rendering timings
and clean-environment packaging remain limited or unverified. Core counts/affinity
were measured; core performance classes/thermal history remain unknown. Required
student-only reflection, authorized real commits and final packaging remain open.
