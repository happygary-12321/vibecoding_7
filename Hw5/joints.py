"""Small coupled bilateral-constraint assemblies (SPEC.md Part 5)."""

from dataclasses import dataclass, replace
import math
from .dynamics import _scalar, _vector
from .geometry import validate_shape
from .rigid import RigidState, advance
from .spatial import (add, scale, dot, cross, rotate, unrotate, quaternion, compose,
                      inverse, multiply, from_axis_angle)

ZERO = (0.0, 0.0, 0.0)
BASIS = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


class ConstraintError(ValueError):
    """Singular, unsupported neighborhood or unconverged constraint solve."""


def _unit(value):
    v = _vector(value, "axis")
    largest = max(abs(x) for x in v)
    if largest == 0:
        raise ValueError("axis must be nonzero")
    v = scale(v, 1/largest) if largest >= 1e-300 else tuple(x/largest for x in v)
    return scale(v, 1/math.sqrt(dot(v, v)))


@dataclass(frozen=True)
class Joint:
    kind: str
    a: int | None
    b: int
    anchor_a: tuple
    anchor_b: tuple
    axis_a: tuple = (0, 0, 1)
    axis_b: tuple = (0, 0, 1)
    reference: tuple = (1, 0, 0, 0)

    def __post_init__(self):
        if self.kind not in ("fixed", "revolute", "prismatic"):
            raise ValueError("unsupported joint kind")
        if (self.a is not None and (type(self.a) is not int or self.a < 0)
                or type(self.b) is not int or self.b < 0 or self.a == self.b):
            raise ValueError("invalid or self joint body references")
        for name in ("anchor_a", "anchor_b"):
            object.__setattr__(self, name, _vector(getattr(self, name), name))
        for name in ("axis_a", "axis_b"):
            object.__setattr__(self, name, _unit(getattr(self, name)))
        object.__setattr__(self, "reference", quaternion(self.reference))
        if self.kind != "fixed" and math.dist(rotate(self.reference, self.axis_b), self.axis_a) > 1e-10:
            raise ConstraintError("local axes disagree with reference relative orientation")


@dataclass(frozen=True)
class Load:
    force: tuple = ZERO
    torque: tuple = ZERO
    force_point: tuple | None = None
    linear_damping: float = 0.0
    angular_damping: float = 0.0

    def __post_init__(self):
        for name in ("force", "torque"):
            object.__setattr__(self, name, _vector(getattr(self, name), name))
        if self.force_point is not None:
            object.__setattr__(self, "force_point", _vector(self.force_point, "force_point"))
        for name in ("linear_damping", "angular_damping"):
            value = _scalar(getattr(self, name), name)
            if value < 0:
                raise ValueError("damping must be nonnegative")
            object.__setattr__(self, name, value)


@dataclass(frozen=True)
class SolverOptions:
    position: float = 1e-10
    orientation: float = 1e-10
    linear_velocity: float = 1e-10
    angular_velocity: float = 1e-10
    max_iterations: int = 16

    def __post_init__(self):
        for name in ("position", "orientation", "linear_velocity", "angular_velocity"):
            object.__setattr__(self, name, _scalar(getattr(self, name), name, positive=True))
        if type(self.max_iterations) is not int or self.max_iterations < 1:
            raise ValueError("max_iterations must be positive int")


@dataclass(frozen=True)
class Residuals:
    position_m: float = 0.0
    orientation_rad: float = 0.0
    linear_velocity_m_s: float = 0.0
    angular_velocity_rad_s: float = 0.0


@dataclass(frozen=True)
class Reaction:
    """World COM impulses on dynamic endpoints; a=None fields are zero sentinels.

    The static support has no dynamic DOFs; its opposite wrench is not stored
    in these COM fields. Its prescribed velocity and instantaneous power are zero.
    """
    joint_index: int
    linear_a: tuple
    angular_a: tuple
    linear_b: tuple
    angular_b: tuple


@dataclass(frozen=True)
class ImpulseStage:
    before: tuple
    after: tuple
    reactions: tuple


@dataclass(frozen=True)
class SystemReport:
    residuals: Residuals
    stages: tuple = ()
    position_iterations: int = 0
    max_translation_correction: float = 0.0
    max_rotation_correction: float = 0.0
    contacts: tuple = ()


def _states(states):
    if not isinstance(states, (tuple, list)) or not 1 <= len(states) <= 16:
        raise ValueError("states must contain 1..16 bodies")
    if not all(isinstance(s, RigidState) for s in states):
        raise ValueError("expected rigid states")
    return tuple(states)


def _configuration(states, joints):
    states = _states(states)
    if not isinstance(joints, (tuple, list)) or not all(isinstance(j, Joint) for j in joints):
        raise ValueError("expected a sequence of Joint")
    parent = list(range(len(states)+1))

    def root(i):
        while parent[i] != i:
            i = parent[i]
        return i

    count = 0
    for joint in joints:
        if joint.b >= len(states) or joint.a is not None and joint.a >= len(states):
            raise ValueError("joint body index out of range")
        a = len(states) if joint.a is None else joint.a
        ra, rb = root(a), root(joint.b)
        if ra == rb:
            raise ValueError("only acyclic assemblies, including the world node, are supported")
        parent[ra] = rb
        count += 6 if joint.kind == "fixed" else 5
    if count > 96:
        raise ValueError("maximum 96 scalar joint constraints")
    return states, tuple(joints)


def _assembly(states, shapes, joints, options):
    states, joints = _configuration(states, joints)
    if not isinstance(options, SolverOptions):
        raise ValueError("expected SolverOptions")
    if not isinstance(shapes, (tuple, list)) or len(shapes) != len(states):
        raise ValueError("one shape per body required")
    for shape in shapes:
        validate_shape(shape)
    if joints and any((s.time, s.step_count) != (states[0].time, states[0].step_count) for s in states):
        raise ValueError("coupled states must have synchronized clocks/counts")
    return states, tuple(shapes), joints


def _endpoint(states, index, anchor, axis):
    if index is None:
        return anchor, ZERO, axis, (1, 0, 0, 0)
    s = states[index]
    arm = rotate(s.orientation, anchor)
    return add(s.position, arm), arm, rotate(s.orientation, axis), s.orientation


def make_joint(kind, states, a, b, anchor=(0, 0, 0), axis=(0, 0, 1)):
    """Capture coincident anchors, axes and relative orientation from world data."""
    states = _states(states)
    # Validate references before indexing (bool is not an index in this API).
    if (a is not None and (type(a) is not int or not 0 <= a < len(states))
            or type(b) is not int or not 0 <= b < len(states) or a == b):
        raise ValueError("invalid joint references")
    anchor, axis = _vector(anchor, "anchor"), _unit(axis)
    qa = (1, 0, 0, 0) if a is None else states[a].orientation
    qb = states[b].orientation
    aa = anchor if a is None else unrotate(qa, add(anchor, scale(states[a].position, -1)))
    ab = unrotate(qb, add(anchor, scale(states[b].position, -1)))
    return Joint(kind, a, b, aa, ab, unrotate(qa, axis), unrotate(qb, axis), compose(inverse(qa), qb))


def _rotation_error(q):
    q = quaternion(q)
    if q[0] < 0:
        q = scale(q, -1)
    length = math.hypot(*q[1:])
    return ZERO if length == 0 else scale(q[1:], 2*math.atan2(length, q[0])/length)


def _tangents(axis):
    base = min(BASIS, key=lambda e: abs(dot(e, axis)))
    t = _unit(cross(axis, base))
    return t, cross(axis, t)


def _rows(states, joints):
    rows = []  # (Jacobian, configuration error, 'linear'/'angular', joint index)
    for index, j in enumerate(joints):
        pa, ra, axis, qa = _endpoint(states, j.a, j.anchor_a, j.axis_a)
        pb, rb, axis_b, qb = _endpoint(states, j.b, j.anchor_b, j.axis_b)
        d = add(pb, scale(pa, -1))
        tangents = _tangents(axis)
        for t in tangents if j.kind == "prismatic" else BASIS:
            row = [0.0]*(6*len(states))
            if j.a is not None:
                row[6*j.a:6*j.a+3] = scale(t, -1)
                angular = scale(cross(ra, t), -1)
                if j.kind == "prismatic":
                    angular = add(angular, cross(t, d))
                row[6*j.a+3:6*j.a+6] = angular
            row[6*j.b:6*j.b+3] = t
            row[6*j.b+3:6*j.b+6] = cross(rb, t)
            rows.append((row, dot(t, d), "linear", index))
        if j.kind == "revolute":
            alignment = dot(axis, axis_b)
            if alignment <= 0:
                raise ConstraintError("opposed or near-perpendicular revolute axes unsupported")
            error = cross(axis, axis_b)
            length = math.hypot(*error)
            if length:
                error = scale(error, math.atan2(length, alignment)/length)
            angular_axes = tangents
        else:
            error = _rotation_error(compose(qb, inverse(compose(qa, j.reference))))
            angular_axes = BASIS
        if math.hypot(*error) > .5:
            raise ConstraintError("orientation violation outside .5 rad projection neighborhood")
        for t in angular_axes:
            row = [0.0]*(6*len(states))
            if j.a is not None:
                row[6*j.a+3:6*j.a+6] = scale(t, -1)
            row[6*j.b+3:6*j.b+6] = t
            rows.append((row, dot(t, error), "angular", index))
    return rows


def _velocities(states):
    return tuple(x for s in states for x in (*s.velocity, *rotate(s.orientation, s.omega)))


def _residual(rows, velocities):
    p = o = v = w = 0.0
    for row, error, kind, _ in rows:
        error = _scalar(error, "constraint configuration residual")
        rate = abs(_scalar(dot(row, velocities), "constraint velocity residual"))
        if kind == "linear":
            p, v = max(p, abs(error)), max(v, rate)
        else:
            o, w = max(o, abs(error)), max(w, rate)
    return Residuals(p, o, v, w)


def joint_residuals(states, joints):
    """Max constrained residuals in m, rad, m/s, rad/s (separate fields)."""
    states, joints = _configuration(states, joints)
    return _residual(_rows(states, joints), _velocities(states))


def joint_coordinates(states, joint):
    """Return the unbounded slider position or principal hinge angle (or zero)."""
    states, _ = _configuration(states, (joint,))
    pa, _, axis, qa = _endpoint(states, joint.a, joint.anchor_a, joint.axis_a)
    pb, _, _, qb = _endpoint(states, joint.b, joint.anchor_b, joint.axis_b)
    if joint.kind == "prismatic":
        return dot(axis, add(pb, scale(pa, -1)))
    if joint.kind == "revolute":
        delta = compose(compose(inverse(qa), qb), inverse(joint.reference))
        if delta[0] < 0:
            delta = scale(delta, -1)
        return 2*math.atan2(dot(delta[1:], joint.axis_a), delta[0])
    return 0.0


def _inverse_mass(states, shapes, impulse):
    result = []
    for i, (s, shape) in enumerate(zip(states, shapes)):
        result.extend(x/shape.mass for x in impulse[6*i:6*i+3])
        torque = unrotate(s.orientation, impulse[6*i+3:6*i+6])
        result.extend(rotate(s.orientation, tuple(t/m for t, m in zip(torque, shape.inertia))))
    return tuple(_scalar(x, "constraint velocity/correction") for x in result)


def _solve(states, shapes, rows, rhs):
    if not rows:
        return (), ()
    inverse_rows = [_inverse_mass(states, shapes, row[0]) for row in rows]
    k = [[dot(row[0], inv) for inv in inverse_rows] for row in rows]
    scales = [math.sqrt(_scalar(k[i][i], "constraint diagonal", positive=True)) for i in range(len(rows))]
    matrix = [[k[i][j]/scales[i]/scales[j] for j in range(len(rows))]
              + [rhs[i]/scales[i]] for i in range(len(rows))]
    n = len(rows)
    for i in range(n):
        pivot = max(range(i, n), key=lambda j: abs(matrix[j][i]))
        if abs(matrix[pivot][i]) <= 1e-12:
            raise ConstraintError("singular or ill-conditioned scaled constraint matrix")
        matrix[i], matrix[pivot] = matrix[pivot], matrix[i]
        for j in range(i+1, n):
            factor = matrix[j][i]/matrix[i][i]
            for c in range(i+1, n+1):
                matrix[j][c] -= factor*matrix[i][c]
            matrix[j][i] = 0
    solution = [0.0]*n
    for i in reversed(range(n)):
        solution[i] = (matrix[i][n]-sum(matrix[i][j]*solution[j] for j in range(i+1, n)))/matrix[i][i]
    lambdas = tuple(_scalar(x/s, "constraint multiplier") for x, s in zip(solution, scales))
    impulse = tuple(sum(lam*row[0][i] for lam, row in zip(lambdas, rows))
                    for i in range(6*len(states)))
    return lambdas, _inverse_mass(states, shapes, impulse)


def project_velocities(states, shapes, joints, *, options=SolverOptions()):
    """Mass/inertia-weighted velocity projection at fixed poses, with impulses."""
    states, shapes, joints = _assembly(states, shapes, joints, options)
    rows, v = _rows(states, joints), _velocities(states)
    lambdas, delta = _solve(states, shapes, rows, [-dot(row[0], v) for row in rows])
    if not rows:
        return states, ImpulseStage(states, states, ())
    result = tuple(replace(s, velocity=add(s.velocity, delta[6*i:6*i+3]),
                           omega=unrotate(s.orientation, add(v[6*i+3:6*i+6], delta[6*i+3:6*i+6])))
                   for i, s in enumerate(states))
    residual = _residual(rows, _velocities(result))
    if residual.linear_velocity_m_s > options.linear_velocity or residual.angular_velocity_rad_s > options.angular_velocity:
        raise ConstraintError("velocity projection residual exceeds tolerance")
    reactions = []
    for index, j in enumerate(joints):
        impulses = [0.0]*(6*len(states))
        for lam, row in zip(lambdas, rows):
            if row[3] == index:
                impulses = [x+lam*y for x, y in zip(impulses, row[0])]
        la = ZERO if j.a is None else tuple(impulses[6*j.a:6*j.a+3])
        aa = ZERO if j.a is None else tuple(impulses[6*j.a+3:6*j.a+6])
        reactions.append(Reaction(index, la, aa, tuple(impulses[6*j.b:6*j.b+3]),
                                  tuple(impulses[6*j.b+3:6*j.b+6])))
    return result, ImpulseStage(states, result, tuple(reactions))


def _pose_project(states, shapes, joints, options):
    max_translation = max_rotation = 0.0
    for iteration in range(options.max_iterations+1):
        rows = _rows(states, joints)
        residual = _residual(rows, _velocities(states))
        if residual.position_m <= options.position and residual.orientation_rad <= options.orientation:
            return states, iteration, max_translation, max_rotation
        if residual.position_m > .25 or residual.orientation_rad > .5:
            raise ConstraintError("pose violation outside supported projection neighborhood")
        if iteration == options.max_iterations:
            break
        _, delta = _solve(states, shapes, rows, [-row[1] for row in rows])
        corrected = []
        for i, s in enumerate(states):
            dx, rotation = delta[6*i:6*i+3], delta[6*i+3:6*i+6]
            length = math.hypot(*rotation)
            q = compose(from_axis_angle(rotation, length), s.orientation) if length else s.orientation
            corrected.append(replace(s, position=add(s.position, dx), orientation=q,
                                     omega=unrotate(q, rotate(s.orientation, s.omega))))
            max_translation = max(max_translation, math.hypot(*dx))
            max_rotation = max(max_rotation, length)
        states = tuple(corrected)
    raise ConstraintError("position/orientation projection iteration limit reached")


def project_constraints(states, shapes, joints, *, options=SolverOptions()):
    """Explicit initialization projection; clocks/counts unchanged, energy may change."""
    states, shapes, joints = _assembly(states, shapes, joints, options)
    states, count, dx, angle = _pose_project(states, shapes, joints, options)
    states, stage = project_velocities(states, shapes, joints, options=options)
    return states, SystemReport(joint_residuals(states, joints), (stage,), count, dx, angle)


def advance_system(states, shapes, joints, dt, *, loads=None, gravity=(0, -9.81, 0),
                   ground=False, restitution=.5, options=SolverOptions()):
    """Coupled fixed-step dynamics, or exact independent dispatch without joints."""
    states, shapes, joints = _assembly(states, shapes, joints, options)
    if type(ground) is not bool or joints and ground:
        raise ValueError("simultaneous joint/ground solving is unsupported")
    if loads is None:
        loads = (Load(),)*len(states)
    if not isinstance(loads, (list, tuple)) or len(loads) != len(states) or not all(isinstance(l, Load) for l in loads):
        raise ValueError("one Load per body required")
    if joints:
        r = joint_residuals(states, joints)
        if (r.position_m > options.position or r.orientation_rad > options.orientation
                or r.linear_velocity_m_s > options.linear_velocity or r.angular_velocity_rad_s > options.angular_velocity):
            raise ConstraintError("initial state inconsistent; call project_constraints explicitly")
    free, contacts = [], []
    for s, shape, load in zip(states, shapes, loads):
        moved, contact = advance(s, shape, dt, gravity=gravity, ground=ground, restitution=restitution,
                                 force=load.force, torque=load.torque, force_point=load.force_point,
                                 linear_damping=load.linear_damping, angular_damping=load.angular_damping)
        free.append(moved)
        contacts.append(contact)
    if not joints:
        return tuple(free), SystemReport(Residuals(), contacts=tuple(contacts))
    kicked = tuple(replace(s, velocity=f.velocity, omega=f.omega, time=f.time, step_count=f.step_count)
                   for s, f in zip(states, free))
    kicked, first = project_velocities(kicked, shapes, joints, options=options)
    trial = tuple(replace(s, position=add(s.position, scale(s.velocity, dt)),
                          orientation=quaternion(add(s.orientation, scale(multiply(s.orientation, (0, *s.omega)), dt/2))))
                  for s in kicked)
    poses, iterations, dx, angle = _pose_project(trial, shapes, joints, options)
    result, final = project_velocities(poses, shapes, joints, options=options)
    return result, SystemReport(joint_residuals(result, joints), (first, final), iterations, dx, angle)
