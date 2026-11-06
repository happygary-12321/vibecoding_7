"""Exactly thirty varied finite-mass objects and five fixed finite bin solids."""
import random
from Hw5.geometry import Prism, Sphere, Cylinder
from Hw5.rigid import RigidState
from Hw5.spatial import from_axis_angle
from .model import Body, World


def make_bin(first_id=30):
    return tuple(Body(first_id+i, Prism(1., *size), RigidState(position=center), True)
                 for i, (center, size) in enumerate((
                     ((0., -.1, 0.), (4.4, .2, 4.4)),
                     ((-2.1, 1.2, 0.), (.2, 2.4, 4.4)),
                     ((2.1, 1.2, 0.), (.2, 2.4, 4.4)),
                     ((0., 1.2, -2.1), (4., 2.4, .2)),
                     ((0., 1.2, 2.1), (4., 2.4, .2)))))


def make_scene(seed=7):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    rng, bodies = random.Random(seed), []
    for i in range(30):
        k, s, m = i//3, i % 3, .8+.1*(i % 7)
        if s == 0:
            shape = Prism(m, .38+.02*(k % 4), .32+.03*(k % 3), .40+.02*(k % 5))
        elif s == 1:
            shape = Sphere(m, .20+.015*(k % 4))
        else:
            shape = Cylinder(m, .18+.01*(k % 4), .40+.03*(k % 5))
        position = ((i % 3-1)*.9, 1.4+.9*(i//6), ((i//3) % 2-.5)*.95)
        orientation = from_axis_angle((1+i % 2, 2, 1+i % 3), rng.uniform(-.6, .6))
        omega = (.12*(i % 3-1), .08*(i % 5-2), .10*(i % 4-1))
        bodies.append(Body(i, shape, RigidState(position, orientation=orientation, omega=omega)))
    return World(tuple(bodies)+make_bin())
