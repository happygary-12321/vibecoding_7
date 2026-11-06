"""Validated immutable state and velocity-first semi-implicit Euler (SI)."""

from dataclasses import dataclass
import math

Vector3 = tuple[float, float, float]


def _scalar(value, name, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite int or float")
    try:
        value = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} is not representable") from exc
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(f"{name} must be finite" + (" and positive" if positive else ""))
    return value


def _vector(value, name):
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError(f"{name} must be a three-component tuple or list")
    return tuple(_scalar(component, name) for component in value)


@dataclass(frozen=True)
class State:
    """One particle's position, velocity, elapsed time, and completed steps."""

    position: Vector3 = (0.0, 0.0, 0.0)
    velocity: Vector3 = (0.0, 0.0, 0.0)
    time: float = 0.0
    step_count: int = 0

    def __post_init__(self):
        object.__setattr__(self, "position", _vector(self.position, "position"))
        object.__setattr__(self, "velocity", _vector(self.velocity, "velocity"))
        object.__setattr__(self, "time", _scalar(self.time, "time"))
        if self.time < 0 or type(self.step_count) is not int or self.step_count < 0:
            raise ValueError("time and integer step_count must be nonnegative")


@dataclass(frozen=True)
class Parameters:
    """Mass (kg), timestep (s), and world gravity vector (m/s^2)."""

    mass: float = 1.0
    dt: float = 1.0 / 240.0
    gravity: Vector3 = (0.0, -9.81, 0.0)

    def __post_init__(self):
        object.__setattr__(self, "mass", _scalar(self.mass, "mass", positive=True))
        object.__setattr__(self, "dt", _scalar(self.dt, "dt", positive=True))
        object.__setattr__(self, "gravity", _vector(self.gravity, "gravity"))


def step(state: State, parameters: Parameters, force: Vector3 = (0.0, 0.0, 0.0)) -> State:
    """Return a new state; force in newtons applies only to this call.

    Invalid inputs or nonfinite arithmetic raise ValueError without changing
    any input. No global state, force accumulation, contacts, or rendering.
    """
    if not isinstance(state, State) or not isinstance(parameters, Parameters):
        raise ValueError("step requires State and Parameters")
    force = _vector(force, "force")
    acceleration = _vector(tuple(g + f / parameters.mass
                                 for g, f in zip(parameters.gravity, force)), "acceleration")
    velocity = _vector(tuple(v + a * parameters.dt
                             for v, a in zip(state.velocity, acceleration)), "velocity")
    position = tuple(x + v * parameters.dt for x, v in zip(state.position, velocity))
    time = _scalar(state.time + parameters.dt, "time")
    if time <= state.time:
        raise ValueError("timestep cannot advance representable simulation time")
    return State(position, velocity, time, state.step_count + 1)
