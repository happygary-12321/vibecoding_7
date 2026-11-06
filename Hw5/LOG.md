# Part 1 verification log

Part 1 records below are historical and unchanged in meaning. Current Part 2
implementation and verification are recorded in the dated section at the end.

## Independent oracles and derivations

Lecture mapping: **VERIFIED in the 2026-10-22 supplement below** using the
subsequently supplied `MECE 4990 Lecture 6.pdf` (1-based PDF pages).

Historical status at original implementation: **PENDING**. Repository-wide file search, including hidden
paths outside `.git`, found no lecture/slide files or PowerPoint decks; the only
PDF is the existing HW3 `report.pdf`. No actual course slide/page can be cited.
The following analytical oracle is independently derived, not attributed to an
unavailable lecture. The dated supplement now maps these tests to the supplied
lecture's oracle categories without attributing our derivations to the slides.

For constant a=g+F/m, integration gives v(t)=v0+a*t and
x(t)=x0+v0*t+a*t²/2. Summing updated velocities over n equal steps gives
x_n=x0+n*h*v0+a*h²*n*(n+1)/2. Thus signed position bias is a*h*t/2;
velocity has roundoff error only. Each axis obeys this independently.
`Hw5.test_dynamics.DynamicsTests.test_constant_force_trajectory_and_bias`
checks every step for masses 2 and 4, force (4,6,-8), g=(0,-10,0):
a=(2,-7,-4) and (1,-8.5,-2), respectively. No production reference helper
generates any expected result.

`test_hand_step` uses h=.25, m=2, x=(1,-2,3), v=(2,-3,4), F=(4,6,-8),
g=(0,-10,0). Hand arithmetic gives v'=(2.5,-4.75,3),
x'=(1.625,-3.1875,3.75). `test_gravity_is_mass_independent` checks gravity
alone at masses .25 and 7. `test_uniform_motion_and_momentum` checks linear
motion and conserved vector momentum (5,-10,3) kg m/s when g=F=0.
No energy conservation under accelerated semi-implicit Euler is asserted.

`test_first_order_position_convergence` compares raw position error to the
independent continuous endpoint (4,-2.5,1.5) at T=1 for 20/40/80/160 steps.
The norm of the bias is sqrt(69)*h/2; each halving should halve error.
It checks decreasing nonzero errors and log2(error_coarse/error_fine)=1.

## Additional researched oracle: Galilean boost

Source accessed 2026-10-22: Richard Fitzpatrick, University of Texas at Austin,
[Newton's first law of motion](https://farside.ph.utexas.edu/teaching/celestial/Celestial/node5.html),
Newtonian mechanics section, equations (2.1)-(2.11), especially (2.7) and (2.11).
This university teaching source derives position/velocity transformation and
acceleration invariance between inertial frames with constant relative velocity.
Its passive-frame minus sign becomes plus when choosing relative frame velocity
-u. Extending the vector relation to all three components gives the tested boost.

Associated test: `Hw5.test_dynamics.DynamicsTests.test_galilean_boost`.
Assumptions: Newtonian inertial frames, aligned axes, equal clocks and initial
positions, same constant mass, identical uniform gravity and prescribed constant
force, and no velocity-dependent forces or boundaries. Boost u=(1.7,-.8,2.3).
Two masses and two timesteps are tested at every step, comparing v_b-v_a=u
and x_b-x_a=u*n*h without a reference trajectory helper.

Our discrete extension follows by induction: equal acceleration increments
preserve velocity difference u; each position difference then increases by h*u.
This relational oracle tests sensitivity to initial velocity, axis handling and
unintended frame-dependent behavior across paired runs. It complements absolute
trajectory checks; a common wrong constant acceleration could still pass the
boost check, so it does not replace them. Damping or stationary walls would
invalidate these assumptions. This source is not claimed to be the course slides.

## API tests and tolerance policy

All short test names above belong to `Hw5.test_dynamics.DynamicsTests`.
`test_force_lifetime_and_independent_bodies` checks one-step loading and absence
of shared body state. `test_invalid_construction` covers scalar/vector validity,
mass/dt ranges and clock/count validity. `test_rejection_preserves_inputs`
checks invalid force/type, arithmetic overflow and unadvanceable time without
input mutation. `test_immutable_vectors_and_clock` checks defensive tuple copies,
frozen state and clock accumulation across differing durations.

Chosen before executing tests: scalar/vector abs_tol=1e-11 in the corresponding
SI unit and rel_tol=1e-13. These fixtures use at most 160 steps and state scales
below 20: 8*N*epsilon*20 < 5.7e-12, giving conservative roundoff margin.
Convergence order uses absolute 1e-9, with smallest position error about .026 m,
far above roundoff; exact discrete clock checks use binary-exact increments.
Integration error is never hidden inside a loose trajectory tolerance: its
signed a*h*t/2 bias is explicitly checked, and convergence uses uncorrected error.

## Original implementation execution results (historical)

Verified 2026-10-22 with the documented Python312/python.exe, CPython 3.12.10
(the complete HW4 runner printed executable and version). Exact commands are in
[README.md](README.md).

- `-B -m unittest -v Hw5.test_dynamics`: 10 tests passed, 0.009 s, exit 0.
- `-B -m hw4.run_tests`: all 58 legacy/HW4 tests passed, 5.846 s, exit 0.
- `-B -m Hw5.example`: exit 0; 100 steps, 1.000000000 s;
  position (4.01,1.56095,1.495) m, velocity (4,-3.81,-2) m/s.
  Position minus continuous endpoint is (.01,-.03405,-.005) m as predicted.
- `git diff --check`: exit 0, no whitespace errors. Git emitted an LF/CRLF
  advisory for the pre-existing user change in hw4/README.md. New Hw5 files
  are untracked, so this command checks tracked changes only.

The first combined interpreter/version/new-test/example command failed before
Python launched: the sandbox reported the documented executable as unavailable.
The approved HW4 command succeeded; new tests and example were retried outside
the sandbox with approval and passed on their first actual execution. No test
assertion failed, no physics fix was needed, and no tolerance was loosened.
At that time lecture mapping remained pending; no rotational or collision
validation was claimed. See the supplement for the updated mapping and run.

## 2026-10-22 supplement: verified lecture mapping

Inspected the actual 45-page [MECE 4990 Lecture 6.pdf](../MECE%204990%20Lecture%206.pdf).
Every page number below is a **1-based PDF page**, not a presumed printed slide
number. Full text of pages 7, 8, 11, 12, 31, 32, and 35-38 was extracted using
pypdf before edits. The parser warned about three incorrect object offsets;
extraction completed after fixing console encoding. No PDF was modified.
Poppler was not found in PATH or the accessible bundled files; fitz and
pypdfium2 were unavailable. This inspection verifies page text, not visual layout.

All test identifiers in the following tables have the exact prefix
`Hw5.test_dynamics.DynamicsTests.`.

### Page 7, "Simulator Oracles"

| Lecture category | Test names and actual assertions | Physical assumptions | Blind spots |
| --- | --- | --- | --- |
| Exact analytical solution | `test_constant_force_trajectory_and_bias`: at every step v=v0+a*t and x_numeric-x_continuous=a*h*t/2, on all axes, for masses 2 and 4. `test_uniform_motion_and_momentum`: x=x0+v0*t on all axes. | Constant mass, prescribed constant force/uniform gravity, free flight; uniform motion additionally needs g=F=0. | Special cases only; no variable-force trajectory, rotation or contacts. Bias checking also tests the chosen discretization, not exact continuous position. |
| Limiting case | `test_uniform_motion_and_momentum`: with zero force/gravity, linear position and unchanged momentum (5,-10,3). `test_gravity_is_mass_independent`: zero applied force gives v=(0,-.981,0), x=(0,-.0981,0) at two masses. New `test_arbitrary_gravity_hand_step_mass_independence`: the zero-force limit for all three gravity components. | Uniform gravity and no other interactions; g=0 for the uniform-motion case. | Zero-force/zero-gravity results alone cannot validate nonzero applied forces or behavior away from those limits. No damping limit exists in Part 1. |
| Convergence order | `test_first_order_position_convergence`: raw position error against (4,-2.5,1.5) at T=1 is positive, decreases at 20/40/80/160 steps, and log2(E_h/E_(h/2)) is 1 within 1e-9; final velocity/time are checked separately. | Smooth constant acceleration, common physical endpoint, fixed timestep within each run. | Order alone can converge to the wrong equations; no contact/discontinuous-force convergence. The slide's RK4 example has order 4; this implementation is semi-implicit Euler, expected order 1. |
| Conservation or invariant | `test_uniform_motion_and_momentum`: each component of m*v remains (5,-10,3). `test_gravity_is_mass_independent` and the new arbitrary-gravity test: gravitational trajectories do not change with mass. | Momentum conservation requires zero net force; gravitational mass independence requires prescribed acceleration and F=0. | Errors can preserve momentum/invariance while producing wrong positions. Mass independence alone does not establish acceleration magnitude or direction. No angular momentum, quaternion norm, or rotational energy is tested. |

The categories overlap intentionally: the same zero-force run supplies a limiting
case and a conserved-quantity assertion. This is not two independent physical
derivations. Existing hand-step checks additionally validate the discrete contract.

### Page 8, "Independence"

Associated tests: `test_constant_force_trajectory_and_bias`,
`test_uniform_motion_and_momentum`, `test_first_order_position_convergence`,
`test_hand_step`, `test_gravity_is_mass_independent`, and
`test_arbitrary_gravity_hand_step_mass_independence`.

Continuous expected values are obtained by integrating dx/dt=v and
dv/dt=g+F/m, independently of the production stepping implementation. The tests
use their own elapsed n*h, literal acceleration fixtures and continuous endpoint;
they never call production trajectory/energy/reference helpers. Momentum is
computed independently from m*v. Convergence measures uncorrected error against
that continuous endpoint, not against another production run treated as truth.

The discrete contract is a different question: velocity-first Euler intentionally
has position bias. The hand tests use literal arithmetic for v'=v+a*h followed
by x'=x+v'*h. The multi-step bias follows the independent arithmetic-series sum
already derived above. Checking this discrete update can catch update-order bugs,
but by itself only establishes compliance with that update, not correctness of
the governing physics. Comparing both continuous solution and predicted bias,
and checking convergence, keeps these questions separate.

Assumptions: Newtonian point masses, SI units, the stated axes/sign conventions,
constant acceleration and fixed h for the multi-step derivation. Blind spots:
one agent authored implementation and tests, so they are not independently
authored; shared mistaken model/sign assumptions can survive. Literal expected
values and separate mathematical derivations reduce code coupling but do not
prove the model correct. The lecture's independence warning applies here.

### Pages 11-12: metamorphic testing

Page 11 is "Metamorphic Relations"; page 12 is "Symmetry tests are a form of
metamorphic relation". These pages describe changing inputs and checking the
relation between outputs without needing an exact output for each run. Page 12
lists rotation, translation, relabeling, scaling, and conditional time reversal.

Associated test: `test_galilean_boost`. Input transformation adds constant
u=(1.7,-.8,2.3) to initial velocity; output assertions at every step are
v_boosted-v_original=u and x_boosted-x_original=u*n*h. The assumptions are equal
initial positions/clocks, aligned inertial frames, constant uniform gravity,
identical prescribed constant force/mass and no boundaries or velocity-dependent
forces. The discrete induction and UT Austin source remain in the researched
oracle section above. The lecture supplies the **general category**, while
UT Austin supplies the **specific Galilean relation**; we do not claim these
pages explicitly present Galilean boosts or that the relation is absent from all
lecture material.

Added value: paired runs probe sensitivity to the velocity offset and unintended
frame dependence without using an absolute trajectory reference. Blind spots:
a common incorrect constant acceleration can pass this relation, so analytical
tests remain necessary. It does not prove rotation, damping, contact, or time
reversibility correctness. No time-reversal oracle is asserted for this integrator.

### New arbitrary-gravity fixture and tolerance

`Hw5.test_dynamics.DynamicsTests.test_arbitrary_gravity_hand_step_mass_independence`
uses g=(1,-2,3), F=(0,0,0), x=(1,-2,3), v=(2,-3,4), h=.25,
initial time=2/count=8, and masses .5 and 8 kg. Hand arithmetic:

```text
dv = g*h = (.25, -.5, .75)
v' = (2.25, -3.5, 4.75)
dx = v'*h = (.5625, -.875, 1.1875)
x' = (1.5625, -2.875, 4.1875)
time' = 2.25; count' = 9
```

Before running, exact equality (zero tolerance) was chosen: all inputs,
intermediates and results are small binary-exact numbers, including zero divided
by either mass. There is no roundoff allowance needed for this fixture and no
integration-error allowance because the target is the specified discrete step.
The test checks all components, clock/count, fresh result identity, unchanged
state/parameters/force inputs, and identical resulting states across masses.
This closes the missing non-y gravity coverage without changing production code.
Blind spot: one step with one arbitrary vector does not validate every gravity
configuration, variable force, or rotation.

### Future lecture requirements, not Part 1 verification

Page 35, "3D Rigid Body Dynamics": 13 physical components and body-frame Euler
rotational dynamics. Page 36, "3D Rigid Body Dynamics: Oracles": torque-free
angular momentum/kinetic energy and rotation unchanged by whole-body translation.
Page 37, "Geometries": solid rectangular prism, solid sphere and solid cylinder,
each with center of mass, inertia tensor and ground-contact representation;
ground contact only, not multi-body collisions. Page 38, "Geometries: Oracles":
sample points inside each shape to compare numerical inertia with its formula,
and check symmetry such as a cube's axis-independent inertia.
These rotational/geometry-specific tests remain **not implemented/not verified**.
The six current physical components are position/velocity; clock/count are
metadata additional to both those six and the future 13. See SPEC.md for scope.

### Supplement execution results

Executed 2026-10-22 from the repository root using the documented
`C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe`;
the HW4 runner confirmed CPython 3.12.10. Exact PowerShell commands:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest -v Hw5.test_dynamics
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.example
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.run_tests
git diff --check
```

Also executed the full all-HW5-file PowerShell whitespace block documented in
README.md; it checks tracked and untracked `.py`/`.md` files directly.

| Check | Actual result |
| --- | --- |
| HW5 Part 1 suite | 11 tests passed, 0.011 s, exit 0, including the new arbitrary-gravity test at both masses with exact equality. |
| Example | Exit 0; 100 steps, time 1.000000000 s; position (4.01,1.56095,1.495) m, velocity (4,-3.81,-2) m/s; expected bias (.01,-.03405,-.005) m. |
| Complete HW4/legacy suite | 58 tests passed, 4.465 s, exit 0. |
| Tracked whitespace | `git diff --check` exit 0; only the pre-existing hw4/README.md LF/CRLF advisory. |
| HW5 tracked/untracked whitespace | 8 text files checked, no trailing whitespace or extra blank EOF lines, exit 0. |

All tests passed on their first execution in this supplement; no tolerance or
physics change was needed. Initial failures were PDF-inspection tooling only:
interpreter access in the sandbox, then GBK console output; approved execution
and UTF-8 output fixed these. Parser warnings and the rendering-tool limitation
are recorded above and in AI_USE.md. The historical 10-test run remains above
as historical evidence, not the result of this supplement.

Lecture mapping is now complete for Part 1's supported categories. Rotational,
geometry-specific, ground-contact, damping and joint requirements remain future
work; multi-body collision detection is not required by pages 37-38. No commit
or push was performed.

## 2026-10-22 Part 2: solid rigid bodies and ground

### Lecture inspection and oracle mapping

Re-read the actual 45-page `MECE 4990 Lecture 6.pdf` before writing the Part 2
SPEC and before implementation. The existing pypdf extraction command with UTF-8
output verified the complete requested pages; the three known object-offset
warnings recurred without preventing extraction. Page references are 1-based
PDF pages. Part 1 status/results above describe that earlier stage, not current
Part 2 capabilities. Minimal quaternion support does not complete Part 3.

In the following table, `R.` means `Hw5.test_rigid.RigidTests.`, `I.` means
`Hw5.test_inertia.InertiaSamplingTests.`, and `S.` means
`Hw5.test_showcase.ShowcaseTests.`. These are exact test methods; unittest
discovery prints the same modules without the `Hw5.` package prefix.

| Source/category | Tests and assertions | Assumptions / blind spots |
| --- | --- | --- |
| PDF p35, "3D Rigid Body Dynamics" | `R.test_gyroscopic_hand_step`: nonzero coupling for I=(52,40,20), omega=(1,2,3). `R.test_principal_axis_rotation_and_torque`: constant principal spin and literal torque response. `R.test_world_offcenter_load_and_lifetime`: world lever arm/force, torque transform, one-step lifetime. | Uniform, immutable inertia, body-frame omega; literal steps check discrete equations, not global trajectory accuracy. Principal spin alone would miss the gyro term. |
| PDF p36, "3D Rigid Body Dynamics: Oracles" | `R.test_torque_free_invariants_refine`: maximum relative world angular-momentum and rotational-energy drift over T=1, three timesteps. `R.test_translation_invariant_rotation`: exact equality of orientation/omega for shifted trajectories. | Angular momentum is about COM, expressed in world axes; gravity at COM has no torque. No contacts/loads. First-order finite-run drift is allowed and must refine. Translational symmetry can survive a common rotational error. |
| PDF p37, "Geometries" | `R.test_hand_inertia_and_symmetry`: literal nonunit prism/sphere/cylinder moments, COM, full tensor and cube-axis symmetry. `R.test_oriented_clearance`: prism/cylinder 90-degree and tilted support. `R.test_quaternion_frames_and_mesh`: orientation-dependent vertices for every shape. | Uniform solid density; body cylinder axis z. Formula tests do not alone establish sampling or contact behavior. Display tessellation is not used for collision. |
| PDF p38, "Geometries: Oracles" | `I.test_interior_quadrature_refinement`: independent interior integration of all nine tensor entries, total mass/first moments, n=8/16 error reduction. `R.test_hand_inertia_and_symmetry`: cube arbitrary-axis inertia and cylinder axial/transverse distinction. | Deterministic midpoint quadrature and uniform density. Finite resolutions/fixtures do not cover every aspect ratio, mesh, or density distribution. Symmetry alone can hide a common wrong inertia scale. |
| PDF pp7-8, hand/limiting/independence categories | `R.test_zero_spin_agrees_with_part1`: identical position/velocity/time/count for all shapes under nonzero 3D force/gravity, no rotation. | This is deliberately an API regression, not an independent physics oracle; original independent Part 1 tests remain. |

### Researched additional oracle: offset-origin inertia tensor

Source verified 2026-10-22: J. Peraire and S. Widnall, MIT 16.07,
[Lecture L26: 3D Rigid Body Dynamics: The Inertia Tensor](https://ocw.mit.edu/courses/16-07-dynamics-fall-2009/dd277ec654440f4c2b5b07d6c286c3fd_MIT16_07F09_Lec26.pdf),
PDF page 7, "Parallel Axis Theorem"; page 3 defines the matrix sign convention.
The notes derive offset components using vanishing first moments about COM.
Their positive product-of-inertia symbols enter the matrix with minus signs.
Our matrix convention is directly `integral (r^2*delta_ij-r_i*r_j) dm`, yielding
`I_offset = I_COM + m*((d dot d)*Identity - outer(d,d))`.

Associated test: `I.test_parallel_axis_offset_tensor`. Assumptions: the same
uniform rigid solid/mass, COM origin for the initial tensor, parallel axes after
translation, and d=(.3,-.4,.5) m. Independent sample coordinates are shifted by -d
before integrating; neither samples nor integration use production inertia
formulas. Check all nine entries at both resolutions, including nonzero negative
or positive off-diagonals. Compare both sampled-offset minus sampled-COM tensor
to the theorem and sampled-offset tensor to production-COM plus the theorem.
The first relation alone can hide a common quadrature/COM-inertia error; the
second comparison and centered sampling tests supply absolute coverage.
This geometric oracle does not test time integration or impacts.

The original UT Austin Galilean oracle and test remain intact as Part 1 evidence;
this Part 2 research is a separate offset-inertia relation, not a second citation
for an analytical trajectory formula.

### Independent calculations and error budgets

Before first execution, the new test files specified these tolerances. No values
were loosened after execution. All core expectations come from literal hand
arithmetic or test-local integrals/matrices, not production reference helpers.

**Hand inertia and Euler coupling.** Prism m=12, (a,b,c)=(2,4,6) gives
I=(52,40,20); sphere m=5,R=2 gives (8,8,8); cylinder m=6,R=2,L=6 gives
(24,24,12), in kg m^2. For the prism at omega=(1,2,3), Euler coupling gives
alpha=((40-20)*2*3/52,(20-52)*3/40,(52-40)*2/20)
=(30/13,-2.4,1.2). At h=.01, omega'=(1+3/130,1.976,3.012).
Principal z torque 40 N m with Iz=20 increases omega_z=2 to 2.5 in .25 s.
These and frame/contact calculations allow 1e-11 SI absolute roundoff, far below
the changes under test. Constant principal spin produces an exact discrete
angle n*2*atan(h*omega/2); its continuous-angle error is checked separately
against 7e-5 rad at T=1,h=.01,omega=2 (leading error ~6.67e-5 rad).

**Torque-free integration.** The test independently forms a quaternion rotation
matrix (production uses cross-product rotation) and computes world L=R*I*omega
and E=omega dot I*omega/2 using literal I=(52,40,20). Initial omega=(.3,.4,.5),
q=(cos(.3),sin(.3),0,0). At h=.01 the small h*|omega| and smooth moderate Euler
coupling motivate a conservative .005 relative finite-run drift ceiling over
one second. This is an integration-error budget, not roundoff. The stronger
requirement is that maxima over the entire run shrink by a ratio in [.4,.6]
when h halves, with coarse error >1e-8. This first-order bracket is chosen
before measurements; it is not a rigorous all-state stability bound.
No energy/omega rescaling is performed. Observed maximum relative errors:

| h (s) | world angular momentum | rotational energy |
| --- | --- | --- |
| .01 | .000922183706960478 | .0007242565889032875 |
| .005 | .0004610671923410806 | .00036229520502556315 |
| .0025 | .00023052708213245604 | .0001811890264586471 |

**Interior inertia quadrature.** Test-only `samples` uses prism Cartesian cell
midpoints with mass m/n^3; sphere radial shell midpoints, uniform cos(theta)
midpoints and 2n azimuths, weighting by the exact shell-volume fraction divided
by 2n^2; cylinder annulus midpoints, n height midpoints and 2n azimuths, weighting
by the exact annulus-volume fraction divided by 2n^2. Thus weights are density
times represented volume, not equal weights on a nonuniform spherical grid.
Every point is checked strictly inside its solid. No production sampling or
inertia expression generates a point or a weight. Total mass and first moments
are checked. n=8/16 gives 512/4096 prism points and 1024/8192 curved-solid points.
Midpoint error is O(n^-2): require relative diagonal error <2/n^2 and fine/coarse
ratio [.20,.30]. Off-diagonal cancellation, mass/first moments and offset-theorem
differences use 1e-10 absolute (SI appropriate to each quantity), allowing
accumulated roundoff in up to 8192 small weighted additions. This allowance is
many orders below the diagonal quadrature error. Offset diagonal comparison
retains the sampling allowance 2*max(I)/n^2; no dynamics timestep is involved.

| Shape | max relative diagonal error n=8 | n=16 |
| --- | --- | --- |
| Prism | .015625 | .00390625 |
| Sphere | .014687538146972656 | .003684893250465393 |
| Cylinder | .013671875 | .00341796875 |

### Ground-contact calculations, coverage and limits

`R.test_offcenter_impulse_hand_calculation`: prism m=3,a=2,b=4,c=2 has Iz=5.
At 45 degrees about z the support lever is (1,-3,0)/sqrt(2). With v_y=-2,
omega=0,e=.5, inverse effective mass is 1/3+(1/2)/5=13/30, so j=90/13 N s,
v_y'=4/13, omega_z'=18/(13*sqrt(2)), and selected-point vn'=1 m/s.
The kinetic-energy change is independently -45/13 J. This separates rotational
effective mass from COM-only restitution and tests the torque sign.

`R.test_sphere_centered_impact_and_endpoints` checks e=0,.5,1, zero artificial
spin, unchanged tangential velocity and penetration correction. Sphere normals
pass through COM; frictionless ground cannot spin it up.
`R.test_contact_point_direction_and_manifold_limit` checks a separating contact
with inward COM and an approaching contact with outward COM. It explicitly
demonstrates the tied-face limitation: zero centroid speed can leave an inward
corner untreated. `R.test_cylinder_ground_and_advance_clock` checks the tilted
cylinder impact, restitution at its support, endpoint clearance and exactly one
clock/count increment. No claim of exact conservation across projection is made.

Major-function coverage: shape construction/inertia/tensors/COM/vertices are
covered by hand, mesh and quadrature tests; `ground_support` by oriented-clearance,
impact and scene tests; `world_mesh`, quaternion normalization/multiplication and
forward/inverse transforms by `R.test_quaternion_frames_and_mesh`; angular
acceleration by the gyro/torque tests; `advance` by Part 1 equivalence, loads,
invariants, contacts and scene; `contact_velocity`/`resolve_ground` by independent
impact and direction checks. `R.test_validation_and_immutability` covers rejected
dimensions, state, force/torque/application point, timestep, restitution, shape,
mesh resolution and arithmetic overflow with unchanged caller-owned inputs.
Private vector primitives are exercised through nontrivial frame and impact
expectations, not merely self-inverse round trips. `S.test_three_body_headless_scene`
checks all three shapes rotate and impact; `S.test_snapshot_smoke` renders a
temporary PNG with Agg. Live animation event-loop behavior is not tested.

Limitations: first-order finite-run invariants do not establish long-run stability,
arbitrary aspect-ratio stability or general forced-rotation accuracy. One support
resultant is not a full manifold; contact can chatter and cannot model stacking
or all corner motions. Penetration projection changes potential energy. Impacts
are resolved at endpoints without continuous detection. Curved display meshes
are approximate, but cylinder support uses its oriented finite axis and radius
analytically (not a sphere). No friction, damping, joints or body-body collision.

### Part 2 execution evidence

On 2026-10-22, with the documented CPython 3.12.10 interpreter, from repository root:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest discover -v -s Hw5 -p 'test_*.py'
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.example
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.showcase --headless
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.showcase --headless --snapshot Hw5/showcase.png
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.run_tests
git diff --check
```

- All HW5: 29 tests passed (11 preserved Part 1, 14 rigid, 2 sampling, 2 showcase),
  0.857 s, exit 0 on the first actual execution.
- Part 1 example: exit 0; unchanged position (4.01,1.56095,1.495), velocity
  (4,-3.81,-2), 100 steps at t=1 s.
- Both showcase modes: exit 0; each body 720 steps at t=3 s. Impulses counted:
  prism 25, sphere 5, cylinder 15. Final positions respectively
  (-2.7,.460164,0), (.3,.577906,0), (2.7,.459555,0); final body omega
  (-.285216,.915269,.822096), (1.5,1,.5), (.125832,.112979,1).
- Complete HW4/legacy suite: 58 tests passed in 4.581 s, exit 0.
- Saved `Hw5/showcase.png` at t=1 s and visually inspected it: three solids,
  ground, axis labels and body-axis markers are visible. No live GUI playback
  was claimed verified; the headless path avoids any GUI requirement.

The initial unapproved sandbox launches of the new test and showcase commands
could not locate the documented interpreter. Approved external retries succeeded.
These were launch failures, not failing physics assertions. There were no test
failures, no changes to production physics after the first passing run, and no
tolerance relaxation. Tracked/all-HW5 whitespace results are recorded after the
final documentation check below. No commit or push.

Final whitespace check: `git diff --check` exited 0 (only the pre-existing
hw4/README.md LF/CRLF advisory). The README PowerShell scan passed all 15 HW5
text files, including new/untracked files, with no trailing whitespace or extra
blank lines at EOF. The generated PNG is binary and excluded from text checks.
Final status retained the pre-existing root README/HW4/transcript/PDF changes;
this Part 2 work changed files only under Hw5.

## 2026-10-22 Part 3: quaternion rotations and verification

Earlier entries retain their original execution results and scope. The current
Part 3 changes extend the same spatial.py representation; rigid.py's integrator,
geometry calculations, contact solver and Part 1 API are unchanged. The only
geometry.py edit clarifies its docstring: analytic support with documented tie
tolerances. Earlier broad references to "exact" support should be read with
the prism 1e-12 m and cylinder 1e-14 direction tie rules in SPEC.md.
The Part 2 test-local `world_vector` matrix reference remains test-local and
does not call the new production conversion.

### Actual lecture inspection and mappings

Before implementation, searched the actual 45-page `MECE 4990 Lecture 6.pdf`
with pypdf. **PDF page 39 is "Quaternions"; PDF page 40 is "Quaternions: Oracles"**.
Numbers here are 1-based PDF pages. Page 39 gives the half-angle axis construction
and motivates quaternions over Euler angles. Page 40 lists unit norm, constant-z
spin angle omega*t, and conversion to a matrix and back. The three known object
offset warnings recurred but extraction succeeded. This verifies page text,
not a new visual rendering of the lecture PDF.

All abbreviated test names below have the exact prefix
`Hw5.test_quaternions.QuaternionTests.`. Discovery prints the module without
the `Hw5.` prefix.

| Lecture oracle | Tests and assertions | Assumptions / blind spots |
| --- | --- | --- |
| p39: half-angle rotation representation | `test_identity_and_coordinate_quarter_turns`, `test_exact_half_turn_matrices_and_small_angles`: literal coordinate-vector/matrix expectations, identity, small-angle retention, exact and near-pi cases. | Right-handed active rotations, radians; finite fixtures cannot cover all floating-point ranges. |
| p40: unit quaternion norm | `test_long_run_norm_with_changing_omega`: maximum norm error <1e-14 over 10000 steps at h=.001 with nonspherical prism and non-principal omega; omega must change measurably. | Normalization is expected; norm alone can pass with a wrong phase, axis or multiplication order. This is not a long-run energy-conservation claim. |
| p40: constant omega about z gives angle omega*t | `test_constant_z_spin_phase_error_and_refinement`: compare measured angle to both 2.6 rad continuous target and the independently derived discrete phase for T=2, omega=1.3, n=100/200/400; separate predicted positive lag and near-quarter refinement ratio. | Torque-free sphere makes constant omega physically valid; angle range is kept below pi to avoid wrapping ambiguity. Fixed-axis second-order phase is a special case, not general second-order dynamics. |
| p40: matrix round trip | `test_matrix_properties_and_orientation_round_trips`: orientation distance <2e-12, orthogonality and det +1, identity, small angles, coordinate/arbitrary axes, exact and near pi; also compare recovered rotated vectors to independent Rodrigues expectations. | Proper finite rotations only. Round trips alone can hide paired inverse-function errors; norm/round trips do not replace vector expectations. |

### Additional researched oracle: independent Rodrigues vector rotation

Source verified 2026-10-22: University of Illinois, TAM 212 Introductory Dynamics,
[Rotations and Angular Velocity, "Rodrigues' rotation formula"](https://courses.grainger.illinois.edu/tam212/su2025/rkr.html).
The relevant displayed equation is `Rot(v;theta,u)=v*cos(theta)+(u cross v)*sin(theta)
+u*(u dot v)*(1-cos(theta))` for a unit axis u. The same page states the right-hand
convention. The section heading and equation were verified from the actual page;
the equation is not assigned an invented equation number.

Associated test: `test_rodrigues_arbitrary_axis_and_matrix`. Test-local
`rodrigues` independently normalizes axis, spells out the cross product, and
computes the displayed vector expression. It calls no production quaternion,
matrix or vector helpers. Matrix columns are independently constructed as images
of basis vectors; both to_matrix and from_matrix are tested against these.

Assumptions: active Euclidean rotations, a fixed nonzero axis, right-handed
coordinates, angle in radians. Added coverage: catches rotation direction,
axis and component/column convention errors that can preserve norm and survive
paired round trips. Blind spots: fixed-axis algebra does not establish dynamics
for changing omega; shared mistaken interpretation of handedness is possible,
so literal coordinate rotations and nonidentity-body-frame tests complement it.

### Other exact mappings, independence and numerical policy

`test_noncommuting_composition_order` uses literal x/z quarter-turn results:
body y maps to world z under x then z, versus -world x under z then x.
It also checks matrix composition in the documented order.
`test_body_kinematics_right_multiplication` starts at Rx(pi/2), spins about body
z and checks the world image of body x is (cos(phi),0,sin(phi)); incorrect left
multiplication would put the sine in world y instead.
`test_sign_equivalence_vectors_geometry_and_trajectories` checks q versus -q
on vectors, world meshes, support, positions/velocities/omega, contact records and
orientation for all three shapes through 60-step contacting trajectories.
`test_inverse_and_magnitude_preservation` checks inverse/unrotate recovery,
composition with inverse, vector length and unchanged omega with nonunit input q.
`test_sphere_arbitrary_axis_spin` checks torque-free sphere omega=(2,-3,6)/7
against fixed-axis Rodrigues motion; constant arbitrary body spin is physically
valid for isotropic sphere inertia, unlike general nonprincipal prism rotation.
`test_invalid_inputs_and_unchanged_sequences` checks malformed/nonfinite/reflecting/
sheared/scaled matrices, invalid axes/angles/quaternions, accepted 1e-12 diagonal
matrix perturbation and unchanged mutable input sequences on success/failure.

Tolerances were written in test_quaternions.py before the first execution:

- Algebraic vector/matrix/orientation checks: absolute 2e-12 in the appropriate
  unit (dimensionless matrix/quaternion norm or radians for orientation). Small
  fixed fixtures have scales <=7 and O(10-100) floating-point operations; this
  provides margin above double-precision roundoff without an integration allowance.
  The public matrix-input contract separately uses 1e-10 residual/determinant
  tolerance; it is not an accuracy allowance for exact rotation fixtures.
- Stable orientation metric: normalize, use the smaller of ||q-p|| and ||q+p||,
  with the larger as denominator in `4*atan2(small,large)`. This gives the principal
  relative angle and avoids acos cancellation. A 1e-12 rad fixture must retain
  its nonzero vector part and recover its angle to 1e-12 relative accuracy.
- Unit norm: 1e-14 absolute, a conservative few-dozen-epsilon budget for each
  normalized snapshot. Norm is measured each step, not summed over steps.
  Quaternion normalization does not normalize vector/omega magnitudes.
- Constant-z spin: normalized Euler multiplies by the normalized factor
  `(1,0,0,h*omega/2)`, hence discrete angle `2*n*atan(h*omega/2)`.
  The lag against omega*T has leading term `omega^3*T*h^2/12`, with a smaller
  alternating-series correction. Actual phase and predicted lag agree within
  3e-12 rad (roundoff), while the positive integration lag must stay below that
  leading term. Fine/coarse lag ratio must be in [.249,.251].
- Arbitrary-axis sphere: at T=1,h=.002, omega norm=1, phase lag is about
  3.33e-7 rad. The discrete Rodrigues comparison allows 5e-12 vector roundoff;
  the continuous comparison allows 3e-6 vector error, covering vector norm
  sqrt(38) times the predicted phase lag (~2.06e-6). These two allowances test
  different questions. No integration-error allowance hides algebraic errors.

Measured constant-z phase errors (radians):

| h | continuous minus numerical angle |
| --- | --- |
| .02 | .00014645181674000085 |
| .01 | .0000366157384616983 |
| .005 | .0000091541086484348 |

Maximum quaternion-norm residual over 10000 varying-omega steps:
2.220446049250313e-16. General rigid dynamics remain first order; these tests
neither change the integrator nor assert exact invariant conservation.

### Part 3 example and actual verification

Commands executed from the repository root with documented CPython 3.12.10:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest discover -v -s Hw5 -p 'test_*.py'
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.example
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.showcase --headless
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.quaternion_example --headless
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.quaternion_example --headless --snapshot Hw5/quaternions.png
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.run_tests
git diff --check
```

- All HW5: **41 tests passed**, 1.294 s, exit 0 on first run; includes the
  29 existing tests and 12 new quaternion tests. No tolerance was loosened.
- Part 1 example: exit 0 with prior numerical output, position (4.01,1.56095,1.495)
  and velocity (4,-3.81,-2) at t=1,100 steps.
- Part 2 headless showcase: exit 0,720 steps/body; original outputs and impact
  counts 25/5/15 preserved.
- Part 3 headless example: exit 0; same marked corner (.7,.4,.5) maps to
  (.5,.7,.4) for x-then-z and (-.4,-.5,.7) for z-then-x. Rotation-order separation
  is 2.094395102393 rad. Quaternion/matrix maximum vector residual 1.11e-16 m.
  Spin angle 1.299981692131 rad versus 1.3 continuous, lag 1.83079e-5 rad;
  omega remains (0,0,1.3).
- Snapshot command: exit 0. Inspected the generated PNG. The first rendering
  clipped axis labels and obscured the middle corner mark; tight image bounds
  and explicit marker layering fixed these presentation issues. Regenerated and
  inspected all three marked-prism panels. No live GUI verification is claimed.
- Complete HW4/legacy suite: **58 tests passed**, 4.584 s, exit 0.

No test failed. The initial lecture extraction and new example launches could
not access the documented interpreter inside the sandbox; approved retries
outside it succeeded. No physics/convention or tolerance changes were needed.
No damping, joint, solver or integrator change; no commit or push. Whitespace
results for tracked and all HW5 text files are appended after the final check.

Final checks: `git diff --check` exited 0, with only the pre-existing
hw4/README.md LF/CRLF advisory. The README PowerShell whitespace block passed
all **17 HW5 text files**, including untracked new files; binary PNGs are excluded.
Final status retains the pre-existing root README/HW4/transcript/PDF changes.
Part 3 adds no edits outside Hw5. Remaining limits include finite-precision
trigonometric range reduction at extreme angles, the documented matrix acceptance
tolerance, first-order general rotational integration and existing endpoint/
single-resultant ground contact. Damping and joints remain future work.

## 2026-10-22 Part 4: linear and angular viscous damping

Earlier records retain their historical results and scope. Part 4 adds optional
keyword coefficients to rigid.advance; the unchanged Part 1 API remains undamped.
The Part 4 SPEC was written before implementation. Damping is evaluated as a
world COM force and body-frame torque at the old velocities, with the existing
explicit gyro, normalized quaternion, velocity-first translation and endpoint
contact ordering preserved. There is no new multiplier-based damping mechanism,
clamp, omega normalization, energy rescaling, solver or joint implementation.

### Verified lecture pages and exact test mappings

Inspected the actual 45-page `MECE 4990 Lecture 6.pdf` before editing:
**1-based PDF page 41 is "Damping" and page 42 is "Damping: Oracles"**.
Page 41 gives linear force/angular torque damping and the stated SI coefficient
units. Page 42 gives zero-coefficient regression, exponential free-body velocity
decay and energy dissipation. Known object-offset warnings did not prevent
pypdf text extraction. No claim of a new visual lecture render is made.

All test names in this section have the prefix
`Hw5.test_damping.DampingTests.` (discovery displays `test_damping` without `Hw5.`).

| Lecture check | Exact tests / assertions | Assumptions and blind spots |
| --- | --- | --- |
| p42: zero coefficients reproduce undamped results | `test_default_and_zero_exact_undamped_regression`: exact equality of full states and contact records for 60 steps, each shape, nonzero external loads/force point and actual contacts. All 41 prior tests and prior example results also pass unchanged. | This is a regression/limiting oracle, not an independent physical derivation. A shared error in default/zero paths could pass; prior independent tests remain necessary. |
| p42: exponential free-body velocity decay | `test_linear_exponential_and_position_refinement`: nonzero 3D v/x with m=2.5,c=1.25; continuous exponential and integrated position at T=1; closed-form discrete sequence checked separately. `test_sphere_angular_exponential_and_refinement`: omega0=(1,-2,3), sphere m=5,R=2,I=8,c_omega=4. Both require first-order refinement. | Uniform stationary environment; no gravity/contacts/external work. Constant exponential angular components apply to the isotropic sphere, not general nonspherical rotation. Special-case references do not validate all loads. |
| p42: dissipating energy | `test_linear_angular_and_combined_sphere_energy_decay`: strict kinetic-energy decrease every step for linear-only, angular-only and combined cases; unaffected velocity/spin stays unchanged. | Unforced, gravity-free, contact-free sphere, within damping bounds, nonzero initial velocities. Does not establish energy decrease under work, projection or explicit nonspherical drift. |

Additional coverage:
`test_combined_hand_step_and_inputs_unchanged` checks literal one-step velocity,
position, omega, quaternion, clock/count and unchanged inputs.
`test_nonspherical_gyro_and_body_damping_contribution` uses nonidentity orientation
and compares gyro plus independent body damping correction; omega_x increases
despite damping, exposing the invalid componentwise exponential assumption.
`test_external_loads_lifetime_and_no_com_drag_moment` verifies drag at COM is not
incorrectly applied at the external force point and that loads/coefficients must
be supplied again on the next call.
`test_invalid_coefficients_and_step_boundaries` rejects negative/nonfinite/bool/
malformed coefficients and bound violations, accepts equality, and checks inputs
unchanged on failure. The nonspherical bound uses minimum inertia, not an average.
`test_gyro_numerical_drift_can_exceed_dissipation` demonstrates the documented
counterexample to unconditional nonspherical per-step energy decrease.
`test_headless_example_smoke` executes the damping example and checks its report.

### Researched additional oracle: mechanical damping power

Verified 2026-10-22: Douglas Cline, University of Rochester, authored textbook
[Variational Principles in Classical Mechanics, section 10.4, Rayleigh's Dissipation Function](https://phys.libretexts.org/Bookshelves/Classical_Mechanics/Variational_Principles_in_Classical_Mechanics_%28Cline%29/10%3A_Nonconservative_Systems/10.04%3A_Rayleighs_Dissipation_Function).
The displayed work-against-friction relation `2*R=dW_f/dt` identifies dissipation
power; equation (10.15) gives generalized dissipative forces. The page credits
Cline and the Rochester source textbook. This is an authored mechanics source,
not a second citation for exponential decay.

For our isotropic viscous force/torque laws, R=(c*|v|^2+c_omega*|omega|^2)/2.
The associated test is `test_power_balance_rate_converges_nonspherical`.
Our rigid-body derivation: dot translation with v and Euler's body equation
with omega. Since omega dot (omega cross I*omega)=0, the gyro term does no
continuous work. Therefore E_dot=-c*|v|^2-c_omega*|omega|^2 with constant mass/
inertia, no gravity, external loads or contacts. Rotation preserves the dot
product, so body torque/body omega give physical rotational power.

The test starts from v=(2,-1,3), omega=(1,2,3), nonspherical I=(52,40,20), m=12,
c=.8,c_omega=.6. Instantaneous power is independently -19.6 W. It measures
(E(h)-E(0))/h for four independently started steps and requires convergence,
not equality to continuous power. It also verifies the explicit-method bias
using literal gyro/damping acceleration and independent energy.

Added value: couples translation, non-principal rotation, torque sign, inertia
and energy balance beyond the isotropic exponential cases. Blind spots: it is
a local h->0 check, not a long-run stability result or validation of contact/work
accounting. An orientation-only error might preserve this energy rate, so the
Part 3 vector and body-frame kinematics oracles remain necessary.

### Discrete scheme, hand calculations and tolerances

For damping-only linear motion, k=c/m and r=1-k*h:
`v_n=v0*r^n`, `x_n=x0+(v0/k)*r*(1-r^n)` for n*h=T.
Continuous motion is `v0*exp(-k*T)` and
`x0+(v0/k)*(1-exp(-k*T))`. For the sphere angular test,
`omega_n=omega0*(1-(c_omega/I)*h)^n`; continuous omega has the corresponding
exponential. These expectations are test-local derivations, not production
reference helpers. Separate discrete-form checks use roundoff allowances while
continuous errors must decrease by first-order refinement.

Hand step: sphere m=5,R=2,I=8, h=.25, c=2,c_omega=4; initial
x=(1,2,3),v=(2,-4,6),omega=(1,2,-3), time=1,count=4. Linear factor=.9,
angular factor=.875, so v'=(1.8,-3.6,5.4),x'=(1.45,1.1,4.35),
omega'=(.875,1.75,-2.625),q'=normalize(1,.109375,.21875,-.328125),
time'=1.25,count'=5. Normalization here is the specified quaternion update only.

Nonspherical hand damping: I=(52,40,20),omega=(1,2,3),c_omega=2,
gyro alpha=(30/13,-2.4,1.2); damping adds (-1/26,-.1,-.3) rad/s^2.
At h=.01 the difference from the undamped omega is (-.01/26,-.001,-.003).
No exponential assumption is used for these three components.

All new tolerances were written before running tests and left unchanged:

- Hand steps and closed-form discrete sequences: 1e-11 absolute in the relevant
  SI unit. Fixtures have <=200 trajectory steps and scales below 10, leaving
  margin above ordinary O(n*epsilon*scale) roundoff. No exponential truncation
  error is hidden in that allowance.
- Continuous endpoint error bounds: velocity norm error <h, position <3h,
  angular-velocity norm error <h for rates k=.5 and the chosen fixtures.
  The leading explicit-decay velocity error is approximately
  |v0|*exp(-k*T)*k^2*T*h/2; chosen ceilings exceed it conservatively.
  Each halving must reduce all measured errors with ratio [.48,.52]; coarse
  errors must exceed 1e-8. This establishes first order for the smooth fixtures.
- Sphere energy decay uses strict inequality for 100 unforced steps, with
  positive damping and nonzero affected velocity; no energy helper from production.
- Power: expanding the explicit quadratic kinetic energy yields
  `(E(h)-E0)/h = P0 + h*B`,
  `B=(m*|a0|^2+alpha0 dot I*alpha0)/2`, only in the unforced/free fixture.
  Here a0=-(.8/12)*(2,-1,3),
  alpha0=(30/13-.6/52,-2.4-1.2/40,1.2-1.8/20), B=267.8727179487179.
  The bias comparison uses 2e-9 W absolute, a roundoff/cancellation budget for
  subtracting energies of about 280 J and dividing by minimum h=.0025 s.
  The nonzero h*B bias is integration/discretization error, not roundoff.
  The same [.48,.52] halving ratio checks convergence of rate to -19.6 W.

Measured results:

| h (s) | linear velocity error (m/s) | linear position error (m) | sphere omega error (rad/s) | power rate error (W) |
| --- | --- | --- | --- | --- |
| .02 | .008210182280629467 | .026121783964392714 | .005704503070431331 | 5.357454358974884 |
| .01 | .004093927340170864 | .013042057033078928 | .002844494833838755 | 2.678727179486124 |
| .005 | .002044186039635602 | .006516335070940980 | .001420317496135435 | 1.339363589736060 |
| .0025 | not run | not run | not run | .6696817948610274 |

### Stability restrictions and remaining physical/numerical limits

Enforce h*c/m<=1 and h*c_omega/min(I)<=1 for positive coefficients; equality
accepted. The scalar Euler stability interval extends to 2, but the chosen
stricter bound keeps isolated decay factors nonnegative/nonreversing.
At equality a pure mode becomes exactly zero by the discrete equation; this
is tested and is not a clamp. It does not approximate exponential decay well.
Zero coefficients bypass damping arithmetic and impose no new step bound.

The bound is not a gyro or contact stability guarantee. A prism at omega=(1,2,3),
h=.1,c_omega=.001 has negative continuous damping power but larger numerical
rotational energy after the step; the counterexample test intentionally verifies
this limitation, not an injected defect. Refinement is needed. Finite inputs
can still encounter arithmetic representability limits. Damping is relative to
a stationary environment, so the undamped Galilean-boost relation is not applied
to damped runs. External work or gravity/projection can increase energy and are
excluded from the dissipation oracles. No joints or new contact solver.

Part 3 wording clarification: accepted near-rotation matrices can differ from
their recovered unit-quaternion rotation according to the 1e-10 matrix acceptance
tolerance, not necessarily machine roundoff alone. SPEC and spatial docstring
now state this; the matrix algorithm and acceptance threshold did not change.

### Actual Part 4 commands and results

Executed from the repository root with the documented CPython 3.12.10 interpreter:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest discover -v -s Hw5 -p 'test_*.py'
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.example
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.showcase --headless
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.quaternion_example --headless
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.damping_example --headless
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.damping_example --headless --snapshot Hw5/damping.png
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.run_tests
git diff --check
```

- **52 HW5 tests passed**, including all 41 prior tests and 11 new damping
  tests, 1.547 s, exit 0 on first actual test execution.
- Part 1 example and Parts 2-3 headless examples: exit 0 with prior outputs
  preserved (Part 2 impact counts 25/5/15; Part 3 matrix residual 1.11e-16 m).
- Complete HW4/legacy suite: **58 tests passed**, 4.896 s, exit 0; runner printed
  the documented executable and Python 3.12.10 version.
- New damping headless example and optional snapshot: exit 0. At t=4 s:
  undamped speed=1.118033989 m/s, angular speed=2 rad/s,E=7.125 J;
  damped speed=.225004071 m/s,angular speed=.269316086 rad/s,E=.199098234 J.
  Unwrapped marker angles are 7.999733349 and 3.444017097 rad respectively.
  The snapshot was inspected: speed/rotation/energy, travel, marker-angle curves
  and final surface marks are visible. Physics uses 400 fixed steps of .01 s;
  no GUI timing or live GUI verification claim.

No test assertion failed and no tolerance was changed after execution. Initial
lecture-reading/new-example launches in the sandbox could not locate the
documented interpreter; approved external retries succeeded. The three known
PDF object-offset warnings did not prevent extraction. No physics fix was needed
after the first passing run. Final tracked/untracked whitespace results follow
after documentation checks. No commit or push.

Final whitespace checks passed: `git diff --check` exited 0 (the pre-existing
hw4/README.md LF/CRLF advisory only), and the exact README PowerShell block
passed all **19 HW5 text files**, including tracked/untracked files. PNGs are
binary and excluded from the text scan. Final status retained the pre-existing
root README/HW4/transcript/PDF changes; all Part 4 edits are in Hw5.

## 2026-10-22 Part 5: coupled fixed, revolute and prismatic joints

This dated addition preserves the preceding Parts 1-4 execution history. Before
implementation, inspected the current state/rigid/spatial/geometry modules,
tests, SPEC, README and logs and the actual lecture PDF. Wrote the Part 5 SPEC
first, including constraints, frames, solver, units, supported topology and failure
contract. Existing Parts 1-4 implementation/test files were not changed.
The remaining matrix phrase "accepts roundoff only" was corrected to the
documented 1e-10 near-rotation threshold; matrix behavior did not change.

### Actual lecture and exact oracle mappings

Verified from the actual 45-page `MECE 4990 Lecture 6.pdf`:
**1-based PDF page 43: "Joints"; page 44: "Joints: Oracles"**.
Page 43 describes removing 6 DOFs for fixed and 5 for prismatic/revolute,
constraint forces and stabilization. Page 44 asks for bounded long-run constraint
violations and conservative-system energy. Known PDF object-offset warnings
recurred but all requested page text was extracted. No invented printed slide
number or manual review is claimed.

All short names below have exact prefix `Hw5.test_joints.JointTests.`;
discovery prints the same module without `Hw5.`.

| Oracle / behavior | Exact tests and assertions | Assumptions / blind spots |
| --- | --- | --- |
| p43 DOFs and constraint dynamics | `test_world_prismatic_arbitrary_axis_force`, `test_world_prismatic_transverse_load_resisted`: axial acceleration/position literals with arbitrary axis and nonidentity orientation; transverse force has no motion. `test_revolute_offset_pivot_hand_acceleration`: alpha from I about pivot, not COM alone. `test_world_fixed_pose_velocity_and_offcenter_load`: world-fixed pose and zero velocity under force/torque/off-center load. | Ideal bilateral joints, prescribed constant loads, small steps; hand fixtures alone do not establish general multibody accuracy. |
| p44 bounded long-run violations | `test_long_run_revolute_arbitrary_axis_nonidentity_and_sign`: 600 steps, arbitrary world axis/nonidentity pose, q/-q and norm. `test_dynamic_prismatic_rotating_parent_transport`: 500 steps with rotating parent and changing slider coordinate; independent anchor/transport derivatives. | These cover moderate scales/conditioning and local projection; not closed loops, arbitrary stiffness/mass ratios or every topology. |
| p44 conservative energy | `test_revolute_pendulum_energy_and_first_order`: K+m*g*y drift and endpoint scalar-reference angle at common T=1, with h halving. `test_isolated_momenta_and_energy_refinement`: total momentum and kinetic-energy behavior of a consistent, isolated dynamic pair. | No damping/work/contact. No claim of exact energy conservation for a velocity/pose projection integrator. Initialization projection is excluded from conservation runs. |
| Allowed whole-assembly / relative motion | `test_two_body_fixed_coupling_and_whole_motion`: both finite bodies accelerate, center motion matches total mass, rotation remains possible. `test_two_body_revolute_relative_spin_allowed`: nonzero relative spin persists. `test_acyclic_chain_couples_three_finite_bodies`: force on one body accelerates a three-body mixed-joint chain. | Constraint satisfaction alone could be faked by freezing; these nonzero motion/force-response assertions prevent that. No full general tree performance claim. |
| Symmetry / limits / interfaces | `test_scene_rotation_symmetry`: positions, world loads/points, velocities, orientations, anchors/axes rotated consistently for all types. `test_translation_invariance_world_support_moves`: support and body move together. `test_equilibrium_zero_damping_and_no_joint_regression`: equilibrium/zero damping plus exact independent dispatch/contact records. `test_joint_load_lifetime_and_optional_damping`: one-call loads, axial damping and offset-pivot angular damping. | Gravity disabled for whole-scene rotation; static support is translated too. These symmetries can preserve a shared model error, so hand oracles remain. |
| Validation / explicit initialization | `test_validation_topology_failures_and_inputs_unchanged`: bad axes/references, self-joints, nonfinite data, cycles/redundancy, inconsistent clocks, opposed axes, excessive pose error, iteration cap, singular mass-ratio matrix and unchanged inputs. `test_stationary_world_power_and_initialization_energy`: inconsistent starts rejected; explicit projection changes energy without clock/count advancement. | Failed configurations are rejected, not silently regularized. No claim that projection initialization is conservative. |
| Executable examples | `test_joint_example_headless_smoke`, `test_joint_example_snapshot_smoke`: all three joint scenes, report output and an actual temporary Agg PNG. | Static snapshot/headless verification does not verify GUI event loops or playback performance. |

### Additional researched oracle: workless ideal reactions

Opened and verified 2026-10-22: Kevin M. Lynch and Frank C. Park,
[Modern Robotics, section 8.7, Constrained Dynamics](https://modernrobotics.northwestern.edu/nu-gm-book-resource/8-7-constrained-dynamics/),
Northwestern University textbook video supplement, transcript paragraphs on
velocity constraints and workless constraint torques. It states A*theta_dot=0,
tau_constraint dot theta_dot=0 and tau_constraint=A^T*lambda. These are the
supporting relations; the transcript does not assign them equation numbers.

Associated tests: `test_ideal_reaction_power_both_bodies` and
`test_stationary_world_power_and_initialization_energy`.
For our spatial-coordinate formulation, the same identity is
`(J^T*lambda) dot V = lambda dot (J*V)=0` for admissible instantaneous V.
Tests do NOT call the production Jacobian/residual evaluator as their oracle.
They independently rotate omega, compute anchor positions/velocities, and pair
each reported COM impulse with COM velocity and angular impulse with world omega.
They also reconstruct the anchor couple `T_anchor=T_COM-r cross P` and check
`P dot u_anchor + T_anchor dot omega` on BOTH bodies. The two calculations
agree and their sums vanish, while individual body contributions are nonzero.
Prismatic coverage uses separated anchors and a rotating parent, testing the
extra parent moment required by the transported transverse constraint.

Reported reactions are impulses, not forces: impulse dot velocity has units J.
Dividing an impulse by a chosen step h gives force-equivalent power in W and
preserves the zero identity; this is an instantaneous constraint pairing, not a
claim of exact finite-step work. For fixed-configuration velocity projection,
deltaV=M^-1*J^T*lambda and J*V_after=0. Thus
`K_after-K_before=-.5*deltaV^T*M*deltaV` for an inconsistent initial velocity.
The stationary-world test independently checks that finite energy loss as
well as the zero pairing against the final admissible velocity. Its energy
changes from 1.9900000000000002 to 1.7818181818181817 J during explicit
initialization; time/count remain zero. A stationary support contributes zero
power. Moving prescribed supports are unsupported and would require support-work
accounting. For world attachments the report's a-fields are zero sentinels,
not a claim that the balancing support wrench vanishes.

Measured impulse-velocity pairings (J), one contribution per dynamic body:

| Joint | Body a | Body b | Sum |
| --- | --- | --- | --- |
| Fixed | -.18428975436098255 | .18428975436098255 | 0 |
| Revolute | -.16578065050648888 | .16578065050648888 | 0 |
| Prismatic | -.018337680359062428 | .018337680359062435 | 6.938893903907228e-18 |

Assumptions: bilateral stationary constraints, velocity consistency at the solve
configuration, physical equal/opposite reactions with correct moments and no
friction/motor. This oracle adds reaction-direction/lever-arm/frame coverage beyond
checking residuals or energy alone. Blind spots: a reaction in a wrong constraint
subspace could be workless for selected motion; independent hand dynamics and
nonzero allowed-motion tests remain needed. It does not certify nonlinear pose
projection, which is recorded separately and can change energy/momentum.

### Independent hand dynamics and convergence derivation

World slider: unit axis n=(2,-1,2)/3, m=4, F=12*n+(3,6,0), with the second
term perpendicular to n. Hence acceleration=(F dot n)/m*n=3*n=(2,-1,2).
At T=1,h=.01, v=(2,-1,2), displacement=.5*a*T*(T+h)=(1.01,-.505,1.01)
and axial coordinate=1.515 m. These literal values use the specified
velocity-first rule, not a production constraint/reference helper.

Offset hinge: prism m=3, dimensions (2,4,2), COM Iz=5; pivot 1 m away gives
Ip=5+3*1^2=8 kg m^2. Torque 16 N m gives alpha=2 rad/s^2. At h=.001 the
velocity-kick omega_z=.002; final geometric correction is higher-order and
is allowed only 2e-10 rad/s difference. COM tangential v_y=.002 is checked
within 1e-8 m/s, allowing its O(h^2) radial component. Using COM inertia alone
would give .0032 rad/s and fail. The damping kick check similarly uses
alpha=-4/8=-.5 at omega_z=1, so old-pose constrained omega_z=.9995.

Fixed pair: masses 2+3=5, net force (5,0,0) gives assembly COM acceleration
(1,0,0). From COM x=.2 at rest, T=1,h=.01 gives x=.705 and v_x=1 while
nonzero torque rotates the assembly. Three-body chain: masses 1+2+3=6 with
6 N on its last body gives a=1, v=.2 and displacement=.021 at T=.2,h=.01.

The solver is a first-order kick/project/drift scheme. At a consistent pose,
J*V=0 gives O(h^2) uncorrected pose error after drifting. Mass-weighted pose
correction and final tangent projection remove that drift locally, but can
produce O(h^2) one-step energy/momentum error and O(h) accumulated error over
a fixed interval. Therefore first-order endpoint/refinement is expected,
not the lecture's RK4 example order and not exact conservative energy.

Pendulum reference is independent scalar dynamics:
`theta_ddot=-(m*g*L/(I_COM+m*L^2))*sin(theta)` with m=2,L=1,I_COM=.032,
theta0=.3 and theta_dot0=0. Test-local RK4 at 16384 steps to T=1 provides a
high-resolution reference, theta=-.2996001765987578 rad. This is a TEST reference
integrator only; production remains first order. Smooth scalar frequency ~3.1
rad/s and tiny reference h make reference error negligible against the ~1e-4
production errors (not a claim that production has fourth-order accuracy).

### Tolerances chosen before first execution

- Default solver: 1e-10 m/rad/m/s/rad/s in separate residual fields, max 16
  pose iterations, scaled pivot threshold 1e-12. Tests independently check
  anchor norms, alignment/relative matrices and transported anchor velocities
  within 5e-9 in each physical unit over 500/600 steps. This margin includes
  conversion from max row components to vector norms, floating-point rotations
  and iterative stopping; it is not a timestep integration-error allowance.
- Direct hand scalar/vector checks generally use 1e-9 SI, with the special
  offset-pivot budgets above. Quaternion norm uses 2e-14 absolute. Sign-equivalent
  trajectories use 1e-9 orientation/position allowance. Whole-scene rotation and
  translated-support comparisons use 1e-8 to include repeated constraint solves
  with different tangent bases/roundoff; no unrotated gravity is involved there.
- Isolated pair: max total linear-momentum error <1e-9 kg m/s; total WORLD
  angular-momentum error <.005 kg m^2/s; kinetic-energy deviation <.005 J over
  T=1 at h=.004/.002, and both latter errors must halve within ratio [.35,.65].
  The conservative error ceilings give margin for the expected O(h) drift at
  omega=.4 and metre/kg scales; refinement is the stronger accuracy requirement.
  Energy is measured independently from literal sphere inertias .2 and .3.
  Angular momentum includes x cross m*v about the same fixed world origin.
- Pendulum: common T=1, h=.01/.005/.0025, angle error <.02 rad and maximum
  K+m*g*y deviation <.15 J, each error ratio [.35,.65] under halving. These are
  integration-error budgets for moderate motion, separate from solver tolerance.
- Workless impulse pairing and independent projection-energy identity use
  1e-10 J absolute, allowing floating-point products/cancellation at O(1) J
  scale. Each body must have a nontrivial contribution >1e-4 J; all-stopped or
  zero-reaction runs cannot satisfy the test merely by producing zeros.

No tolerance was loosened after execution. Conservation runs start consistent
and perform no initialization projection; the separate initialization test
reports its energy change explicitly.

### Measured residuals and conservation/refinement

Independent long-run residuals (not the production diagnostic):

| Fixture | Max position (m) | Max orientation (rad) | Max linear velocity (m/s) | Max angular velocity (rad/s) |
| --- | --- | --- | --- | --- |
| 600-step arbitrary-axis hinge | 5.613217783960923e-16 | 2.898597830398228e-16 | 1.249000902703301e-16 | 1.3256738189514616e-16 |
| 500-step rotating-parent slider | 5.117875266520903e-16 | 1.6653345369377346e-16 | 1.9540102647498285e-16 | 0 |

Isolated fixed pair, maximum error over T=1:

| h | Total linear momentum (kg m/s) | Total world angular momentum incl. orbital (kg m^2/s) | Kinetic energy (J) |
| --- | --- | --- | --- |
| .004 | 1.616509124176106e-15 | .0006141330017770397 | .0002456176196401483 |
| .002 | 3.84752750796379e-15 | .0003071332389630310 | .0001228443964518267 |

Conservative world pendulum:

| h | Endpoint angle error (rad) | Max total mechanical-energy deviation (J) |
| --- | --- | --- |
| .01 | .0002457270383612875 | .013447851569861058 |
| .005 | .0001232364161182775 | .006774610317361152 |
| .0025 | .00006173874605014396 | .0034000491848900083 |

These approximately half-error ratios support first-order behavior. None is
reported as exact conservative energy, and no energy rescaling was used.

### API coverage and limitations

Joint/Load/SolverOptions constructors and make_joint are covered by hand, frame,
load/damping, chain and invalid-input cases. project_velocities has both reaction
work and singular-matrix coverage; project_constraints has real nonlinear pose
initialization, velocity/energy changes and an iteration-cap failure case.
joint_coordinates is checked against hand displacement/angle and visible motion;
joint_residuals is checked alongside independent anchor/velocity calculations,
not used as the sole oracle. advance_system covers all types, world/dynamic pair,
a three-body chain, optional damping, one-call load lifetime, no-joint exact
dispatch and failure-before-return without caller mutation.

Only small acyclic forests are supported. Closed loops/redundant constraints,
motors, limits, friction, moving prescribed supports and body-body collision are
not implemented. Any joints with ground=True are explicitly rejected. Extreme
mass conditioning or excessive pose error is rejected rather than silently
regularized. Finite projection can dissipate kinetic energy; pose correction
can change energy/angular momentum. Tests cover first-order finite-time drift,
not arbitrary large-step stability or indefinite long-time accuracy. Static
plot verification does not establish GUI event-loop behavior.

### Commands, actual results, failures and fixes

Executed from the repository root with documented CPython 3.12.10:

```powershell
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m unittest discover -v -s Hw5 -p 'test_*.py'
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.example
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.showcase --headless
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.quaternion_example --headless
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.damping_example --headless
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.joints_example --headless
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m Hw5.joints_example --headless --snapshot Hw5/joints.png
& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe' -B -m hw4.run_tests
git diff --check
```

- First HW5 execution: 69 tests passed, 7.813 s. Final completed suite:
  **72 tests passed**, 8.591 s, exit 0, comprising all prior 52 and 20 joint tests.
  Intermediate coverage additions and rendering failure are recorded below.
- Parts 1-4 numerical/headless examples all exited 0 with previous outputs
  preserved. HW4/legacy runner printed Python 3.12.10 and **58 tests passed**,
  5.066 s, exit 0.
- New joint headless example and final optional snapshot exited 0. All scenes
  use 300 steps of .005 s (T=1.5), without ground or prescribed paths.
  Fixed pair: both bodies share omega_z=.307079 rad/s and have distinct loaded
  velocities/positions, demonstrating coupled whole-body rotation/translation.
  Revolute coordinate=-.563765611 rad relative to its captured initial angle;
  slider coordinate=1.128750000 m, agreeing with .5*a*T*(T+h), a=1.
- Example maximum row residuals (m,rad,m/s,rad/s): fixed
  (7.859302098012222e-11,1.942890293094024e-16,5.551115123125783e-17,0);
  revolute (5.4740434407563043e-11,0,2.220446049250313e-16,0);
  prismatic (1.6653345369377348e-16,0,2.7755575615628914e-17,0).
  These are solver row diagnostics, distinct from the independent norm-based
  long-run values above.
- The initial snapshot was generated; inspection found a cropped label and
  insufficient visual distinction of initial poses. Adding ghost outlines first
  exposed a Matplotlib Poly3DCollection error with facecolor='none' (expected 5
  values, got 0). Switching to line collections exposed unequal polygon-length
  array conversion on the cylinder (caps versus side quads). The newly added
  snapshot smoke test caught this: 71-test run, 70 passed/1 error, exit 1,
  9.370 s. Fixed by representing each outline as uniform two-point edge segments.
  The corrected 71-test suite passed, 9.916 s; after adding the explicit joint
  load/damping test, the 72-test suite passed in 8.500 s. A final residual-finiteness
  validation check was then added, and 72 tests passed in 8.414 s. Local-axis
  agreement with the captured reference orientation was then explicitly validated
  for direct revolute/prismatic construction; final 72 tests passed in 8.591 s.
  Axis labels were placed inside
  panels; final PNG was regenerated and visually inspected. No live GUI claim.
- Final code review tightened the .5-rad rejection to check the angular-error
  vector norm (not just row components) and added a corresponding validation
  case plus three-body-chain coverage. An apply_patch attempt failed on an
  unmatched SPEC context; no partial edit occurred, and corrected context succeeded.
  Review also found that NaN from extreme finite input arithmetic could evade
  a max-residual comparison; explicit finite residual checks and an extreme-input
  rejection case close that gap. This did not require changing physical tolerances.
  Direct local axes must also agree through the reference orientation within
  1e-10; a mismatched local-axis case is now rejected explicitly.
- Initial lecture/new-example sandbox launches could not access the documented
  interpreter; approved external retries succeeded. Known PDF object-offset
  warnings did not prevent extraction. No check remains blocked. No physics
  test assertion failed; the only unittest failure was the plotting smoke error
  above. No tolerances or physical requirements were weakened. No intentional
  defect, commit or push.

Tracked/untracked whitespace results are appended after the final documentation scan.

Final whitespace: `git diff --check` exited 0 (only the pre-existing
hw4/README.md LF/CRLF advisory). The existing README PowerShell scan passed all
**22 HW5 text files**, including tracked/untracked files; PNGs are excluded as
binary. Final joint headless/snapshot commands were repeated after validation
review and exited 0 with identical reported results. Final status preserves the
pre-existing root README/HW4/transcript/PDF changes; Part 5 edited only Hw5.
