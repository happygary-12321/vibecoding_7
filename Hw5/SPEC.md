# HW5 models: Parts 1-5

The unchanged Part 1 API implements free-flight point-mass translation in three dimensions.
That API remains point-mass translation only, not rigid-body dynamics. It has no
geometry, orientation, angular velocity, torque, quaternion, damping or contact.
The rigid-body and coupled-joint APIs are specified below. HW3 and HW4 are separate.

## Units and coordinates

Use SI: position in metres, time/timestep in seconds, velocity in m/s, mass
in kg, acceleration in m/s², and applied force in newtons. The inertial world
frame is right-handed: +x right, +y up, +z given by x cross y (toward the viewer
when x is screen-right and y screen-up). The origin is arbitrary; there are no
walls. Default gravity is (0, -9.81, 0) m/s², pointing downward along -y.
Custom finite three-component gravity vectors, including zero, are supported.

## State and parameters

`State(position, velocity, time=0, step_count=0)` is an immutable per-body
snapshot. Position and velocity each have three components, defaulting to zero.
`Parameters(mass=1, dt=1/240, gravity=(0,-9.81,0))` is immutable.
Mass and timestep must be positive finite numbers. Numeric inputs accept Python
int/float, excluding bool, and normalize to finite float; unrepresentable huge
integers are rejected. Vectors accept only lists/tuples of length three and are
copied to immutable tuples. Strings, complex values and nonfinite values fail.
Time is finite and nonnegative; step_count is an exact nonnegative Python int.
Explicit input errors raise ValueError. Circumventing frozen dataclasses using
low-level Python mutation is outside the API contract.

## Equations and interface

`step(state, parameters, force=(0,0,0)) -> State` implements componentwise:

```text
dx/dt = v
dv/dt = g + F/m
a_n = g + F_n/m
v_(n+1) = v_n + a_n*h
x_(n+1) = x_n + v_(n+1)*h
```

This is velocity-first semi-implicit Euler, matching HW3's integration order.
Gravity is acceleration, not force; do not divide it by mass. Applied force
excludes gravity. Force is constant over this one step only, is not stored,
and defaults to zero on the next call. Repeat it explicitly for persistent load.

A successful step returns a new snapshot, increments step_count exactly once,
and adds h to time. Fresh states start at t=0/count=0. For fixed h, elapsed
time equals n*h up to floating-point accumulation. Variable h is allowed:
time is the sum of accepted durations, not count times the most recent h.
Resume metadata may be supplied independently; no prior history is inferred.
Time must advance representably. Nonfinite acceleration, velocity, position,
or time is rejected with ValueError before returning a new state. Inputs are
never mutated, on success or failure. Finite but extreme inputs may therefore
fail due to floating-point limits; representability does not guarantee accuracy.

Separate state/parameter/force values permit callers to step multiple independent
bodies without globals or shared accumulators. There is no multi-body world,
interaction solver, scheduler, or future-feature scaffold in Part 1.

## Historical future requirements (Part 1 lecture supplement, 2026-10-22)

Verified against [MECE 4990 Lecture 6.pdf](../MECE%204990%20Lecture%206.pdf),
using 1-based PDF pages. These are requirements for later work, not implemented
features or completed oracles in Part 1.

- Page 35, "3D Rigid Body Dynamics": the future physical state has 13
  components: position (3), velocity (3), quaternion (4), angular velocity (3).
  Current Part 1 has only the first six physical components. Simulation time
  and step count are additional metadata, not part of the 13 physical components.
  Future rotation must use body-frame Euler dynamics
  `I * omega_dot + omega cross (I * omega) = M`, with body-frame inertia I
  constant and torque/angular velocity expressed consistently in that frame.
- Page 36, "3D Rigid Body Dynamics: Oracles": verify torque-free angular
  momentum and kinetic energy, and verify that translating the entire body
  leaves its rotation unchanged. These checks require rotational state and are
  not satisfied by current point-mass momentum or Galilean-boost tests.
- Page 37, "Geometries": implement solid rectangular prism, solid sphere and
  solid cylinder, each with center of mass, inertia tensor and a representation
  for ground contact. Ground contact will be needed later; multi-body collision
  detection is not required by these slides. Part 1 remains contact-free.
- Page 38, "Geometries: Oracles": verify inertia numerically by sampling points
  inside each solid and comparing with the analytical formula; test geometric
  symmetry, including the cube's equal inertia about every axis through its
  center. No geometry-specific oracle is complete in Part 1.

Quaternion rotations, damping and revolute/prismatic/fixed joints from the full
assignment remain future work too. No Parts 2-5 systems are added by this supplement.

## Part 2 specification (written before implementation, 2026-10-22)

The preceding future-status statements describe the Part 1 supplement. Part 2
now implements the three solids, rigid-body free flight and ground contact via
`Hw5.rigid`; the exports in `Hw5` and `Hw5.dynamics` retain Part 1 behavior.
Minimal quaternion operations are a dependency here, not completion of Part 3.
At Part 2, damping, joints and body-body collisions were unimplemented.
Part 4 below adds optional damping and Part 5 adds joints; body-body collisions
remain absent.

### Uniform solids, body coordinates and inertia

All solids have positive finite mass in kg and dimensions in metres, uniform
density, center of mass/body origin (0,0,0), and principal axes aligned with
body x,y,z. Shapes are immutable. Products of inertia at COM are zero.
Inertia has units kg m^2; `inertia` returns the diagonal entries and
`inertia_tensor` the full 3 by 3 matrix. Numerically unrepresentable/zero inertia
is rejected even when input dimensions are finite.

| Shape | Dimensions/convention | Diagonal COM inertia |
| --- | --- | --- |
| Prism | full lengths a,b,c along body x,y,z | m/12 * (b^2+c^2, a^2+c^2, a^2+b^2) |
| Sphere | radius R | (2*m*R^2/5) * (1,1,1) |
| Cylinder | radius R, full length L; symmetry axis body z | (m*(3*R^2+L^2)/12, m*(3*R^2+L^2)/12, m*R^2/2) |

### State, frames and loads

`RigidState` contains world COM position/velocity, orientation q=(w,x,y,z),
and body angular velocity omega in rad/s: 13 physical components. Time and
step_count are additional metadata with the same conventions as Part 1.
Quaternion multiplication is Hamilton; q maps body vectors to world by
q*(0,v_body)*conjugate(q). Input finite nonzero quaternions are normalized;
zero quaternions fail. Angular velocity is NEVER normalized.
Public entry points validate before returning; immutable inputs are unchanged
on failure, including arithmetic overflow. Frozen-object bypass is unsupported.

`advance(state, shape, dt, gravity, force, torque, force_point, restitution,
ground)` returns `(new_state, contact_or_None)`. Defaults: gravity=(0,-9.81,0),
force=torque=0, force_point=None (COM), restitution=.5, ground=True.
Forces are world N; explicit torques are world N m about COM. An optional
world application point adds `(force_point-position) cross force` to torque.
Gravity acts at COM. Loads last one call only. Parameters and load vectors must
be finite, dt positive, restitution in [0,1], and ground an actual bool.

### Numerical order

At the initial orientation transform total world torque to body coordinates.
Euler's equation is `I*omega_dot + omega cross (I*omega) = torque_body`.
Use explicit omega update, then `q_trial=q + h/2 * q*(0,omega_new)` and normalize
q_trial. Update translation velocity-first exactly as Part 1. Advance clock and
count once, then resolve ground at the endpoint if enabled. Smooth free-flight
global accuracy is first order; quaternion projection controls norm, not energy
or momentum. No normalization/projection of omega or conserved quantities.
Off-center load lever arms and torque transforms use the start of the step.
Large steps can be unstable; finite-result rejection is not an accuracy guarantee.

### Geometry and frictionless ground y=0

World geometry is COM plus rotated body geometry. Prism rendering uses its
eight actual vertices. Sphere/cylinder rendering uses polygon meshes only for
display; collision uses analytic support with documented tie tolerances, NOT the visual tessellation or a
bounding sphere. Cylinder support minimizes y over its finite solid: choose
the lower end along its oriented axis plus the lowest radial rim direction.
When a coefficient is zero, choose the center of that tied direction. Prism
support averages vertices tied within 1e-12 m of the minimum; this is one
resultant point for a face/edge, not a multi-contact solver. Near-ties introduce
that geometric tolerance; cylinder ties within 1e-14 in unit direction use zero.
Sphere support is directly below COM, independent of orientation.

`ground_support` returns world lever arm r and clearance y_COM+r_y.
Clearance <=0 is touching/penetrating. Translate COM upward by -clearance,
without changing orientation, and compute contact normal speed
`vn = (v_COM + omega_world cross r) dot n`, n=(0,1,0).
For vn<0 apply J=j*n with
`j=-(1+e)*vn / (1/m + (r cross n) dot I_world^-1*(r cross n))`.
Update v by J/m and omega_body by I_body^-1*R^T*(r cross J).
For vn>=0 apply no impact impulse even if COM is moving inward. Penetration
correction still applies. `resolve_ground` does not advance time/count.
The contact record includes pre/post normal speed, scalar impulse, lever arm,
and correction depth. No tangential impulse/friction is applied.

All simultaneous lowest points are reduced to the selected resultant. A tied
face can have rotationally approaching corners despite a separating centroid;
this deliberately limited model will not resolve those individual contacts.
It can chatter, tip inaccurately, inject potential energy through projection,
and miss impacts occurring between endpoints. There is no resting constraint,
continuous collision detection, stacking, or general contact manifold solver.
Post-impulse restitution is enforced at the selected point only. Tests must
make these limitations visible rather than assert general nonpenetration over
arbitrary timesteps. Ground is optional for conservation/free-flight tests.

## Part 3 quaternion contract (specified before implementation, 2026-10-22)

This extends `Hw5.spatial` using the same normalized Hamilton representation
as Part 2. Coordinate handedness is right-handed, components `(w,x,y,z)`, angles
are radians, and rotations are active. A quaternion q rotates a body-coordinate
column vector into world coordinates via `q*(0,v)*conjugate(q)`. The inverse
maps world to body. q and -q represent the same orientation; raw components
need not be equal. No quaternion sign canonicalization is promised.

`compose(after, before)` returns normalized `after*before`: apply `before`
first, then `after`, both interpreted as active rotations in the common frame.
Thus a fixed-world x rotation followed by fixed-world z uses `compose(qz,qx)`.
`multiply` remains the algebraic Hamilton product, also used with non-unit
pure angular-velocity quaternions; it must not normalize its operands/result.
Public rotation helpers validate and copy inputs; caller-owned sequences are
never changed. `conjugate(q)` and `inverse(q)` normalize the rotation first,
then negate its vector part; they are rotation inverses, not arbitrary-quaternion
algebraic inversion APIs. `rotate`/`unrotate` preserve vector magnitude within
roundoff and never normalize the vector or angular velocity.

`from_axis_angle(axis, angle)` accepts a finite three-component list/tuple and
a finite int/float angle excluding bool. Axis magnitude is irrelevant; normalize
it robustly by scaling. An exactly zero angle returns identity, including with a
zero axis; all input shape/type/finiteness checks still run. A zero axis with
any nonzero angle is invalid (even a multiple of 2*pi). Small nonzero angles
are retained using sin(angle/2), without an epsilon cutoff. Very large finite
angles are allowed, with ordinary floating-point trigonometric range-reduction
limits; subnormal half-angles may underflow. No accuracy guarantee at extremes.

`to_matrix(q)` returns an immutable 3x3 rotation matrix R acting on columns:
`v_world=R*v_body`; `R^T` is world-to-body and `R(after*before)=R(after)R(before)`.
`from_matrix(R)` accepts only finite 3x3 lists/tuples of numbers. It requires
every entry of `R^T*R-Identity` and `det(R)-1` to have absolute magnitude <=1e-10.
Reflections, scaling, material shear and malformed/nonfinite input fail with
ValueError. This fixed 1e-10 threshold accepts near-rotations within the stated
residual bounds; it is not restricted to machine roundoff. No arbitrary matrix
projection/orthogonalization is performed. The recovered quaternion is normalized,
so a tolerated near-rotation can differ from the recovered rotation by an amount
governed by the documented 1e-10 matrix acceptance tolerance, not necessarily
machine roundoff alone; it is
not promised to reproduce its nonorthogonal entries exactly. Largest-component
extraction avoids division by sin(theta) or by a vanishing scalar part at pi.

`angular_distance(q,p)` returns the principal orientation angle in [0,pi].
Normalize both, let d=min(||q-p||,||q+p||), s=max of those norms, and return
`4*atan2(d,s)`. This sign-invariant metric retains small errors without the
near-identity cancellation of acos(abs(dot(q,p))). For unit quaternions,
d=2*sin(theta/4), s=2*cos(theta/4). Arguments are copied and validated.

Body-frame kinematics remain `q_dot=.5*q*(0,omega_body)`. The existing normalized
Euler update uses omega after the Euler rotational-dynamics step, then projects
q to unit norm. General smooth rotational trajectories have first-order global
accuracy. Constant-axis spin is a special case with discrete angle per step
`2*atan(h*|omega|/2)`, hence O(h^2) accumulated phase error at fixed T for fixed
omega. Unit norm does not ensure correct phase or conserved energy/momentum.
Euler's rigid-body rotational equations describe dynamics, not Euler-angle
orientation coordinates; no Euler-angle system is introduced. The integrator
and contact solver are unchanged. Damping was future work at Part 3 and is
specified below for Part 4; joints were future work at Part 3 and are added in Part 5.

## Part 4 damping contract (specified before implementation, 2026-10-22)

Historical Parts 1-3 statements above describe those stages. Rigid-body
`advance` now accepts optional keyword-only `linear_damping=0.0` (c) and
`angular_damping=0.0` (c_omega). Both must be nonnegative finite Python int/float
scalars, excluding bool; invalid values raise ValueError without changing inputs.
The Part 1 point-mass API remains undamped and unchanged. Joints were future work
at Part 4; see the Part 5 assembly API below.

Linear damping is the physical world force `F_d=-c*v_world` at COM, with
c in N s/m. It has no moment about COM. Angular damping is the physical
body-frame torque `tau_d=-c_omega*omega_body`, with c_omega in N m s/rad.
The stationary environment defines the drag reference frame; the undamped
Galilean-boost relation does not apply with this drag. External force/torque
and off-center force-point inputs retain their existing one-call lifetime.
Damping coefficients are also supplied per call and must be repeated to persist.
Angular velocity and vector magnitudes are never normalized or silently clamped.

```text
m*v_dot = m*g + F_external - c*v
I*omega_dot + omega cross (I*omega) = tau_external_body - c_omega*omega
```

The treatment is explicit at the start of the step: transform external world
torque, including the EXTERNAL off-center force moment, to body coordinates;
subtract c_omega*omega there. Compute the complete Euler acceleration with the
gyroscopic term intact. Independently subtract c*v from world external force
before velocity-first translation. Damping is not applied at force_point.
Update omega, then the existing normalized Euler quaternion using new omega;
update velocity and position velocity-first, clock/count once, then optional
ground contact. The frame/quaternion/contact conventions remain unchanged.
When each coefficient is zero its damping arithmetic is bypassed; when both
are zero the existing undamped computation path is preserved exactly, including
contact records. No replacement integrator, energy correction or splitting.

Accuracy is first order in general, including exponential decay and position.
For each positive coefficient enforce the conservative explicit-step bounds:
`h*c/m <= 1` and `h*c_omega/min(I_body) <= 1`. Equality is accepted. Ratios must
be finite/representable; failure raises ValueError rather than substepping or
clamping. Zero coefficients impose no new bound. This is stricter than the scalar
absolute-stability bound 2: isolated damping factors remain in [0,1], so pure
linear damping and isotropic-sphere angular damping do not reverse signs and
their unforced kinetic energies decrease monotonically (equal if velocity zero).
At equality, pure damping can remove a mode in one step: this is the explicit
discrete equation, not an imposed velocity cutoff, and is a poor approximation
to the continuous exponential. Small h relative to decay times is needed for accuracy.

These bounds control the damping terms only. The existing explicit gyroscopic
update still has timestep-dependent drift and may increase rotational energy
on nonspherical bodies; no unconditional per-step dissipation claim is made.
In gravity-free, unforced, contact-free continuous motion,
`dE/dt=-c*|v|^2-c_omega*|omega|^2`. For the explicit velocity update the finite
energy difference additionally contains an O(h^2) nonnegative quadratic term;
the finite-difference power converges to the continuous rate, not equals it.
External work, gravity and penetration projection can increase energy; no
monotonic-decay assertion applies there. Large-step gyroscopic instability,
contact limitations and floating-point representability limits remain.

## Part 5 joint contract (specified before implementation, 2026-10-22)

`Hw5.joints` adds a separate assembly API; Parts 1-4 APIs remain unchanged.
A fixed joint removes all six relative DOFs. A revolute joint permits only one
relative rotation about its axis (five constraints). A prismatic joint permits
only axial relative translation (five constraints). Bodies retain their finite
mass/inertia and dynamic equations; none are made kinematic or assigned a path.

### Configuration, frames and construction

`make_joint(kind, states, a, b, anchor, axis)` captures a reference configuration.
Kinds are `fixed`, `revolute`, `prismatic`; a is a body index or None for the
stationary world, b is a distinct valid body index. The input anchor and axis
are world vectors; the nonzero finite axis is normalized. Both anchors are
initialized to the same world point, then stored in each body's local frame;
the world anchor/axis remain literal world coordinates when a=None. Store local
axes on both bodies and reference `q_ref=inverse(q_a)*q_b`. Quaternions remain
Hamilton body-to-world; omega remains body-frame. The world has identity
orientation and zero velocity, without fake mass or geometry. A direct immutable
`Joint` constructor supports explicit local data; assembly validation checks
references/topology/configuration. All scalar/vector/type validation excludes
bool, nonfinite values and zero axes; inputs are copied and never mutated.
For revolute/prismatic local data, the reference orientation must map axis_b
onto axis_a within 1e-10 unit-vector distance, or construction is rejected.

Only forests, including the world node, are supported: no cycles, parallel
redundant joints, or components with multiple world connections. At most 16
dynamic bodies and 96 scalar constraint rows. Invalid topology is ValueError;
singular/ill-conditioned constraint matrices, reversed revolute axes and failed
iteration/residual checks raise `ConstraintError`. Revolute configurations with
axis dot product <=0 and constrained angular-error norm >.5 rad are outside the
supported
projection neighborhood. Maximum translational constraint-row violation is
limited to .25 m. Large steps should fail explicitly rather than return an
unconverged assembly.

### Constraints and virtual velocities

Let r_i=R_i*local_anchor_i, p_i=x_i+r_i, axis n=R_a*axis_a,
d=p_b-p_a, and anchor velocity u_i=v_i+omega_world_i cross r_i.
For static a: p_a is its world anchor and u_a=omega_a=0. Set w_i=R_i*omega_i.

- Fixed: d=0 and q_b=q_a*q_ref up to quaternion sign;
  u_b-u_a=0 and w_b-w_a=0.
- Revolute: d=0 and R_b*axis_b=n;
  u_b-u_a=0 and the two components of w_b-w_a perpendicular to n vanish.
  Relative spin along n remains free. Axis-angle alignment error uses the
  shortest alignment rotation, excluding opposed-axis singularities.
- Prismatic: d is parallel to n and q_b=q_a*q_ref. For any t perpendicular
  to n, `t dot (u_b-u_a)+(t cross d) dot w_a=0`; this includes the changing
  direction of an axis attached to a dynamic parent. Also w_b-w_a=0.
  The axial coordinate s=n dot d and axial speed remain free.

For relative anchor rows t, the Jacobian angular terms are -r_a cross t and
r_b cross t; prismatic adds t cross d to the parent's angular term. Angular
rows apply opposite torques. The prismatic additional moment is essential for
total angular momentum and zero reaction work with a rotating parent.

### Solver, integration and reaction reporting

Use generalized world velocity V=(v_0,w_0,...), block inverse mass with 1/m
and `R*I_body^-1*R^T`. For a fixed configuration solve
`(J*M^-1*J^T)*lambda=-J*V`, then `V+=M^-1*J^T*lambda`.
The dense direct solve uses diagonal scaling and partial pivoting; a scaled
pivot <=1e-12 is rejected. Constraint impulses are physical linear/angular
impulses in N s / N m s at the recorded solve configuration, with both bodies'
world COM impulses reported per joint. For coincident anchors these represent
equal/opposite anchor forces plus couples. Prismatic separated anchors include
the parent alignment moment so net internal torque remains zero.

For a=None, the reaction's a-fields are zero sentinels because the world has no
dynamic COM variables. The support's balancing wrench is not represented by
those fields; its prescribed velocity is zero and it contributes zero power.

`advance_system(states, shapes, joints, dt, loads=None, gravity=..., ground=False,
options=...)` supplies one `Load` per body (world force/torque/force_point and
the existing optional damping coefficients). Loads last one call; coefficients
also must be repeated. Reuse rigid.advance to calculate the free velocity kick,
then project velocities at OLD poses, integrate the constrained new velocities
with the existing normalized Euler quaternion rule, project pose drift, and
project velocities again at the corrected poses. Clock/count advance once.
The discarded free pose is not returned. No joints: dispatch directly to the
existing independent rigid.advance path, including optional ground/contact.
Any joint plus ground=True is rejected: simultaneous contact/joint solving is
not implemented. State clocks/counts must be synchronized in a coupled assembly.

Pose drift projection solves the same mass-weighted linearized system for
translation/world rotation corrections iteratively, applying actual quaternion
rotation increments. Physical world velocities are carried through the coordinate
change, then reprojected. Pose corrections are NOT reported as physical impulses.
They can change potential/kinetic energy and angular momentum through altered
geometry/inertia. No energy rescaling is used. The method is first order for
smooth motion; finite velocity projections can dissipate energy. No exact
conservative-energy or long-run angular-momentum guarantee is made.

`SolverOptions` defaults: position 1e-10 m, orientation 1e-10 rad,
linear velocity 1e-10 m/s, angular velocity 1e-10 rad/s; max_iterations=16.
All tolerances must be finite positive, iteration count a positive exact int.
Residuals are max constrained-row magnitudes, reported separately in those
four units, never combined into a mixed-unit norm. An advancing coupled state
must already meet these tolerances. Explicit `project_constraints` initializes
inconsistent poses/velocities (within the projection neighborhood) without
changing clock/count; its corrections/impulses are a separate initialization
report, not evidence of conservative motion from an inconsistent initial state.
`project_velocities` changes velocities only and reports reaction impulses.
`joint_residuals` and `joint_coordinates` provide diagnostics; tests must also
use independent anchor/orientation/velocity calculations.

`SystemReport` separates velocity-impulse stages, position iterations/correction
sizes and final residuals; each stage records its configuration and final
velocities for physical impulse interpretation. A failure returns no partial
result and never mutates caller data. No motors, limits, friction, closed loops,
body-body collision or moving prescribed world support are included.
