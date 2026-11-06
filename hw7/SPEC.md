# HW7 implementation specification — serial solver and parallel detection

Current implementation: Part 4 adds persistent spawned collision workers and
exact-equality checks; its protocol below precedes implementation. Part 3 serial
profiles, Part 4 intervals and Part 5's six exact accepted full-scene trials are
in PROFILE.md. Whole-example median speedup is 2.827684047x; submission history,
student reflection and verified packaging remain pending. Preserved Part 2 acceptance: six-second serial
scene, independent full-shape containment audit and Agg snapshots. Live GUI
playback is unverified; motion remains at 6 s. Earlier design history follows.

## Part 4 worker protocol (specified before implementation, 2026-11-05)

`ParallelDetector(workers=4, batch_size=4, serial_threshold=0)` owns persistent
`multiprocessing.get_context('spawn')` child processes and one duplex pipe per
worker. A context starts all workers, waits for a readiness handshake from each,
reuses them across both detection barriers and all steps, then sends shutdown
sentinels and joins. On startup/task failure or parent interruption, close pipes,
terminate only owned workers and join them; propagate the error, never fall back.
Unexpected EOF/dead workers are errors. Readiness and shutdown wall times are
separate from stepping. A simulation owns one context; explicit step callers may
provide an already active detector and own its lifecycle.

The parent computes the unchanged canonical SAP pairs. Each batch contains a
stable batch index, immutable tuples of `(body_a, body_b, previous_manifold)` for
only those pairs, the immutable Options and the original enrich flag. Pickling
preserves values without reconstructing/renormalizing states. Workers call the
unchanged importable narrow_phase and return one result per input pair plus PID
and pair count. No shared writable physics data exists. Consecutive canonical
pairs form batches of at most batch_size; dynamically dispatch the next batch
when any worker finishes, store results by batch index, then flatten in canonical
input order, dropping None exactly as serial. Never reorder manifold points.

The trial barrier receives previous cache and enrich=True; the corrected-pose
diagnostic barrier receives no previous cache and enrich=False, exactly as serial.
Cache anchor updates, kicks, physical/split impulses, pose updates, reports and
all dependent velocity mutations remain in the parent with unchanged order.
Empty pairs do no worker work; optional serial_threshold permits a documented
small-pair serial path. Default zero sends every nonempty set to real workers.
Record calls/pairs/batches, each barrier, worker PIDs and completion order.

Interfaces: detect(..., detector=None); step_world(..., backend='serial',
detector=None); simulate(..., backend='serial'|'parallel', workers=4, batch_size=4,
serial_threshold=0). A parallel step requires a live detector, avoiding accidental
per-step spawning. simulate creates/reuses/closes its own detector. CLI and the
new unprofiled measurement tool expose backend/workers/batch size/threshold.
Existing serial profiling tools remain for historical profiles.

Set OMP_NUM_THREADS, OPENBLAS_NUM_THREADS, MKL_NUM_THREADS and NUMEXPR_NUM_THREADS
to 1 before spawning; restore parent environment after startup. Workers set and
report these limits, with per-worker native temp directories under hw7/evidence/
parallel_pilot/native_tmp. Benchmarks launch fresh interpreters with the SAME
limits for the serial parent and parallel children before NumPy/SciPy imports.
These are requested environment limits, not an assertion about every native
library's actual thread count. No new dependency is required.

Historical checkpoints remain immutable and strict source validation stays the
default. Part 4 may explicitly supply an audited compatibility manifest mapping
the historical physics source ID to exact current hashes: all arithmetic/kernel/
solver/state/Hw5 files must be unchanged; only world dispatch and CLI interfaces
may differ. Verify payload hash/options/seed/cache lineage as before, record this
exception, and replay historical serial world/report digests before timing.
Any subsequent source mismatch rejects the manifest, rather than silently loading.

## Part 2 design corrections made before implementation

The Part 1 proposal assumes that origin-enclosing tetrahedron recovery is easy for a lower-rank GJK simplex. Exact face touching and symmetric cylinder contacts make that assumption impractical: a simplex can contain the origin on its boundary even during volumetric overlap. Keep analytic support GJK/EPA, but initialize EPA with a deterministic convex hull of support samples (simplex, coordinate and diagonal directions), using existing SciPy/Qhull for this initialization only. Expand any hull plane excluding the origin until enclosure or a certified supporting touching plane is found; subsequent EPA expansion is implemented here. No random Qhull joggling or geometry faceting. Qhull constructs an internal support polytope, not an approximation substituted for the actual cylinder. See [SciPy ConvexHull documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.ConvexHull.html).

Use exact point-to-solid closest-surface branches for sphere-prism and sphere-cylinder, in addition to sphere-sphere. These avoid iterative smooth-shape witnesses near tangency and handle containment directly; all non-sphere combinations retain analytic support GJK/EPA. For an exterior sphere center c, closest point b on the other solid defines n=(b-c)/distance, gap=distance-radius. For an interior center, choose its nearest boundary point and reverse that normal, with depth=distance_to_boundary+radius. Transform into the other's local frame for box clamping or finite-cylinder radial/axial clamping; handle inside ties by fixed axis order. This is an exact analytic accelerator, not a bounding-shape substitute. The remaining manifold policy and impulse equations are unchanged. SciPy/NumPy are already installed; declare them as runtime dependencies without installing anything.

Initial dynamic verification exposed two further design defects. Requiring BOTH box faces to align with the normal, and requiring every patch point to have nearly the deepest penetration, discards valid shallower contacts on tilted resting faces. Correct clipping uses an aligned reference face, the incident face MOST opposed to its normal (even tilted), and all clipped points with gap between the deepest gap minus geometric allowance and the contact envelope. Likewise feature seeds may have shallower valid depths. This is a manifold correction, not a relaxation of rest/stack test limits.

For a prism face that entirely contains the other solid's projected footprint in its two tangent coordinates, and whose plane the other COM is outside, use its exact plane normal and analytic support gap. The footprint test uses exact support extrema in the prism frame; it certifies a face-interior case, not general AABB collision. Cases near the finite face edges continue through GJK/EPA. This avoids small EPA normal errors creating false rolling acceleration on a horizontal cylinder.

An initial hand-maintained EPA horizon produced an inverted face during the three-cylinder stack check. Use deterministic Qhull reconstruction of the support polytope on EACH EPA expansion instead of maintaining horizon topology manually. Still query the true support until the specified advance tolerance; no fixed faceted shape or random joggling. This uses an existing dependency to remove a topology failure, with rebuild overhead to be measured later. No planned correctness tolerances were enlarged.

The horizontal-cylinder test further revealed that perturbing a complete two-point generatrix into a four-point patch invents a finite-width support patch and can cause artificial rolling. For an exact finite-face branch, use its fresh clipped/support-feature contacts and skip perturbation and stale curved-side anchors; a two-point line is complete. For cap-cap cylinder patches, also seed both caps' centers/cardinal rim points projected to the opposite cap plane and validated inside the finite analytic disk. Keep EPA/perturbation as fallback when those seeds do not span a patch. These changes improve contact geometry rather than widening resting/stacking acceptance limits.

Convergence diagnostics: the three-box fixture drifted outside its 5 mm horizontal budget at 30 physical sweeps; 60 reduced but did not eliminate drift (top COM displacement about 9.4 mm after 10 s). Increase the implemented default to 120 physical sweeps, alternating forward/reverse row traversal to reduce ordering bias while keeping deterministic fixed work. Pseudo sweeps likewise alternate forward/reverse. Keep the test limits unchanged. Tilted incident cylinder caps, like tilted incident box faces, must supply their full candidate feature set: when their cap axis is within 45 degrees of the reference normal, sample center/cardinal rim points on the selected cap rather than requiring both cap normals to align within 1e-4 rad. Each projected sample must still satisfy the actual disk/surface and depth tests. This changes manifold sampling, not cylinder collision geometry.

The first corrected two-second scene reached .03368 m transient penetration after correction, exceeding the .03 m target, then reduced to .00542 m. The old .01 m row depth cap allowed only .002 m correction per step regardless of a roughly .035 m impact overlap. Increase the row depth cap to .03 m (beta remains .2), permitting up to .006 m correction per row per step at the same dt; keep the .01 m per-body translation and .05 rad rotation limits and the .03 m transient test limit. Small-overlap analytical fixtures are unchanged because their depth is below either cap.

The subsequent 3 s smoke with 120 physical sweeps still reached .04087 m transient depth at h=1/240, although its final depth was .00457 m and the box stack passed. The original timestep is too coarse for this scene's simultaneous impacts at the existing .03 m target. Retain the same bodies/placements and acceptance limits, and use a fixed h=1/480 for the falling example. CLI default is 2880 steps (6 simulated seconds), spanning falling, collisions and a settling window; inspect the actual final motion rather than assuming it has stopped. Generic Options retains dt=1/240 for analytical/rest fixtures and accepts any positive finite dt. The 30-body smoke now covers 1440 steps at h=1/480 (still 3 s). This is a fixed timestep refinement, not adaptive stepping, and the profiling workload must use exactly the same revised scene and settings for serial/parallel.

## Inspected foundation and scope

Inspection covered `Hw5/SPEC.md`, `README.md`, `__init__.py`, `dynamics.py`, `geometry.py`, `spatial.py`, `rigid.py`, `joints.py`, all seven `test_*.py` modules, and `example.py`, `showcase.py`, `quaternion_example.py`, `damping_example.py`, `joints_example.py`.

| Existing API | Reuse and limits |
| --- | --- |
| `Prism(mass,a,b,c)`, `Sphere(mass,radius)`, `Cylinder(mass,radius,length)` | Immutable uniform solids with positive finite mass/dimensions; analytic diagonal COM inertia and full tensor. Prism dimensions are full lengths; cylinder symmetry axis is local z. `Prism.vertices()` supplies eight local corners. |
| `RigidState(position,velocity,orientation,omega,time,step_count)` | Immutable validated 13-component physical state plus clock metadata. `omega` is BODY-frame angular velocity. |
| `spatial.rotate`, `unrotate`, `multiply`, `quaternion`, `from_axis_angle`, `compose`, `to_matrix`, vector helpers | Hamilton quaternions `(w,x,y,z)`, active body-to-world rotations; normalized quaternion update; no normalization of angular velocity. |
| `rigid.angular_acceleration(shape,omega,torque_body)` | Explicit Euler angular acceleration including the gyroscopic term. |
| `rigid.advance(state,shape,dt,*,gravity,force,torque,force_point,restitution,ground,linear_damping,angular_damping)` | Returns `(state,contact_or_None)`; velocity-first translation, normalized Euler orientation. May obtain an unconstrained velocity kick with `ground=False` and discard its pose. Cannot use its endpoint ground correction for HW7. |
| `geometry.world_mesh(shape,position,orientation,segments=24)` | Reuse polygon meshes solely for display. Rendering maps world `(x,y,z)` to Matplotlib `(x,z,y)`. Adapt showcase drawing to 30 bodies and five bin solids; its three-color zip and independent-body simulation cannot be reused unchanged. |
| `geometry.ground_support`, `rigid.resolve_ground`, `contact_velocity` | Useful analytic reference for a single support and point velocity. Ground solver projects COM upward and applies one frictionless impact. It has no body-body detection, manifold, resting solve, or split impulse. |
| `joints.advance_system`, `Load`, inverse mass transformation | Useful frame/load conventions. Dense bilateral joint projection is not a unilateral contact solver. It limits assemblies to 16 bodies/96 rows and rejects joints with ground. Do not route 30-body contacts through it. |

HW5 tests contain independent inertia quadrature, Rodrigues rotations, hand contact impulses, free-flight refinement, damping, joint reaction/residual checks, and headless/snapshot smoke tests. They do not establish multi-body contact correctness. Existing examples show point translation, three independent ground-contact solids, rotation composition, damping, or small joint assemblies.

Python imports within Hw5 use only its sibling modules and the standard library, except optional Matplotlib imports for visualization. No production runtime import reaches root `state.py`, `contacts.py`, `integration.py`, `rendering.py`, hw4, or hw6; no runtime PDF/data-file reads were found. SPEC/README link historical files and images outside or alongside the source, which are documentation dependencies. The root aggregate requirements include PyVista/report packages that Hw5 physics does not require. HW7 will initially import `Hw5.geometry`, `Hw5.spatial`, and `Hw5.rigid` from the repository root. Their transitive source dependency is `Hw5.dynamics` and package `Hw5.__init__`; importing joints additionally pulls only Hw5 modules. No HW5 changes are required.

Part 2 adds world IDs/static colliders, oriented bounds/SAP, analytic supports and all six narrow-phase combinations, witnesses/manifolds/cache, unilateral physical/friction/split impulses, diagnostics, deterministic scene, renderer/CLI and independent tests under hw7/. Part 3 records representative serial profiles; Part 4 adds the dispatch backend and interval evidence. Part 5 completes matched full-scene baselines and exact acceptance; full cProfile/stage shares remain outside this step. Existing joint/ground APIs are not used as a multi-body solver.

Scope is discrete, convex, rigid-body collision in one bin. Exclude joints with contacts, moving/kinematic bin parts, concave bodies, soft bodies, rolling/torsional friction, CCD, adaptive stepping, sleeping, and GPU execution in the baseline. Shapes retain their analytic cylinder geometry and inertia. No AABB-only final collision test or sphere substitution is allowed.

## Units, state and implemented public interfaces

SI units: m, s, kg, N, N m, rad, kg m^2, N s. Right-handed world: +y up, gravity `(0,-9.81,0)` m/s^2, +z=x cross y. COM is local origin; R maps body to world. Public state remains `RigidState`; scratch solver arrays use WORLD angular velocity `w=R*omega`. Convert back using `omega=R^T*w` at the FINAL orientation. World inverse inertia is `W=R*diag(1/I)*R^T`. Static collider inverse mass and W are zero, with zero velocities; never construct an infinite-mass Hw5 solid. Static prisms can use unit-mass geometry solely for dimensions/mesh, with dynamics disabled by a separate static flag.

Interfaces (data in model.py, bounds/GJK/EPA in collision.py, narrow_phase in manifolds.py, stepping in world.py):

```text
Body(id: int, shape: Prism|Sphere|Cylinder, state: RigidState, static: bool=False)
World(bodies: tuple[Body,...], cache: tuple[Manifold,...]=(), time=0., step_count=0)
Options(dt=1/240, gravity=(0,-9.81,0), restitution=.15, friction=.4,
        restitution_threshold=.5, enable_split=True,
        velocity_iterations=120, split_iterations=20, ...tolerances below...)
make_scene(seed=7) -> World
world_aabb(body, padding=0) -> AABB(minimum, maximum)
sweep_and_prune(bodies, padding) -> tuple[(lower_id,higher_id),...]
narrow_phase(body_a, body_b, cached_manifold=None, options=None, *, enrich=True) -> Manifold|None
step_world(world, options, *, backend='serial') -> (new_world, StepReport)
simulate(world, options, steps, *, backend='serial', frame_stride=None) -> RunResult
falling_objects.main(argv=None) -> int
```

Manifold records pair IDs, a common normal, up to four ContactPoints, and a method string. Points store local surface anchors, common world impulse point, signed gap, computed depth property, and a matched flag; local-coordinate tuples provide deterministic point ordering rather than opaque feature IDs. StepReport separates per-point physical normal/tangent and push impulses, normal speed before/after, penetration before/after correction, correction-cap body count and newly created corrected pairs. Pair normal n points from A toward B in the sense that translating B in +n separates the bodies; containment may not follow COM direction. Gap `g=n dot (pB-pA)`, penetration `d=max(0,-g)`. Touching has g=0. Impulse point `p=(pA+pB)/2` and arms `rA=p-xA`, `rB=p-xB` are COMMON to the physical pair action, preserving equal/opposite torque about any origin at the solve pose. Surface anchors are retained separately for contact refresh. Swapping ordered arguments flips n and swaps anchors.

Validate unique IDs, supported shape types, finite states/options, synchronized clocks, positive dt, nonnegative friction, restitution in [0,1], and positive integer iteration counts. Invalid/nonfinite results fail before returning; caller input and cache remain unchanged. No global mutable cache or RNG. Deterministic serial replay on the same runtime is required, not cross-platform bitwise identity.

## Exactly 30 finite-mass objects and stationary bin

Dynamic IDs 0..29 contain ten of each shape. For i=0..29 define `k=i//3`, `s=i%3`, mass `m=.8+.1*(i%7)` kg. Use:

- s=0: `Prism(m,.38+.02*(k%4),.32+.03*(k%3),.40+.02*(k%5))`.
- s=1: `Sphere(m,.20+.015*(k%4))`.
- s=2: `Cylinder(m,.18+.01*(k%4),.40+.03*(k%5))`.

Placement indices `layer=i//6`, `col=i%3`, `row=(i//3)%2`; COM `((col-1)*.9,1.4+.9*layer,(row-.5)*.95)` m. Initial linear velocity is zero; body omega `(.12*((i%3)-1),.08*((i%5)-2),.10*((i%4)-1))` rad/s. Use a private `random.Random(7)` by default, drawing exactly one angle `uniform(-.6,.6)` per body in ID order and applying `from_axis_angle((1+(i%2),2,1+(i%3)),angle)`. Seed override changes only these angles. Save the realized initial states in later evidence to avoid reliance on future RNG versions. All enclosing-sphere diameters are below the grid spacings; independently check no initial overlaps and positive bin clearance.

The open-top bin has interior x,z in [-2,2], floor top y=0 and rim y=2.4 m. Five stationary axis-aligned prism colliders, IDs 30..34:

| ID | Center (m) | Full dimensions (m) |
| --- | --- | --- |
| 30 floor | (0,-.1,0) | (4.4,.2,4.4) |
| 31 left | (-2.1,1.2,0) | (.2,2.4,4.4) |
| 32 right | (2.1,1.2,0) | (.2,2.4,4.4) |
| 33 back | (0,1.2,-2.1) | (4,2.4,.2) |
| 34 front | (0,1.2,2.1) | (4,2.4,.2) |

All five orientations are identity. Static colliders are excluded from the count of 30 finite-mass simulated bodies. Their edge seams and exterior faces are real geometry, not infinite half-spaces; objects can escape over the rim. Implemented example defaults to 6 s (2880 steps at h=1/480), saved render rate 30 Hz. No live wall clock controls physics.

## Rotation-aware bounds and sweep and prune

For center x, extent along unit world axis e is: prism `sum_j |R_ej|*half_length_j`; sphere radius; cylinder `L/2*|u_e|+radius*sqrt(max(0,1-u_e^2))`, u=R*(0,0,1). AABB is center +/- extents, expanded outward by contact envelope `eps_contact` on EACH side. This conservatively includes all geometric contacts and near contacts admitted below. Bounds cover static bin prisms as well.

Sweep world x. Sort endpoints by `(coordinate,kind,id)`, with start before end at equal coordinates. Maintain active IDs in sorted order; on start compare closed y/z intervals using `<=` overlap. Include touching x,y,z intervals. Exclude static-static pairs only; dynamic-static and dynamic-dynamic pairs remain. Canonicalize IDs, deduplicate, lexicographically sort final candidates. Static endpoints may be cached; dynamic bounds update every substep. No sleeping or size-based pair pruning. Straight full endpoint sort is the baseline; temporal insertion sort may be evaluated later. Cost O(N log N + overlapping sweep comparisons), worst case O(N^2).

## Chosen narrow phase: analytic support GJK/EPA with persistent manifolds

Use exact convex support functions, distance GJK with original-shape witnesses, then 3D EPA for non-sphere overlap, with the exact sphere and certified finite-face branches documented above. This design supports prism-prism, prism-sphere, prism-cylinder, sphere-sphere, sphere-cylinder, cylinder-cylinder; bin contacts use those same routines against static prisms. AABBs only select candidates. Mesh tessellation never determines collision.

For local direction a=R^T*d, support is prism `(sign(a_j)*half_j)`; sphere `radius*a/|a|`; cylinder `(radius*a_x/rho,radius*a_y/rho,sign(a_z)*L/2)` with rho=hypot(a_x,a_y). Zero prism coordinates choose +half deterministically; zero cylinder radial direction chooses `(radius,0)`, zero axial coefficient chooses +L/2. These tied choices are true extrema. Exactly zero overall direction uses world +x. Use scaled normalization; do not threshold away a nonzero coefficient when it would invalidate extremality.

Minkowski support `S(d)=support_A(d)-support_B(-d)` stores both witnesses. Reduce point/segment/triangle/tetrahedron simplexes by enumerating their faces and computing closest-origin barycentric coordinates. Triangle barycentrics use cross-product area formulas to avoid cancellation in near-collinear Gram determinants. GJK returns distance witnesses when support advance <=eps_geom or support repeats; if the simplex distance <=eps_geom, initialize EPA using simplex plus six coordinate/eight diagonal support directions and certify enclosure by hull half-spaces. Supporting boundary planes with support<=eps_geom certify touch. Ambiguous enclosure failure is a reported CollisionError, never silently 'separated'. A positive near-contact gap may be retained, with zero penetration correction depth.

EPA repeatedly expands the nearest hull face using its true support direction and rebuilds the outward triangulated hull using scipy.spatial.ConvexHull. Stop when support advance over face distance <=eps_geom. Recover witnesses from the closest coplanar triangle's barycentrics; orient n so B moves outward. For symmetric overlaps pick face ties by vertex IDs. Coincident spheres use n=+x in canonical pair order. Initial search direction is COM difference, falling back to +x. GJK cap 64, enclosure cap 16, EPA cap 128 expansions/512 faces; raise CollisionError on exhaustion, duplicate without convergence, or hull failure. No silent fallback or automatic iteration-limit increase. Deep containment, near-parallel cylinder rims, and equal-minimum normals require verification.

Use enclosing radius `r_bound`: prism half-diagonal, sphere radius, cylinder `hypot(radius,length/2)`. For a pair, length scale `ell=max(1 m,2*r_bound_A,2*r_bound_B)`; `eps_geom=Options.geometry_relative*ell` (default 1e-8), `eps_contact=contact_factor*eps_geom` (factor 5). GJK duplicate distance .01*eps_geom, EPA duplicate .001*eps_geom. Affine simplex math has roundoff guards: squared edge <1e-28 m^2; squared triangle cross product <=1e-28 times product of squared edge lengths; tetra determinant <1e-14 times product of edge lengths; barycentric feasibility -1e-12. These are floating-point degeneracy guards, not enlarged collision shells. Each AABB uses its own scale for padding. Computations use double precision world coordinates, so huge COM offsets and extreme scales are unsupported. Treat abs(g)<=eps_contact as touching; retain small positive gaps for continuity, but physical rows only permit g<=eps_geom, and pseudo rows only d>slop. No predictive positive-gap impulse beyond that roundoff envelope.

### Manifold generation, refresh and limitations

One GJK/EPA witness is insufficient for resting faces. Except for finite-face branches, keep local anchor pairs between steps, retransform them, and retain only if normal change <=5 degrees, normal separation <=`break_distance=1e-4*ell`, tangential anchor drift <=break_distance, and both anchors remain on analytic surfaces within break_distance. Recompute g; positive-gap cache points cannot exert forces outside eps_geom. Fresh narrow phase must first confirm a pair within the envelope. Finite-face contacts use fresh clipping/features to avoid stale curved-side anchors. Refresh geometry only: no physical or pseudo impulse warm starting; every step starts accumulated impulses at zero.

Enrich each fresh manifold as follows:

1. Prism-prism contacts use a reference face aligned within face_angle=1e-4 rad and the MOST opposed incident face, even tilted. Clip against reference side planes; accept point gaps from deepest_gap-break_distance through eps_contact. Both qualifying reference orientations may contribute; final coordinate ordering/reduction is deterministic. Otherwise retain the edge/vertex witness and valid enrichment.
2. For nonspherical, non-finite-face pairs with fewer than four points after seeding/reduction, perform four additional support queries with the smaller-radius body temporarily rotated about COM by +/-theta about two deterministic tangents. `theta=min(.01,break_distance/r_bound)` rad. Map witnesses back through local coordinates to ORIGINAL poses; retain original n and recompute depths, tangent/surface validity. These perturbation points must agree with deepest gap within break_distance. Never integrate a perturbed pose. Skip this for a complete finite-face line/patch.
3. For a prism face, seed support features: tied prism corners; cap center/four cardinal rim points; radial-generatrix endpoints. For cylinder cap-cap contacts, select an aligned reference cap and incident cap within incident_cap_angle=pi/4; project center/cardinal samples to the actual reference plane and validate inside its analytic disk. Admit shallower valid gaps through eps_contact, not just equally deep points. Finite prism rectangles and cylinder disks filter the samples. Tilted cylinder rims fall back to analytic witnesses, persistence and perturbation. Spheres keep a single geometric contact; cache can mark its restitution match.
4. Merge world contact points within break_distance/2. Reduce to at most four: deepest; farthest tangential point; largest projected triangle; largest four-point projected convex-hull area, breaking ties by sorted local coordinates. Sort final points by local anchor tuples. Do not merge distinct bin walls.

Perturbation and four-point reduction approximate the contact patch. They may underresolve cap-cap contacts, change features, or leave some corners unsupported on the first step. If stacking fixtures fail, fix manifold enrichment or increase documented iterations before changing performance workloads. No claim of perfectly stable arbitrary stacking. This strategy uses analytic cylinders for detection and sampled points only for the manifold.

## Physical impulses and friction

At fixed solve poses, let `u=(vB+wB cross rB)-(vA+wA cross rA)` and `vn=n dot u` (negative approaching). For any direction t define

```text
K(t)=inv_mA+inv_mB
     +(rA cross t) dot WA*(rA cross t)
     +(rB cross t) dot WB*(rB cross t).
```

Normal row update: `lambda_new=max(0,lambda_old+(b_rest-vn)/K(n))`; apply ONLY delta lambda with `J=delta_lambda*n`, `vA-=inv_mA*J`, `wA-=WA*(rA cross J)`, and opposite plus updates for B. Restitution target is frozen from the pre-solve kicked velocities: `b_rest=-e*vn_pre` for a newly active contact with `vn_pre<-restitution_threshold`, else zero; threshold defaults to .5 m/s and may be set to zero in analytic tests. A contact is newly active if no touching/penetrating point matched it last step. This prevents repeated restitution on resting cached contacts; disappearing and reentering contacts can bounce again. No penetration bias enters this physical row. Reject nonpositive/nonfinite K for a dynamic pair; skip static-static before here.

Default friction is Coulomb mu=.4 for all pairs. Deterministic orthonormal tangents come from the least-aligned coordinate axis. Solve the 2x2 tangential effective-mass system with entries `K_jk=(inv_mA+inv_mB)*(tj dot tk)+sum_i (ri cross tj) dot Wi*(ri cross tk)`, compute accumulated trial tangent impulse cancelling tangential u, then project its 2-vector to the disk `|lambda_t|<=mu*lambda_n`. Apply the delta impulse at the same world point. This is one approximate sticking/sliding coefficient, with no rolling/torsional model. Friction uses only physical normal lambda, never pseudo lambda. Fixed 120 physical sweeps (configurable), normal then tangent rows per point, with alternating canonical/reversed row traversal. Report row normal speed after solving; do not hide convergence-dependent iteration changes.

## Split impulse and time stepping

Pseudo world velocities `(vhat,what)` start at zero each step, separate from `(v,w)`; pseudo accumulated lambdas also start zero. At the endpoint contact pose, for depth d:

```text
slop=1e-4 m; beta=.2; correction_depth_limit=.03 m
b_push = beta*min(max(d-slop,0),correction_depth_limit)/h
lambda_hat_new=max(0,lambda_hat_old+(b_push-vn_hat)/K(n))
```

Activate only for d>slop and enable_split=True. Tests may disable split correction without changing the physical solver. `vn_hat` uses pseudo velocities and the same Jacobian/world inertia. Apply pseudo delta normal impulses to vhat/what only, in 20 fixed alternating forward/reverse sweeps; no restitution or tangential pseudo rows. At h=1/240 the maximum row target is 1.44 m/s. The depth cap bounds each row target, not the sum of many contacts. Bound final per-body correction by a common scale on that body's vhat/what so `h*|vhat|<=.01 m` and `h*|what|<=.05 rad`; report any cap and measure resulting penetration. Such caps can reduce correction and need additional steps. They are a protective numerical choice, not a conservation mechanism.

Implemented endpoint order, explicitly differing from old-pose joint projection:

1. Validate/synchronize. Compute free physical velocity kick with external gravity and body Euler gyroscopic acceleration at the OLD orientation, using `rigid.advance(...,ground=False)` and retaining its kicked v/body omega. Baseline has no other loads or damping. Convert kicked omega to world using OLD R.
2. Predict endpoint `x_trial=x+h*v_kick`; `q_trial=normalize(q+h/2*q*(0,omega_kick))`. Keep kicked world w when changing orientation and express scratch omega at q_trial using its inverse. Ignore advance's omega representation at its returned orientation. Clocks advance only once.
3. Build trial-pose AABBs, sweep and prune, fresh narrow phase plus refresh/enrichment. Use q_trial to compute W and lever arms. Solve physical contact/friction impulses at fixed trial poses with pre-solve restitution targets. This corrects endpoint velocities; do not reintegrate the whole timestep a second time after an impact.
4. Solve separate pseudo rows at the same trial poses. Set `x_new=x_trial+h*vhat`. Apply world rotation increment `q_new=from_axis_angle(what, h*|what|)*q_trial` (identity if zero), normalize. Retain physical world v and w from step 3; convert w to stored BODY omega using q_new. Do not add pseudo velocities to them. Discard pseudo velocities and pseudo lambdas.
5. Re-evaluate contact depths/bounds at corrected poses for diagnostics/cache refresh, without another physical solve or timestep. Newly created contacts due to correction are handled next step and reported. Return new immutable states, cache, report and synchronized clocks. Render sampled states only.

Holding physical world w through pose correction prevents a coordinate-change velocity artifact. Rotating an anisotropic inertia at nonzero w can still change rotational kinetic energy; stationary overlap with v=w=0 must remain exactly stationary in physical velocities. Position correction can change potential energy and angular momentum about a fixed origin. Do not promise exact conservation for corrected configurations. In isolated impact tests disable correction or start at exact touching; use momentum and energy appropriate to that fixed solve pose.

Endpoint detection can miss fast objects crossing thin geometry between steps; this is not CCD. Collisions affect next-step drift, and energy/trajectory accuracy is generally first order. Default dt and scene speed are modest, but require penetration/refinement checks; no timestep stability theorem is claimed. Extreme aspect/mass ratios, deep tangled initial overlaps, large angular steps, and GJK/EPA nonconvergence can fail explicitly.

## Optional serial profiling interface (Part 3)

`solver.solve_contacts(bodies,manifolds,opts,*,observer=None)` accepts an optional phase callback. It emits `solver_setup`, `physical_impulses`, `split_impulses`, `solver_reports`, then None. With no observer, the existing fixed-order arithmetic, iteration counts, inputs and outputs are unchanged. Timing notifications occur only at phase boundaries, never inside impulse arithmetic. Profiling-only `Telemetry` temporarily wraps module bindings for step, free kick, detection, AABBs/SAP, manifolds and narrow kernel, restoring them on exit. It is a single-threaded measurement context, not a physics backend or thread-safe application interface. Exclusive stage times partition the measured step; inclusive times are nested and must not be added together.

`python -B -m hw7.profiling` provides inventory, genuine-state preparation, measurement and exact instrumentation validation commands. Checkpoints include the full World/contact cache, seed, options, content hash and source hashes, and may be loaded only from trusted local profiling evidence. A budgeted/failed run is marked incomplete and returns nonzero; partial journals and cProfile dumps are retained when control returns normally. Hard external termination can preserve only the latest journal/checkpoint. Profiling temporaries, including SciPy/Qhull error streams, are confined to hw7/evidence/profile_serial/native_tmp. See PROFILE for measurement scope, preparation costs and actual results. No collision geometry, solver policy, tolerance or physical state representation changes in Part 3.

## Primary technical sources and attribution

Accessed 2026-11-04. These support algorithm families; actual validation is recorded in LOG.md. Settings, bin/scene, failure policy, tolerances, no-warm-start policy and integration order above are HW7 design choices. Source code was written here, not copied from Bullet; SciPy is an external runtime dependency with its own license.

- [Bullet GJK/EPA implementation](https://github.com/bulletphysics/bullet3/blob/master/src/BulletCollision/NarrowPhaseCollision/btGjkEpa2.cpp): support simplexes, enclosing-origin initialization, EPA expansion and witness recovery. This specification uses an independent Python implementation and explicit failure reporting.
- [Erin Catto, Contact Manifolds, GDC 2007](https://box2d.org/files/ErinCatto_ContactManifolds_GDC2007.pdf): witness/manifold distinction, face clipping, coherence and approximate multi-point patches. Its illustrated polygon cases do not by themselves implement 3D curved-cylinder manifolds.
- [Bullet convex-convex dispatch](https://raw.githubusercontent.com/bulletphysics/bullet3/master/src/BulletCollision/CollisionDispatch/btConvexConvexAlgorithm.cpp): perturbed contact queries and mapping witnesses back to original transforms. Four tangent perturbations and the validity filters above are our choices.
- [Bullet persistent manifold](https://github.com/bulletphysics/bullet3/blob/master/src/BulletCollision/NarrowPhaseCollision/btPersistentManifold.cpp): refreshing local anchors and retaining deepest/spread points. Our exact reduction/matching rules are specified above.
- [Bullet sequential impulse solver](https://github.com/bulletphysics/bullet3/blob/master/src/BulletDynamics/ConstraintSolver/btSequentialImpulseConstraintSolver.cpp): separate physical and push/turn velocities and unilateral accumulated split impulses. Our thresholds, caps, friction policy and iteration counts are not Bullet defaults.

Implementation validation is defined in [TEST_PLAN.md](TEST_PLAN.md); performance work is gated by [PROFILE.md](PROFILE.md). Packaging must contain every imported source dependency, declared third-party runtime requirements, and the repository's real root `.git` history. No nested repository, reconstructed history, or unrelated-file cleanup.
