"""Validated public data; shape inertia/state conventions are inherited from Hw5."""
from dataclasses import dataclass, field
import math
from Hw5.geometry import validate_shape
from Hw5.rigid import RigidState
from Hw5.dynamics import _vector
from .math3 import finite_scalar


@dataclass(frozen=True)
class Body:
    id: int
    shape: object
    state: RigidState = field(default_factory=RigidState)
    static: bool = False

    def __post_init__(self):
        if type(self.id) is not int or self.id < 0 or type(self.static) is not bool:
            raise ValueError('body requires nonnegative integer id and bool static')
        validate_shape(self.shape)
        if not isinstance(self.state, RigidState):
            raise ValueError('body requires RigidState')
        if self.static and any((*self.state.velocity, *self.state.omega)):
            raise ValueError('static body must have zero velocities')


@dataclass(frozen=True)
class Options:
    dt: float = 1/240
    gravity: tuple = (0., -9.81, 0.)
    restitution: float = .15
    friction: float = .4
    restitution_threshold: float = .5
    velocity_iterations: int = 120
    split_iterations: int = 20
    enable_split: bool = True
    slop: float = 1e-4
    beta: float = .2
    correction_depth_limit: float = .03
    max_translation: float = .01
    max_rotation: float = .05
    geometry_relative: float = 1e-8
    contact_factor: float = 5.
    break_relative: float = 1e-4
    face_angle: float = 1e-4
    incident_cap_angle: float = math.pi/4
    cache_angle: float = .08726646259971647
    perturb_angle: float = .01
    gjk_iterations: int = 64
    epa_iterations: int = 128
    epa_faces: int = 512

    def __post_init__(self):
        for name in ('dt', 'correction_depth_limit', 'max_translation', 'max_rotation',
                     'geometry_relative', 'contact_factor', 'break_relative', 'face_angle', 'incident_cap_angle',
                     'cache_angle', 'perturb_angle'):
            object.__setattr__(self, name, finite_scalar(getattr(self, name), name, strict=True))
        for name in ('restitution', 'friction', 'restitution_threshold', 'slop', 'beta'):
            object.__setattr__(self, name, finite_scalar(getattr(self, name), name))
        if self.restitution > 1 or self.beta > 1 or type(self.enable_split) is not bool:
            raise ValueError('restitution/beta must be <=1 and enable_split bool')
        for name in ('velocity_iterations', 'split_iterations', 'gjk_iterations', 'epa_iterations', 'epa_faces'):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(name+' must be a positive integer')
        object.__setattr__(self, 'gravity', _vector(self.gravity, 'gravity'))


@dataclass(frozen=True)
class World:
    bodies: tuple
    cache: tuple = ()
    time: float = 0.
    step_count: int = 0

    def __post_init__(self):
        bodies = tuple(self.bodies)
        if not all(isinstance(b, Body) for b in bodies) or len({b.id for b in bodies}) != len(bodies):
            raise ValueError('expected bodies with unique ids')
        finite_scalar(self.time, 'time')
        if type(self.step_count) is not int or self.step_count < 0:
            raise ValueError('invalid step_count')
        if any((b.state.time, b.state.step_count) != (self.time, self.step_count)
               for b in bodies if not b.static):
            raise ValueError('dynamic body clocks must match world')
        object.__setattr__(self, 'bodies', tuple(sorted(bodies, key=lambda b: b.id)))
        object.__setattr__(self, 'cache', tuple(self.cache))
