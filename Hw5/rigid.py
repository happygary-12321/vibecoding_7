"""Part 2 rigid bodies: body-frame Euler rotation and one ground impulse."""

from dataclasses import dataclass, replace
from .dynamics import State, Parameters, step, _scalar, _vector
from .geometry import validate_shape, ground_support
from .spatial import add, scale, cross, dot, quaternion, multiply, rotate, unrotate


@dataclass(frozen=True)
class RigidState:
    position: tuple = (0, 0, 0)
    velocity: tuple = (0, 0, 0)
    orientation: tuple = (1, 0, 0, 0)
    omega: tuple = (0, 0, 0)
    time: float = 0.0
    step_count: int = 0

    def __post_init__(self):
        point = State(self.position, self.velocity, self.time, self.step_count)
        for name in ("position", "velocity", "time", "step_count"):
            object.__setattr__(self, name, getattr(point, name))
        object.__setattr__(self, "orientation", quaternion(self.orientation))
        object.__setattr__(self, "omega", _vector(self.omega, "omega"))


@dataclass(frozen=True)
class Contact:
    lever_arm: tuple
    penetration: float
    impulse: float
    normal_speed_before: float
    normal_speed_after: float


def _inputs(state, shape):
    if not isinstance(state, RigidState):
        raise ValueError("expected RigidState")
    validate_shape(shape)


def _restitution(e):
    e = _scalar(e, "restitution")
    if not 0 <= e <= 1:
        raise ValueError("restitution must be in [0,1]")
    return e


def angular_acceleration(shape, omega, torque_body):
    """Euler equation with gyroscopic coupling; lecture PDF p35."""
    validate_shape(shape)
    omega, torque_body = _vector(omega, "omega"), _vector(torque_body, "torque")
    momentum = tuple(i*w for i, w in zip(shape.inertia, omega))
    gyro = cross(omega, momentum)
    return _vector(tuple((t-g)/i for t, g, i in zip(torque_body, gyro, shape.inertia)), "omega_dot")


def contact_velocity(state, lever_arm):
    if not isinstance(state, RigidState):
        raise ValueError("expected RigidState")
    return _vector(add(state.velocity, cross(rotate(state.orientation, state.omega),
                                            _vector(lever_arm, "lever arm"))), "contact velocity")


def resolve_ground(state, shape, restitution=0.5):
    """Endpoint projection and frictionless impulse at selected support point."""
    _inputs(state, shape)
    e = _restitution(restitution)
    r, clearance = ground_support(shape, state.position, state.orientation)
    if clearance > 0:
        return state, None
    vn = contact_velocity(state, r)[1]
    impulse = 0.0
    velocity, omega = state.velocity, state.omega
    if vn < 0:
        # k=R^T(r cross n), so k dot I_body^-1 k is rotational inverse mass.
        k = unrotate(state.orientation, cross(r, (0, 1, 0)))
        effective = _scalar(1/shape.mass + sum(x*x/i for x, i in zip(k, shape.inertia)),
                            "inverse effective mass", positive=True)
        impulse = _scalar(-(1+e)*vn/effective, "impulse")
        velocity = add(velocity, (0, impulse/shape.mass, 0))
        omega = add(omega, tuple(impulse*x/i for x, i in zip(k, shape.inertia)))
    corrected = replace(state, position=add(state.position, (0, -clearance, 0)),
                        velocity=velocity, omega=omega)
    return corrected, Contact(r, -clearance, impulse, vn, contact_velocity(corrected, r)[1])


def advance(state, shape, dt, *, gravity=(0, -9.81, 0), force=(0, 0, 0),
            torque=(0, 0, 0), force_point=None, restitution=0.5, ground=True,
            linear_damping=0.0, angular_damping=0.0):
    """Return (state, contact); explicit viscous loads, restricted dt (SPEC.md).

    External world loads and damping coefficients are supplied per call.
    Linear damping acts at COM; angular damping is in body coordinates.
    """
    _inputs(state, shape)
    if type(ground) is not bool:
        raise ValueError("ground must be bool")
    e = _restitution(restitution)
    p = Parameters(shape.mass, dt, gravity)
    c = _scalar(linear_damping, "linear_damping")
    cw = _scalar(angular_damping, "angular_damping")
    if c < 0 or cw < 0:
        raise ValueError("damping coefficients must be nonnegative")
    for coefficient, inertia, name in ((c, shape.mass, "linear"),
                                        (cw, min(shape.inertia), "angular")):
        if coefficient > 0:
            ratio = _scalar(p.dt*(coefficient/inertia), f"{name} damping step ratio")
            if ratio > 1:
                raise ValueError(f"{name} damping requires dt*coefficient/inertia <= 1")
    force, torque = _vector(force, "force"), _vector(torque, "torque")
    if force_point is not None:
        arm = add(_vector(force_point, "force point"), scale(state.position, -1))
        torque = _vector(add(torque, cross(arm, force)), "total torque")
    torque_body = unrotate(state.orientation, torque)
    if cw > 0:
        torque_body = _vector(add(torque_body, scale(state.omega, -cw)), "total body torque")
    if c > 0:
        force = _vector(add(force, scale(state.velocity, -c)), "total COM force")
    alpha = angular_acceleration(shape, state.omega, torque_body)
    omega = _vector(add(state.omega, scale(alpha, p.dt)), "omega")
    q = quaternion(add(state.orientation, scale(multiply(state.orientation, (0, *omega)), p.dt/2)))
    point = step(State(state.position, state.velocity, state.time, state.step_count), p, force)
    result = RigidState(point.position, point.velocity, q, omega, point.time, point.step_count)
    return resolve_ground(result, shape, e) if ground else (result, None)
