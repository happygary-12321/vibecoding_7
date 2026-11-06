# HW5: point masses and rigid solids

See [SPEC.md](SPEC.md) for the model, [LOG.md](LOG.md) for verification and
oracle mapping, and [AI_USE.md](AI_USE.md) for agent provenance.
Only Python's standard library is needed for the physics and numerical headless
examples. The Part 2 animation and snapshot test reuse Matplotlib from the
existing `requirements-figures.txt`. Use the repository's
documented CPython 3.12.10 interpreter. The complete existing HW4 runner also
needs the existing `requirements-figures.txt` dependencies; no new dependencies
are added here.

Run these exact PowerShell commands from `D:\CodexCLI\vibecoding\HW3_submission`:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' --version
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.example
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v Hw5.test_dynamics
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.run_tests
git diff --check
```

Also check all HW5 text files, including untracked files that `git diff --check`
does not examine. Run this PowerShell block from the same root; it rejects
trailing whitespace and extra blank lines at EOF:

```powershell
$hw5Files = @(Get-ChildItem -LiteralPath Hw5 -Recurse -File | Where-Object { $_.Extension -in '.py', '.md' })
foreach ($hw5File in $hw5Files) {
    $hw5Lines = [System.IO.File]::ReadAllLines($hw5File.FullName)
    for ($hw5Index = 0; $hw5Index -lt $hw5Lines.Length; $hw5Index++) {
        if ($hw5Lines[$hw5Index] -match '\s+$') { throw "Trailing whitespace: $($hw5File.FullName):$($hw5Index + 1)" }
    }
    if ($hw5Lines.Length -gt 0 -and $hw5Lines[-1] -eq '') { throw "Blank line at EOF: $($hw5File.FullName)" }
}
Write-Output "HW5 whitespace check passed: $($hw5Files.Count) files"
```

The example applies (4,6,-2) N to a 2 kg particle for 100 steps of 0.01 s,
with nonzero motion in every axis. It prints position, velocity, time/count,
and the continuous endpoint and expected numerical bias for comparison.
Use `from Hw5 import State, Parameters, step` for the Python API. Each call
returns a new state and applies its force for that call only.

Part 1 completes only the translational foundation. The 2026-10-22 supplement
verifies lecture oracle categories on PDF pages 7-8 and 11-12 in LOG.md and adds
a binary-exact arbitrary-gravity test at two masses. Original records retain the
historical fact that the lecture was unavailable during initial implementation.

Requirements from [MECE 4990 Lecture 6.pdf](../MECE%204990%20Lecture%206.pdf)
(1-based PDF pages) that were future work at the Part 1 supplement are now
implemented and tested within Part 2's numerical/contact limits:

- Page 35: 13 physical state components (3 position, 3 velocity, 4 quaternion,
  3 angular velocity) and body-frame rotational dynamics. Clock/count metadata
  are additional to these 13; the preserved Part 1 API has only 6 physical components.
- Page 36: torque-free angular-momentum/kinetic-energy checks and rotation
  unchanged by translation of the whole body.
- Pages 37-38: solid rectangular prism, solid sphere and solid cylinder, each
  with center of mass, inertia tensor and ground-contact representation;
  numerical inertia verification by interior point sampling and symmetry checks.
  Ground contact is implemented; multi-body collision detection is not
  required by these slides.

Minimal quaternion representation/kinematics were introduced as a Part 2 dependency.
Part 3 now completes the rotation utilities and their verification below.
Part 4 adds viscous damping and Part 5 adds fixed/revolute/prismatic joints below. No rotational
or geometry-specific oracle is attributed to Part 1. See SPEC.md for the boundary.

## Part 2 commands and API

From the repository root, using the same Python 3.12.10 interpreter:

```powershell
# All HW5 tests (includes all Part 1 tests and a temporary Agg snapshot smoke test)
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest discover -v -s Hw5 -p 'test_*.py'
# Three independent solids, numeric only; no GUI or plotting imports
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.showcase --headless
# Save a static frame at t=1 s; overwrites this PNG, without opening a window
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.showcase --headless --snapshot Hw5/showcase.png
# Interactive repeating 3-second animation (requires a working Matplotlib GUI backend)
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.showcase
```

The scene uses 720 steps of 1/240 s and 91 sampled frames. The solids share a
ground plane but do not collide with each other. Body-axis markers show rotation,
including on the sphere. Display coordinates are (world x, world z, world y), so
world y remains visibly up. The scene is precomputed, then played at nominal
30 fps; GUI timing does not control physics. [Verified frame](showcase.png).

```python
from Hw5.geometry import Prism, Sphere, Cylinder
from Hw5.rigid import RigidState, advance

shape = Prism(mass=2, a=1.2, b=0.7, c=0.9)
state = RigidState(position=(0, 2, 0), omega=(1, 0.7, 1.3))
state, contact = advance(state, shape, 1/240, restitution=0.65)
# For torque-free invariants: ground=False. Loads are world vectors per call.
```

`geometry.py` supplies uniform inertia, analytic support with documented tie
tolerances and display meshes; `spatial.py` supplies frame/quaternion algebra; `rigid.py` supplies
validated immutable state, Euler rotation, point velocity, endpoint contact and
stepping. Full formulas and frames are in SPEC.md. Test oracles and measured
error budgets are in the dated Part 2 LOG.md section.

Important limits: first-order integration drifts in energy/angular momentum;
one selected contact cannot resolve every corner of a flat face. Endpoint
projection can chatter or add potential energy and does not locate impact time.
There is no friction, resting constraint or stacking. The independent-body path
does not couple joints; use the separate Part 5 assembly API below. Part 4's
optional viscous damping does not supply a resting-contact constraint.
Cylinder support is analytic; only display meshes approximate curved surfaces.
The static Agg frame was inspected; live GUI playback/backend behavior was not
manually verified. Headless tests do not establish live GUI performance.

## Part 3: quaternion rotations

`Hw5.spatial` now provides `from_axis_angle(axis, angle)`, `conjugate(q)`,
`inverse(q)`, `compose(after,before)`, `to_matrix(q)`, `from_matrix(R)`, and
`angular_distance(q,p)`, extending the existing `quaternion`, `rotate` and
`unrotate`. Angles are radians; Hamilton components are `(w,x,y,z)` and active
rotations map body column vectors to world. Composition applies `before`
then `after`; inverse maps world to body. q and -q are orientation-equivalent.
See SPEC.md for zero-axis/zero-angle rules, the stable angular-distance metric
and numerical limits. Matrix validation uses 1e-10; accepted near-rotation
discrepancies are governed by that tolerance, not necessarily machine roundoff
alone. The existing rigid-body
integrator, contact solver and test-local Part 2 matrix reference are preserved.

```powershell
# Quaternion tests alone (all-test discovery above also includes them)
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v Hw5.test_quaternions
# Numerical composition and fixed-spin report; no plotting dependency/import
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.quaternion_example --headless
# Optional static comparison image of the same marked prism under both orders and spin
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.quaternion_example --headless --snapshot Hw5/quaternions.png
# Optional GUI display of that static comparison
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.quaternion_example --show
```

The red star marks the same body vertex. Red/green/blue lines show body x/y/z;
the fixed-world x-then-z and z-then-x rotations differ. The third prism undergoes
principal-z spin in exactly 100 steps of .01 s. Output includes rotated marked
vertices, orientation, quaternion/matrix vector residual, and continuous versus
discrete phase. GUI timing does not enter physics. [Comparison image](quaternions.png).
No live GUI verification is claimed.

Lecture PDF pages 39-40 map to axis-angle representation, norm, constant-z spin,
and matrix-round-trip tests. The additional researched oracle is a test-local
Rodrigues vector formula from Illinois TAM212, independent of production
quaternion/matrix helpers. Norm and round trips alone cannot establish the
correct rotation. See the dated Part 3 LOG.md entry for exact test names,
sources, measured errors, tolerances and blind spots. General rigid-body rotation
remains first-order; constant-axis normalized-Euler phase has second-order error.

## Part 4: linear and angular viscous damping

`advance(..., linear_damping=c, angular_damping=c_omega)` adds optional
nonnegative finite coefficients, both default zero. c is in N s/m and applies
world force -c*v at COM. c_omega is in N m s/rad and applies body torque
-c_omega*omega. Pass coefficients each call; external loads retain their existing
one-call lifetime. Part 1's point-mass API remains undamped. Stationary-environment
drag does not obey the undamped Galilean-boost relation.

The scheme evaluates these physical loads explicitly at the old velocities,
preserves gyroscopic coupling and the existing quaternion/contact update, and
is first-order. The enforced timestep bounds are `h*c/m <= 1` and
`h*c_omega/min(I) <= 1` for positive coefficients. Equality is accepted; violations
raise ValueError rather than clamp or substep. These bounds ensure nonreversing
damping-only factors and monotonic unforced sphere kinetic energy; they do not
guarantee general explicit-gyro stability or nonspherical per-step energy decay.
Use timesteps small relative to decay times for accuracy. With both coefficients
zero, the prior arithmetic and contact records are reproduced exactly.

```python
state, contact = advance(state, shape, 1/240,
                         linear_damping=2.0, angular_damping=1.0)
```

From the repository root with the documented interpreter:

```powershell
# New damping tests; all-test discovery above includes these too
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v Hw5.test_damping
# Fixed-step numerical comparison, without plotting imports or a GUI
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.damping_example --headless
# Optional snapshot; uses existing Matplotlib and overwrites the named PNG
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.damping_example --headless --snapshot Hw5/damping.png
# Optional static GUI plots; GUI timing has no effect on physics
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.damping_example --show
```

The showcase compares identical marked spheres (m=5,R=1,I=(2,2,2)) for 400
steps of .01 s, with zero versus c=2,c_omega=1. Gravity, ground and external
loads are disabled. It reports speed, angular speed, independently calculated
kinetic energy and unwrapped marker angle at t=0,1,2,3,4 s. The optional plot
shows decreasing speed/rotation rate, COM motion, energy and the final surface
mark. [Verified damping comparison](damping.png). No live GUI verification is claimed.

Lecture PDF pages 41-42 map to exact zero-coefficient regression, exponential
decay and unforced sphere energy dissipation. The additional researched oracle
checks convergence of nonspherical finite-difference energy rate to continuous
mechanical damping power. These expectations and their roundoff/integration
budgets are in the dated Part 4 LOG.md entry. Energy may increase under external
work, gravity/projection or explicit nonspherical numerical drift. Part 5 adds
the joint assembly API below; the ground/contact limitations remain unchanged.

## Part 5: coupled fixed, revolute and prismatic joints

`Hw5.joints` supports a dynamic body attached to the stationary world and joints
between finite-mass bodies. Fixed removes six relative DOFs; revolute permits
only axial rotation; prismatic permits only axial translation. Constraint
impulses include world inertia and anchor lever arms. This is a coupled solver,
not a set of prescribed paths. A three-body chain is also tested.

```python
from Hw5.geometry import Sphere
from Hw5.rigid import RigidState
from Hw5.joints import make_joint, advance_system, Load

states = (RigidState((-1, 0, 0)), RigidState((1, 0, 0)))
shapes = (Sphere(2, .5), Sphere(3, .5))
joint = make_joint('fixed', states, 0, 1, anchor=(0, 0, 0))
states, report = advance_system(states, shapes, (joint,), .01,
    gravity=(0, 0, 0), loads=(Load(force=(5, 0, 0)), Load()))
# Both finite-mass bodies accelerate; total mass is 5 kg.
```

`make_joint` takes world anchor/axis and captures local anchors/axes plus the
reference relative orientation. Use `a=None,b=body_index` for the static world;
no infinite-mass shape is needed. `Load` uses the existing world forces/torques,
world force point and optional damping. Loads/coefficients last one call.
For an inconsistent initial condition, call `project_constraints` explicitly
and inspect its initialization report; `advance_system` rejects inconsistent
starts. `project_velocities` reports physical impulses at fixed poses.
`joint_residuals` reports m, rad, m/s and rad/s separately. `joint_coordinates`
returns slider displacement (m), principal hinge angle (rad) relative to its
captured initial pose, or zero for fixed. Hinge angles are wrapped, not accumulated.

The method projects kicked velocities, integrates the constrained state,
projects small pose drift, and projects velocity at the corrected pose. It is
first-order. The default solver tolerances are 1e-10 in each field's physical
unit, with 16 pose iterations and scaled-pivot singularity rejection at 1e-12.
`SolverOptions` can set explicit positive tolerances/iteration limits; a failed
solve raises `ConstraintError` with inputs unchanged. Pose/velocity projection
can change energy, and pose correction can introduce angular-momentum drift.
No exact long-run conservation claim is made; refinement tests quantify the error.

Only acyclic forests including the world node are supported (16 bodies / 96
rows maximum). No closed loops, motors, limits or joint friction. Severe mass
conditioning, opposed hinge axes, large constrained angular errors (> .5 rad),
translation row errors > .25 m or iteration-limit failure are explicitly rejected.
Moving prescribed supports are not implemented. **Any joint plus ground=True
is rejected**; simultaneous joint/ground solving is unsupported. With no joints,
the API delegates to the existing independent path, including optional ground.

From the repository root, using Python 3.12.10:

```powershell
# Joint tests; all-HW5 discovery below includes all prior 52 tests too
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v Hw5.test_joints
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest discover -v -s Hw5 -p 'test_*.py'
# All three demonstrations: fixed dynamic pair, revolute pendulum, prismatic slider
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.joints_example --headless
# Optional three-panel snapshot (overwrites this PNG) or static GUI display
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.joints_example --headless --snapshot Hw5/joints.png
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.joints_example --show
```

The joint example runs 300 fixed steps of .005 s without ground. It prints
coordinates, physical body states and maximum residuals in separate units. The
fixed pair responds to external loading as a translating/rotating assembly;
both bodies are dynamic. The pendulum shows its pivot/axis; the slider shows
its arbitrary rail axis. [Verified snapshot](joints.png) includes initial-pose
outlines and COM trails. Matplotlib is optional for numerical modes and reused
for plots. No GUI timing enters physics; no manual live GUI verification is claimed.

Lecture PDF pages 43-44 map to joint DOFs, constraint residuals and conservative
energy/refinement checks. The additional researched oracle tests ideal reaction
work using both bodies' independently computed anchor velocities/angular power,
including a rotating-parent slider. Exact sources, fixtures, error budgets,
initialization effects and measured results are in the Part 5 LOG.md entry.
