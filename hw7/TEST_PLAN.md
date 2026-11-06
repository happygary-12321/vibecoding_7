# HW7 correctness plan and Part 2 implementation mapping

Part 1 proposed the independent expectations below. Part 2 implements standard-library unittest fixtures under hw7/tests and preserves actual output under hw7/evidence. LOG.md and the saved verification records distinguish executed checks from remaining gaps; numerical budgets below were not enlarged to make failures pass.

## Implemented checks

| File / named tests | Coverage |
| --- | --- |
| test_geometry.py, BroadPhaseTests.test_randomized_completeness_and_order / test_touching_equal_nested_static_intervals | Independent O(N^2) overlap reference, 0/1/2/30/35/100 proxies, randomized permutation, touching/nested/zero-width intervals and static filtering. |
| test_oriented_prism_and_sphere_bounds / test_cylinder_45_degree_bounds_and_rim_enclosure | Independent rotated-corner extrema and literal cylinder projection/rim enclosure. |
| test_scene_initial_separation_and_static_candidates / test_invalid_bounds_and_duplicate_ids | Exact shape counts, replay, no initial AABB candidates, bounds/ID validation. |
| NarrowPhaseTests.test_*_separated_touching_penetrating_rotated (six tests) | All six unordered types at known axial gaps plus common rigid rotations and pair-swap normals. |
| test_rotated_boxes_against_independent_fifteen_axis_sat | 60 arbitrary-oriented box fixtures versus test-local OBB SAT/Rodrigues. |
| test_box_corner_sphere_rejects_aabb_false_positive / test_cylinder_sphere_rim_and_containment / test_cylinder_cap_cap_and_perpendicular_interior / test_coincident_spheres_and_prism_containment | Corner/rim formulas, cap contacts, contained/coincident/degenerate cases, independently known interior point. |
| test_every_bin_face_shape_and_rotation / test_finite_wall_end_not_infinite_plane | 90 subfixtures: five finite bin faces, three shapes, two orientations, three signed gaps; finite wall-end separation. |
| test_spread_face_cap_and_generatrix_manifolds / test_iteration_failure_is_explicit | Spread box face, cylinder cap and support line; hard iteration-cap failure. |
| test_solver.py, ImpulseTests | Equal/unequal masses, restitution/energy/linear momentum, synthetic off-center angular response, anisotropic rotated world inertia, static limit, sliding/sticking friction, separating/resting cutoff, approaching corners. |
| SplitAndValidationTests | Exact stationary overlap .01 -> .00802 m with zero physical velocities, rotated stationary prism, slop/caps/split-disabled controls, invalid inputs, free-flight clocks and deterministic replay. |
| test_system.py, RestingAndStackingTests | Four 10 s resting fixtures and three-box/three-cylinder stacks at h=1/240 with unchanged .002/.005 m penetration and .005 m horizontal drift limits; sphere refinement h/h2 versus independent exact discrete depth. |
| ExampleTests | 30-body 3 s smoke at h=1/480 (1440 steps), genuine pair/bin impulses, count/finite/clock/containment and .03 m transient/.01 m final penetration checks; CLI/JSON smoke. |

Run `python -B -m hw7.verify --suite hw7` for saved verbose output and `--suite hw5` for existing regressions with temporary files confined to hw7. `--suite focused` runs geometry/solver checks. Three additional focused tests (anisotropic inertia, sticking, invalid bounds) were added during the full run; consult its discovered test count versus the focused record rather than assuming an earlier run discovered them.

Remaining gaps: long-run arbitrary nonspherical free-flight conservation/refinement is covered by existing Hw5 tests, not a separate HW7 world-integrator convergence study; full randomized cylinder-cylinder distance/depth oracles, systematic feature-cache churn, all mass/aspect-ratio regimes, all seeds, and live GUI playback remain unverified. A static Agg snapshot does not verify animation interaction. Parallel agreement is pending and has no implementation. Default six-second scene acceptance is checked separately from the three-second automated smoke using its saved per-run summary/initial-final states; future all-step energy traces and broader seed sweeps would strengthen the evidence.

## Completed default-scene acceptance after resume

The saved full/focused unittest records (41 and 35 tests, 44 distinct methods) and 72 Hw5 regression passes were not rerun unnecessarily. The previously interrupted default CLI was restarted from its initial state and completed 2880 steps at h=1/480, seed 7, 120/20 sweeps. `evidence/serial_default.json` records finite states, 30 dynamic/five static counts, genuine body-body/bin impulses, .0162515352 m maximum corrected penetration and .00128875481 m maximum during the final two seconds. Final depth is .00116464186 m. The original .03/.01 m acceptance limits passed unchanged.

`python -B -m hw7.evidence.audit_default` then exited zero and wrote `evidence/default_audit.json`. It verifies actual body record count/IDs/dynamic count, unchanged static records, dynamic clocks/finite states, summary penetration limits and independently calculated analytic extents within x/z +/-2.01 m, bottom y>=-.01 m and top y<=2.41 m. The added upper-rim and record checks strengthen the audit; they do not change the simulation or relax its tolerances. No full shape was outside that envelope. Initial/final Agg snapshots were generated and visually inspected for recognizable solids, bin and y-up coordinates; no GUI interaction is claimed.

The six-second run retained motion (maximum final speed .388252 m/s, final kinetic energy .495070 J), so it is accepted for the stated contact/containment/finite-state scope, not certified as completely motionless. Its 1151.394 s physics-loop elapsed time is a correctness observation and exposes a substantial performance limitation. Formal profiling, broader stress cases and parallel agreement remain pending.

## Oracle independence and tolerances

Separate geometric tolerance, solver slop, float roundoff and integration error. Use meters for lengths, radians for orientation and explicit units for momenta/energy. Unit-scale analytic fixtures should meet 1e-10 absolute plus 1e-10 relative for closed-form impulse/state algebra; iterative GJK/EPA depth/distance uses 10*eps_geom and normal error <=1e-4 rad on unique well-conditioned normals. Do not demand one particular normal for symmetric containment or face ties; require a unit valid separating direction and a consistent depth. Touching lies in a geometric uncertainty band. Tests just outside the band, at +/-1e-5 m for unit shapes, must distinguish separation and penetration.

Use literal analytic dimensions/inertias and independently written dot/cross, matrix or Rodrigues formulas in oracles. Do not call production support, inertia transform, GJK, SAP, or solver helpers to calculate their own expected answers. Seeded randomized tests supplement hand fixtures, not replace them. Finite-state and serial agreement tests alone cannot establish physical correctness. Full-run budgets below are engineering targets, subject to evidence and documented revision before performance comparisons; they are not guaranteed observations.

## Broad phase

1. Independent brute-force O(N^2) closed-interval overlap on literal AABBs, excluding only static-static. Compare exact sorted pair sets to SAP on random boxes (seed 41; 2, 30, 35, 100 proxies), empty/single cases, all overlapping, disjoint, equal endpoints, equal minima, nesting, negative coordinates, and input permutations. Explicit fixture `[0,1]` and `[1,2]` must be a candidate. Every pair appears once, lower ID first. Repeated runs have identical ordering.
2. Oriented bounds: independently enumerate eight rotated prism corners; sphere bounds center +/- radius; independently derive cylinder axial/radial projection extents. Test identity, quarter turns and arbitrary Rodrigues rotation. Each bound encloses independently sampled cylinder cap/rim points. Sampling alone is not an exact extent oracle; compare literal extents in axis/45-degree fixtures. No underbounds beyond 1e-12 m at unit scale.
3. Compare SAP to brute force using these independently calculated oriented bounds for scene states and randomized poses; for padded intervals compare equal padding on both sides. Include dynamic-static, exclude static-static, and test updated static/dynamic ID order. Near contacts admitted by the narrow-phase envelope must survive broad phase.

## All shape pairs and finite bin solids

Use prism P with full dimensions (2,2,2), sphere S radius 1, cylinder C radius 1/length 2 along local z. Each below places A at origin, B at `(D,0,0)`, equal orientation. Test D=2.01, 2, 1.9: independent expected signed gaps .01, 0, -.1 m, depth 0,0,.1. This exercises P-P, P-S, P-C, S-S, S-C, C-C separately. At D=1.9, the minimum translation depth is .1 along x; no substitute bounding sphere gives the correct suite. Check contact anchors on true analytic surfaces, normal unit length and direction, pair-swap symmetry, midpoint impulse point, and reproducible ties.

Extend each pair with independent nontrivial fixtures:

| Pair | Additional independent geometry oracle |
| --- | --- |
| P-P | Rotate both unit cubes 45 degrees around world z; B moves along x. Their world-axis center separation at first contact is 2*sqrt(2); translate +/- .01 to either side. For general rotated boxes compare test-local 15-axis OBB SAT (three face axes each plus nine nonzero cross axes), not production GJK. SAT classifications suffice where the minimum-depth direction is nonunique. |
| P-S | Sphere at `(1+.8,1+.8,0)` is separated from cube despite overlapping AABBs: closest-corner distance sqrt(1.28)>1. At `(1+1/sqrt(2),1+1/sqrt(2),0)` it touches; at `(1+.6,1+.6,0)` penetration is `1-sqrt(.72)`. Rotate and translate the entire fixture via a test-local matrix. |
| P-C | Cylinder axis z, centered above cube top at y=2 gives side/face touch. Put its axis along y using a literal quarter-turn matrix; half length .6 and radius .3, bottom cap at y=1 when COM y=1.6. Touch depth zero, shift COM +/- .01 for separation/penetration. Add cylinder rim versus box edge and skew poses with independent separating planes/interior point witnesses. |
| S-S | Radii .5 and .75, distance 1.25 touch, 1.5 gap .25, 1.0 depth .25. Orientations must not change outcomes. Coincident equal spheres depth 2 and deterministic +x. |
| S-C | Cylinder radius 1/half length 1; sphere radius .5 outside cap/rim. Sphere center `(1+.3,0,1+.4)` touches rim since hypot(.3,.4)=.5. Offsets scaled by 1.1 separate by .05; scaled .9 penetrate .05. Apply rigid transforms. Also side, cap center, sphere center inside cylinder and sphere enclosing a small cylinder. |
| C-C | Parallel axes z, radius .5 and .7, side distance 1.2 touches. Coaxial cylinders with half lengths .4/.6 touch at axial center distance 1; +/- .01 changes cap gap/depth. Tilt both using a common literal rotation. Add perpendicular axes and near-parallel cap/rim cases; use independently certified separating support planes for separated cases and an explicit point strictly inside both solids for overlaps. |

Common rigid transforms preserve signed distances and rotate normals for unique-normal fixtures. For shallow penetration also translate along the reported normal by depth+10*eps_geom and independently confirm separation; this is supplemental, not the sole depth oracle. Test duplicate vertices, line/triangle origin simplexes, nearly parallel features, tiny positive gaps, coincident COM, containment and near-zero search directions. Force low iteration limits to check diagnostic failures and immutable inputs; iteration exhaustion must never silently drop collisions.

For every one of five static bin prisms and every dynamic shape, construct isolated separated, touching, penetrating and rotated contacts at its interior face. Independently compute projected extrema: prism sum of absolute rotated half-axes, sphere radius, cylinder half-length*abs(axis dot normal)+radius*sqrt(1-(axis dot normal)^2). Confirm gaps/depths and a reaction on the dynamic body pointing into the interior for inner-face contact. With dynamic A and static B, canonical n points from dynamic toward the wall and the dynamic reaction is -n. Test wall/floor corner with two manifolds, edge/rim contacts and an object just above a wall end: finite walls must not behave as infinite planes. Exterior-side contact must use its actual outward geometry. Freeze static states and verify they remain identical.

## Manifolds and physical impulses

Flat cube on floor should expose four distinct support corners; rotating cube with zero centroid normal velocity but an approaching corner must receive appropriate angular/linear response. Upright cylinder on floor needs spread cap contacts (>=3 noncollinear); horizontal cylinder needs two separated generatrix endpoints. Two flat box faces should form a spread patch; test cap-cap contact, stale anchors, small sliding, feature changes and a separated returning pair. Retained anchors must satisfy geometric filters. Contact count alone is insufficient: verify patch area and residual normal corner velocities after the solve.

Hand impulse fixtures disable friction, gravity, pseudo correction and restitution cutoff as needed, using EXACT touching poses and one row:

- Equal 1 kg spheres, vA=(1,0,0), vB=(-1,0,0): K=2 kg^-1; e=1 gives j=2 N s and swapped velocities; e=0 gives j=1 and both zero. Both have no angular response.
- Masses 2 and 3 kg, vA=2 along +x, vB=0, e=.5: K=5/6, j=3.6; vA'=.2, vB'=1.2 m/s, total x momentum 4 kg m/s, kinetic energy changes from 4 to 2.2 J.
- One synthetic off-center contact: A m=2, Iz=4; B m=3, Iz=6; n=(1,0,0), arms both (0,1,0), vA=(1,0,0), vB=0, no spin. K=1/2+1/3+1/4+1/6=5/4; e=0 gives j=.8. Expect vAx=.6, vBx=4/15, wAz=.2, wBz=-2/15 and final relative contact speed zero. This validates both angular terms independently of narrow phase. Repeat rotated in world to expose body/world mistakes.
- Dynamic sphere against static floor m=2, vn=-3, e=.5: K=.5, j=9 N s, final vn=1.5, bin unchanged.
- Approaching versus separating and grazing rows: unilateral lambda>=0; separating point receives no impulse, mu=0 leaves tangential velocity unchanged. At low impact speeds below .5 m/s or old resting points, restitution target is zero. Confirm the configured threshold separately from e=1 conservation fixtures.
- Friction row: one 1 kg sphere at floor, radius 1, inertia .4, vx=1; imposed normal lambda=1, mu=.2. Tangential K=1+1/.4=3.5; uncapped magnitude 2/7 exceeds .2. Expect tangent impulse -.2 along x, vx=.8 and wz=-.5 rad/s from r=(0,-1,0) cross J=(-.2,0,0). Sticking case with smaller vx remains inside cone. Assert no pseudo lambda changes the friction bound.

## Momentum, energy and split impulse

At the fixed solve configuration, with no external loads or bin, verify total linear momentum and total angular momentum `sum(x cross m*v + R*I_body*R^T*w)` for equal/opposite common-point impulses within 1e-10 scaled budgets. For one frictionless row, expected kinetic change is `-(1-e^2)*vn_pre^2/(2*K)`; e=1 preserves kinetic energy, e=0 loses it. Friction should not add kinetic energy in isolated well-resolved fixtures beyond roundoff/iteration residual. Multi-contact restitution need not produce exact global conservation. Explicit free-flight nonspherical rotation uses refinement at h,h/2,h/4 over fixed duration rather than roundoff-level energy demands.

Initially stationary overlap fixture: two equal spheres at depth .01 m, no gravity/friction/restitution, h=1/240. Physical v,w start zero. With beta=.2, slop=.0001, no active cap, b_push=.4752 m/s; equal masses split relative correction .00198 m, leaving depth .00802 m after one step. Physical velocities and kinetic energy stay zero within 1e-12 scaled units. Run correction-only iterations over time: depth decreases toward slop without physical separation speed. Repeat stationary off-center prism/static-wall and two rotated prisms to check angular pseudo response without nonzero physical omega. Compare enabled/disabled correction. Verify just below/above slop, .01 m depth cap and final body translation/rotation caps; large-overlap correction is bounded, not instant full separation. Do not count potential-energy changes as kinetic injection.

## Resting, stacking and full example

Run 10 s at h=1/240, with h/2 comparison on shorter identical 2 s fixtures. Single prism, sphere and upright/horizontal cylinder resting on the floor: after settling with e=0, target max penetration <=2e-3 m, COM drift <=5e-3 m over final 2 s for symmetric fixtures, |v|<=.02 m/s, |w|<=.05 rad/s. Cylinder rolling is not tested as a stationary fixture when its setup contains tangential spin.

Stack three aligned unit cubes (m=1) and a separate stack of three upright cylinders (radius .4, height .6). After 10 s with e=0 and mu=.4, target maximum penetration <=5e-3 m, final COM heights within .01 m of geometric stack levels, and no collapse/NaN. Measure every-step penetration and contact residuals, not only the final image. Inspect sensitivity to 30/60 physical sweeps, 20/40 split sweeps and timestep refinement before accepting limits. Record any chatter or cap hits.

Full scene: exactly 30 dynamic bodies, 10 per shape and five unchanged static bin solids; default **2880 steps at h=1/480 (6 s)**, unit quaternion norm residual <=1e-12, synchronized clocks, actual nonzero pair/bin impulses with all shape categories participating. Penetration target remains <=.03 m transient and <=.01 m during final 2 s; report maxima/percentiles/worst pair/step. The former 240 Hz scene failed the transient target; its preserved evidence is development_240hz_tests.log, not accepted evidence. Require bodies inside the bin by the final window with finite velocities and no unexplained energy bursts; the CLI's escape field checks COM positions, so inspect full geometry as well. No teleportation, freezing, sleeping or removing objects to force acceptance. The automated 3 s smoke checks 1440 steps; the longer default CLI supplies separate settling evidence. Deterministic replay is tested on isolated worlds and initial scene generation; a second full-scene bitwise replay is not yet claimed.

## Part 5 complete-scene verification (2026-11-05)

Six full 2880-step trials (three/backend) completed sequentially in alternating
order, with exact complete canonical World/cache/StepReport equality, unchanged
physical/containment acceptance and independent saved audit replays. Evidence
is evidence/full_scene/comparison.json and full_serial_r0..2/full_parallel_r0..2/.
Four short evidence-harness tests passed before timing; no production change or
relaxed acceptance/tolerance. Retained realized JSON and trusted full replay
pickle permit rerunning the acceptance audit without physics. All six had finite
states, normalized quaternions, unchanged five static solids, actual body/body
and bin impulses, passing .03 m transient/.01 m last-two-second penetration and
full analytic extents within original bin tolerance. Residual motion is reported
in PROFILE. Full-scene verification is now complete for this fixed seed, while
broader stress/live GUI remain limitations. Prior Part 4/Part 3 records below
are preserved as historical scope and are not new reruns.

## Part 4 implemented parallel checks (2026-11-05)

Run `python -B -m hw7.parallel_checks <unique_label>` from the root. Results are
preserved under evidence/parallel_pilot/<label>.log/.json; this runner includes
geometry, solver and profiling regressions without overwriting Part 2/3 logs.

`tests/test_parallel.py` maps requirements to real Windows-spawn tests:

| Test | Requirement |
| --- | --- |
| all_six_shape_pairs_cache_and_enrich_through_workers | All six pair types at separated/touching/penetrating poses, exact manifolds with prior cache and both enrich flags |
| rotating_multistep_world_reports_cache_and_both_barriers | Six collision steps with spinning prisms/cylinder, exact World/cache/StepReports, 1/2/4 workers and 1/2/4 batch sizes, both barrier counters |
| pool_reuse_and_gather_under_forced_reverse_readiness | Same PIDs reused; force parent to consume later batches first, verify distinguishable results remain canonical |
| worker_error_propagates_and_cleans_without_fallback | Real worker kernel exception, parent error, no surviving owned worker or serial fallback |
| parent_interrupt_cleans_owned_workers | Interrupted parent dispatch aborts/joins its children |
| startup_failure_cleans_all_created_children | Readiness error cleans partially started pool |
| unexpected_worker_exit_is_error_and_cleans_other_workers | Dead worker/transport failure propagates and remaining children exit |
| invalid_settings_closed_pool_and_threshold | Reject invalid counts/batches/thresholds and inactive pool; documented threshold counters |
| stationary_split_exact_zero_energy | Exact serial/parallel worlds/reports and zero physical velocities/kinetic energy |

No existing physics tolerance is weakened. The old invalid-backend fixture now
uses `invalid` for zero-step simulate because `parallel` became supported; a
parallel step without its required live detector still fails validation.
Latest short suite: tests_v3, 48 tests passed, no failures/errors/skips. tests_v2
retains a transport-error type failure, fixed by converting broken pipe/EOF to
WorkerError after cleanup. The first 46-test suite also passed.

Genuine cached states at steps 389, 600 and 1440 require an explicit versioned
compatibility manifest, unchanged arithmetic hashes, payload SHA/options/seed/
cache lineage validation and exact replay of historical serial digests. Validate
full Python World/cache/report equality on 30-step serial/parallel intervals
before performance screening. Canonical dataclass value digests ignore pickle
object-sharing details while retaining every float and ordering; no tolerance.
At the Part 4 checkpoint the full 2880-step comparison was pending. Part 5 above
completed it exactly at dt=1/480 and 120/20 sweeps; older planning numbers below
are historical proposals.

## Serial and eventual parallel agreement (historical proposal)

Same exact initial state, dt, 2400 steps, pair/point ordering, iterations, friction and tolerances in both paths; include identical diagnostic work. Prefer parallel independent narrow-phase tasks with canonical result gather if profiling supports it: serial impulse order can then remain identical. Require exact candidate sets and contact feature/status sequences where arithmetic is unchanged, and short well-conditioned fixtures agree to `1e-10 + 1e-9*scale` in positions/velocities plus 1e-9 rad sign-invariant orientation distance. If a native kernel changes arithmetic, justify a revised budget using its eps_geom/solver residuals and reference fixtures before accepting it.

For the chaotic 10 s scene, still first try those trajectory tolerances; do not quietly relax them when contact branches diverge. Locate first divergence and distinguish a race/missing work from floating-point ties. If exact trajectories are impractical for a justified solver-order change, document that numerical method change, revalidate every analytic fixture and residual/penetration target, and predeclare aggregate budgets (e.g. total kinetic/potential energy relative difference <=1%, penetration maxima within .002 m, same count/containment/finite-state criteria). These provisional aggregate budgets cannot excuse a wrong impulse fixture. Retain per-step evidence and disclose branch differences. No independent duplicate-scene throughput benchmark qualifies as parallel agreement for the requested example.
