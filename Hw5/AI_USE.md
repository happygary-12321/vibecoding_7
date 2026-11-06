# Agent-use record

The user requested HW5 Part 1 only: validated 3D point-mass stepping, independent
tests, lecture/researched oracle mapping, a headless example and documentation;
preserve HW3/HW4 and do not commit or push. This record was written by Codex,
not by the user. One agent performed the work; no subagents were used.

Inspected root README, assign3/SPEC.md, state.py, integration.py, validation.py,
HW4 README/runner and analytical/conservation/convergence/symmetry/limiting tests.
Searched repository and ancestor directories for AGENTS.md: none found.
The initial broad read was truncated; targeted reads followed. Optional absent
ancestor-file checks returned exit 1, without blocking inspection. Existing
user changes were `hw4/README.md` and untracked `hw4/transcript/`; preserved.
The empty lowercase `hw5` directory was renamed via a temporary name to `Hw5`.

Design: standard-library frozen dataclasses, three-component tuple snapshots,
per-call force, velocity-first Euler, explicit elapsed time and step count,
finite result checks, no shared global state or speculative rigid-body systems.
Agent authored `Hw5/__init__.py`, `dynamics.py`, `example.py`,
`test_dynamics.py`, `SPEC.md`, `README.md`, `LOG.md`, and this `AI_USE.md`;
added only a short HW5 link to the root README. No HW3 source/HW4 test edits.

Tools/commands: PowerShell Get-Content/Get-ChildItem, rg --files (including hidden
paths for instructions/slides), git status --short, git ls-files; apply_patch
for source/docs. External web search found Galilean transformation references.
Opening the University of Virginia page timed out; the UT Austin source was
successfully opened and used instead. Lecture materials were unavailable;
the required actual course slide/page mapping is explicitly pending in LOG.md.

Test tolerances were selected before running tests. Exact verification commands
are in README.md; actual execution results and any failures/fixes follow below.

Execution on 2026-10-22: the combined version/new-tests/example launch initially
returned CommandNotFoundException for the documented interpreter in the sandbox.
The independently issued, previously approved HW4 runner succeeded (58 tests,
exit 0) and identified CPython 3.12.10. Requested execution escalation for the
new unittest command and example because of interpreter access; both approved
retries succeeded (10 tests, exit 0; example exit 0). This was an environment
launch failure, not a failing physics test. No implementation or tolerance
changes were made after test execution. Example output and verification details
are in LOG.md. No commits, pushes, intentional bugs, or Parts 2-5 were performed.
Final `git diff --check` passed (exit 0), with an LF/CRLF advisory for the
pre-existing hw4/README.md change. `git status --short` confirmed the new Hw5
folder and root README edit alongside the preserved pre-existing HW4 changes.

## 2026-10-22 supplement: supplied Lecture 6 and arbitrary gravity

This dated addition follows PDF page 31, "Good attribution", and page 32,
"Attribution templates". The original entries above are historical records:
the lecture was unavailable then and was supplied for this supplement.

- Tool: Codex via shell, apply_patch and the PDF skill; pypdf for reading.
  Actual model/version: **not recorded** (no verified runtime identifier is
  available). No model identity is inferred from the agent's product name.
- Prompt/spec reference: the user's follow-up beginning "Supplement the
  existing HW5 Part 1 using the supplied MECE 4990 Lecture 6.pdf", its six
  requirements, current Hw5/SPEC.md, and actual PDF pages 7-8, 11-12, 31-32,
  35-38. One agent did the work; no human review or subagent work is claimed.
- Files changed in this supplement: `Hw5/test_dynamics.py`, `Hw5/LOG.md`,
  `Hw5/SPEC.md`, `Hw5/README.md`, `Hw5/AI_USE.md`. No production physics code,
  HW3/HW4 files, root README, or supplied PDF were edited in this supplement.
- Changes: verified lecture categories and exact test/assertion mappings;
  retained the UT Austin Galilean source and discrete proof separately;
  added literal hand-calculated arbitrary-gravity coverage with zero tolerance;
  documented future rotational and geometry requirements without implementing them.
- Issues/fixes: the first PDF extraction could not launch the interpreter in
  the sandbox; an approved external retry reached Python but failed printing
  page 8 under the console's GBK encoding. Setting stdout to UTF-8 fixed it.
  Pypdf reported three incorrect object offsets (198, 226, 227), but extracted
  all requested pages successfully from the 45-page document. No PDF repair
  was made. No Poppler command or fitz/pypdfium2 package was available; a search
  of bundled files also encountered two inaccessible app-server directories.
  Page text was inspected; no visual-render fidelity claim is made.
- Coverage issue found: arbitrary non-y gravity was specified but untested.
  Fixed by `test_arbitrary_gravity_hand_step_mass_independence`, using masses
  .5 and 8, g=(1,-2,3), zero force and h=.25. It verifies all physical values,
  metadata and unchanged inputs. Existing tolerances were not changed.
- Verification used the documented CPython 3.12.10 interpreter from the root:
  `& 'C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe'`
  with each of these exact argument lists: `-B -m unittest -v Hw5.test_dynamics`
  (11 tests passed, 0.011 s, exit 0), `-B -m Hw5.example` (exit 0, 100 steps,
  position (4.01,1.56095,1.495), velocity (4,-3.81,-2)), and
  `-B -m hw4.run_tests` (58 tests passed, 4.465 s, exit 0).
  Full copyable commands are also in README.md and the LOG.md supplement.
  `git diff --check` passed, exit 0, with the existing hw4/README.md LF/CRLF
  advisory. The exact PowerShell whitespace block in README.md passed on all
  8 HW5 text files, including untracked files. No test initially failed;
  the inspection failures and fixes are recorded above. Final status/diff
  inspection showed only the pre-existing changes outside Hw5.
- No commit or push was made; no reviewer or past execution evidence is invented.

## 2026-10-22 Part 2: solids, rotation and ground contact

- Tool: Codex with shell/apply_patch, PDF skill and web research. Actual
  model/version: **not recorded**; no verified runtime model identifier was
  supplied. One agent performed the work, without subagents or claimed human review.
- Prompt: user request "Implement HW5 Part 2: three solid geometries, 3D
  rotational dynamics, and ground contact", including its seven requirements.
  Inspected current Part 1 code/SPEC/README, historical logs/tests, root dependency
  conventions and actual Lecture 6 PDF before editing. No AGENTS.md was found.
  Wrote the Part 2 SPEC section before writing implementation.
- Design: preserve Part 1 modules/exports; separate immutable RigidState and
  solid-shape API; body-frame omega and full Euler gyroscopic term; normalized
  Hamilton body-to-world quaternion update without angular-velocity normalization;
  velocity-first translation; world force/torque and optional off-center force;
  exact shape support with one selected ground resultant and rotational effective
  mass. Damping/joints and full Part 3 quaternion work remain out of scope.
- Added files: `Hw5/spatial.py`, `Hw5/geometry.py`, `Hw5/rigid.py`,
  `Hw5/test_rigid.py`, `Hw5/test_inertia.py`, `Hw5/showcase.py`,
  `Hw5/test_showcase.py`, and generated `Hw5/showcase.png`.
  Updated `Hw5/SPEC.md`, `Hw5/README.md`, `Hw5/LOG.md`, `Hw5/AI_USE.md`.
  No Part 1 code/tests, HW3/HW4, root README, or lecture PDF were edited.
- Research: re-extracted actual lecture pages 35-38 (and the earlier oracle and
  attribution pages) with pypdf/UTF-8. Known PDF object-offset warnings recurred;
  extraction succeeded. Verified MIT OCW L26 PDF page 7, Parallel Axis Theorem,
  and page 3 tensor signs. Test-local interior quadrature includes all nine
  entries and volume weighting; no production formula generates the samples.
  Sources, assumptions, derivations and exact oracle/test mappings are in LOG.md.
- Validation: test tolerances were chosen in the test files before running.
  All 29 HW5 tests passed on first actual execution (0.857 s); the 11 Part 1
  tests remain intact. The Part 1 example passed with its prior output; both
  new headless showcase commands passed; 58 complete HW4/legacy tests passed
  (4.581 s). Python version 3.12.10 was printed by the HW4 runner.
  Exact commands, all with interpreter
  `C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe`, were:
  `-B -m unittest discover -v -s Hw5 -p 'test_*.py'`, `-B -m Hw5.example`,
  `-B -m Hw5.showcase --headless`,
  `-B -m Hw5.showcase --headless --snapshot Hw5/showcase.png`, and
  `-B -m hw4.run_tests`. Full copyable PowerShell commands are in LOG.md/README.md.
- Issues/fixes: sandbox launches of the new test/showcase commands reported
  the interpreter unavailable. Approved external retries succeeded, without
  changing code or tolerances. No physics assertion failed. Final documentation
  clarifies historical Part 1 future-status statements rather than erasing them.
  The single-contact face limitation is an explicit tested design limit, not
  hidden by a stronger solver claim.
- Visualization: reused existing Matplotlib, produced an Agg PNG, and inspected
  the frame with view_image. All solids/ground/markers are visible. No human
  review or live GUI playback is claimed. No new dependency was installed.
- Final whitespace commands: `git diff --check` and the README PowerShell scan
  of every `.py`/`.md` under Hw5, including untracked files. Results are recorded
  in LOG.md: both passed, all 15 HW5 text files checked; only the pre-existing
  hw4/README.md LF/CRLF advisory. Nothing committed or pushed.

## 2026-10-22 Part 3: complete quaternion rotation utilities

- Tool: Codex using shell, apply_patch, pypdf, web research and view_image.
  The session instructions describe the agent as based on GPT-6; the exact
  deployed model identifier/version is **not recorded**. No human review or
  subagent participation is claimed.
- Prompt reference: user's "Implement HW5 Part 3: complete and verify quaternion
  rotations" and its seven numbered requirements. Inspected spatial.py,
  rigid.py, geometry.py, existing tests, SPEC/README/logs and the actual lecture
  PDF before changes. The broad read was truncated, followed by targeted reads.
  Specified the Part 3 contract before implementation. The lecture search
  verified PDF page 39, Quaternions, and 40, Quaternions: Oracles.
- Design: extend existing normalized Hamilton (w,x,y,z) body-to-world convention;
  add axis-angle, rotation inverse/conjugate, explicit-order composition,
  quaternion/matrix conversion, largest-component extraction near pi, strict
  matrix validity checks and sign-invariant atan2/chord orientation distance.
  Preserve normalized Euler stepping and body-frame omega. Algebraic multiply
  stays unnormalized for kinematics. No solver/integrator change was needed.
- Files changed: `Hw5/spatial.py`, `Hw5/geometry.py` (docstring only),
  `Hw5/SPEC.md`, `Hw5/README.md`, `Hw5/LOG.md`, `Hw5/AI_USE.md`.
  Added `Hw5/test_quaternions.py`, `Hw5/quaternion_example.py`, and generated
  `Hw5/quaternions.png`. Part 1 code/tests, rigid.py, existing Part 2 tests and
  their independent test-local matrix reference were preserved. All edits are
  under Hw5; no HW3/HW4, root README or supplied PDF edits.
- Research: verified the Illinois TAM212 Rotations and Angular Velocity page,
  Rodrigues' rotation formula section and its displayed vector equation. The
  new test-local Rodrigues reference calls no production helpers. Existing
  Galilean and parallel-axis research records are retained.
- Verification: documented Python 3.12.10 (version printed by HW4 runner), root
  working directory. Commands and results:
  `-B -m unittest discover -v -s Hw5 -p 'test_*.py'`: 41 tests passed, 1.294 s;
  `-B -m Hw5.example`: passed, original output;
  `-B -m Hw5.showcase --headless`: passed, original outputs/impact counts;
  `-B -m Hw5.quaternion_example --headless`: passed;
  `-B -m Hw5.quaternion_example --headless --snapshot Hw5/quaternions.png`:
  passed and image inspected;
  `-B -m hw4.run_tests`: 58 tests passed, 4.584 s. All successful commands
  exited 0. Exact full interpreter commands are in the dated LOG.md section.
  Test tolerances were written before execution and were not loosened.
- Failures/fixes: initial lecture extraction and Part 3 example launches in the
  sandbox reported the documented interpreter unavailable. Approved retries
  outside it succeeded. Known PDF object-offset warnings did not prevent text
  extraction. No physics test assertion failed. Initial optional image inspection
  found clipped labels and an obscured corner marker; tight image bounds and
  explicit marker layering fixed them, followed by successful regeneration and
  visual inspection. No live GUI/manual human review is claimed.
- Final whitespace verification covers tracked changes plus all `.py`/`.md`
  files under Hw5, including untracked files, using the README PowerShell block.
  Final results are recorded in LOG.md. No damping/joints, intentional defects,
  commits or pushes were introduced.
  Both checks passed: git diff --check exit 0 (existing hw4/README.md LF/CRLF
  advisory only), and all 17 HW5 text files passed the whitespace scan.

## 2026-10-22 Part 4: linear and angular viscous damping

- Tool: Codex with shell, apply_patch, pypdf, web research and view_image.
  The session describes the agent as based on GPT-6; exact runtime model
  identifier/version is **not recorded**. One agent worked without subagents;
  no human review or manual live GUI verification is claimed.
- Prompt reference: user's "Implement HW5 Part 4: linear and angular viscous
  damping" and its seven requirements. Inspected current implementation,
  tests, SPEC/README/logs and actual Lecture 6 PDF. Broad reads were truncated
  and followed by targeted reads. No AGENTS.md was found. The Part 4 SPEC was
  updated before implementing damping. PDF pages 41/42 were verified as Damping
  and Damping: Oracles (1-based PDF pages).
- Design: optional `linear_damping`/`angular_damping` keywords, finite nonnegative
  coefficients default zero, world COM viscous force and body viscous torque.
  Explicit old-velocity evaluation preserves the existing gyro/quaternion/contact
  ordering. Enforce h*c/m<=1,h*c_omega/min(I)<=1 for nonreversing isolated damping.
  Bypass zero-coefficient arithmetic to preserve the undamped path. Explicit gyro
  still has numerical energy drift; no normalization of omega, clamp or energy
  rescaling. External off-center torque uses external force only. No joints.
- Files changed: `Hw5/rigid.py`, `Hw5/spatial.py` (matrix tolerance docstring
  clarification only), `Hw5/SPEC.md`, `Hw5/README.md`, `Hw5/LOG.md`,
  `Hw5/AI_USE.md`. Added `Hw5/test_damping.py`, `Hw5/damping_example.py` and
  generated `Hw5/damping.png`. No prior tests or Part 1 code, HW3/HW4, root README,
  lecture PDF, or prior images were edited. Historical results remain intact.
- Research: verified Douglas Cline's authored mechanics textbook section 10.4
  Rayleigh's Dissipation Function, hosted by LibreTexts with University of
  Rochester attribution/source, especially the displayed dissipation-power
  relation and eq (10.15). Also inspected Stutts' university notes section 3.2
  during research. LOG.md cites the actual oracle source and identifies our
  rigid-body power derivation separately. The associated nonspherical test
  evaluates energy independently from literal mass/inertia and measures h->0
  power convergence beyond exponential special cases.
- Verification with documented CPython 3.12.10: 52 HW5 tests passed, 1.547 s;
  Parts 1-3 headless examples passed with previous outputs; the new damping
  headless example and optional Agg snapshot passed; 58 HW4/legacy tests passed,
  4.896 s. Every successful command exited 0. Exact interpreter/path commands
  are in the dated Part 4 LOG.md section and README.md. Argument lists executed:
  `-B -m unittest discover -v -s Hw5 -p 'test_*.py'`, `-B -m Hw5.example`,
  `-B -m Hw5.showcase --headless`, `-B -m Hw5.quaternion_example --headless`,
  `-B -m Hw5.damping_example --headless`,
  `-B -m Hw5.damping_example --headless --snapshot Hw5/damping.png`,
  and `-B -m hw4.run_tests`.
- Failures/fixes: first sandbox launches of the new lecture-reader and damping
  example could not access the documented interpreter. Approved external retries
  succeeded. Known PDF object-offset warnings recurred but extraction succeeded.
  No test initially failed, and no test tolerance was loosened. Matrix wording
  was corrected to the acceptance-tolerance contract without changing matrix
  conversion behavior. The damping snapshot was generated and visually inspected;
  it shows the comparison without clipped labels or a need for presentation fixes.
- Final whitespace checks use `git diff --check` plus the README PowerShell
  scan of all HW5 `.py`/`.md`, including untracked files. Actual final results
  are appended to LOG.md. No intentional defects, commits or pushes.
  Both checks passed: git diff --check exit 0 with the existing HW4 LF/CRLF
  advisory, and 19 HW5 text files passed the tracked/untracked whitespace scan.

## 2026-10-22 Part 5: coupled ideal joints

- Tool: Codex using shell, apply_patch, pypdf, web research and view_image.
  Session instructions describe the agent as based on GPT-6; exact deployed
  model identifier/version is **not recorded**. One agent worked, no subagents,
  and no human review or manual live GUI verification is claimed.
- Prompt/spec reference: user's "Implement HW5 Part 5: fixed, revolute, and
  prismatic joints" and its seven numbered requirements; current Parts 1-4
  modules/tests/SPEC/README/logs and the supplied MECE 4990 Lecture 6 PDF.
  Read before editing; broad output truncation was followed by targeted reads.
  No AGENTS.md was found. Wrote the Part 5 SPEC before implementation.
  Verified actual 1-based PDF pages 43, Joints, and 44, Joints: Oracles.
- Design: separate immutable Joint/Load/SolverOptions and assembly API; finite
  dynamic bodies plus a stationary world with no fake mass; local anchors/axes
  and captured relative quaternion. Dense mass/world-inertia-weighted Jacobian
  impulse solve with gyro/load/damping kicks, constrained drift, pose projection
  and final velocity projection. Angular anchor terms and rotating-parent slider
  transport moment are included. Separate physical residual units and reaction
  stages; initialization projection explicitly reports its energy implications.
  Forest topology only, singular/large-error/failed solves explicitly rejected;
  no joint/ground combination, motors, limits, friction or moving supports.
- Files added: `Hw5/joints.py`, `Hw5/test_joints.py`, `Hw5/joints_example.py`,
  generated `Hw5/joints.png`. Files updated: `Hw5/SPEC.md`, `Hw5/README.md`,
  `Hw5/LOG.md`, `Hw5/AI_USE.md`. No previous implementation/test modules or
  HW3/HW4/root README/lecture PDF files were edited. Historical Parts 1-4 runs
  are preserved. Corrected the remaining SPEC matrix "roundoff only" wording.
- Research: opened Northwestern's Modern Robotics section 8.7, Constrained
  Dynamics (Lynch/Park), including the transcript's workless constraint relation,
  velocity Jacobian and transpose reaction form. LOG.md provides the actual URL,
  supporting relations, independent two-body/anchor power derivation, discrete
  impulse interpretation and exact tests. No invented equation numbers.
- Verification commands used the documented
  `C:\Users\omen16\AppData\Local\Programs\Python\Python312\python.exe` from root:
  `-B -m unittest discover -v -s Hw5 -p 'test_*.py'`, `-B -m Hw5.example`,
  `-B -m Hw5.showcase --headless`, `-B -m Hw5.quaternion_example --headless`,
  `-B -m Hw5.damping_example --headless`, `-B -m Hw5.joints_example --headless`,
  `-B -m Hw5.joints_example --headless --snapshot Hw5/joints.png`,
  `-B -m hw4.run_tests`. Exact copyable commands are in LOG.md/README.md.
  Final HW5 result: **72 passed**, 8.591 s (all previous 52 plus 20 joint tests).
  HW4: **58 passed**, 5.066 s; Python 3.12.10 printed by that runner. All prior
  examples and final joint commands exited 0. Snapshot inspected after fixes.
- Actual failures/fixes: sandbox could not launch the new PDF-reader and joint
  example commands; approved external retries succeeded. Known PDF object-offset
  warnings did not prevent extraction. One apply_patch attempt failed on an
  unmatched SPEC context with no partial mutation; corrected context succeeded.
  Initial numeric suites passed (69 tests, then 70 after chain/validation additions).
  Snapshot improvement exposed a Matplotlib transparent-face Poly3DCollection
  error. Switching to Line3DCollection exposed ragged cap/side polygon lengths;
  the newly added snapshot test produced a 71-test run with 1 error, 9.370 s.
  Fixed by drawing uniform two-point edges; 71 tests then passed in 9.916 s.
  Added explicit joint-load/damping coverage: 72 passed in 8.500 s. Code review
  had tightened angular-neighborhood validation to vector norm before the 70-test
  run. Residual arithmetic finiteness (NaN must not evade max checks) was added
  with a rejection case: 72 passed in 8.414 s. Direct local-axis/reference
  agreement was then explicitly validated with a rejection case; final 72 passed
  in 8.591 s. No physical test expectation or tolerance was weakened.
  Axis labels were moved inside panels to avoid cropping. Final PNG shows
  recognizable solids, initial-pose outlines, anchors/axes and COM trails.
- Tests independently compute anchor velocity, rotational/transport terms,
  pivot inertia, scalar pendulum reference, world/orbital angular momentum and
  reaction-work pairings. No production residual evaluator is the sole oracle.
  Conservation fixtures start consistent; initialization projection is recorded
  separately. Solver correction can dissipate/change energy; limitations remain
  explicit instead of being hidden by rescaling.
- Final whitespace checks: `git diff --check` and the existing README PowerShell
  scan including all tracked/untracked HW5 text files. Actual final counts are
  recorded in LOG.md. No checks remain blocked, and no intentional defects,
  commits or pushes were introduced.
  Final checks passed: git diff --check exit 0 with only the existing HW4
  LF/CRLF advisory, and all 22 HW5 text files passed the tracked/untracked scan.
  Final joint headless and snapshot commands were repeated after validation
  review and returned 0 with identical numerical results.
