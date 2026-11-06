"""Small internal tuple algebra, operating on already validated inputs."""
import math

ZERO = (0., 0., 0.)
AXES = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))


def add(a, b):
    return (a[0]+b[0], a[1]+b[1], a[2]+b[2])


def sub(a, b):
    return (a[0]-b[0], a[1]-b[1], a[2]-b[2])


def mul(a, s):
    return (a[0]*s, a[1]*s, a[2]*s)


def dot(a, b):
    return a[0]*b[0]+a[1]*b[1]+a[2]*b[2]


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def norm(a):
    return math.hypot(*a)


def unit(a):
    length = norm(a)
    return mul(a, 1/length) if length else AXES[0]


def mv(r, v):
    return (dot(r[0], v), dot(r[1], v), dot(r[2], v))


def tmv(r, v):
    return tuple(sum(r[j][i]*v[j] for j in range(3)) for i in range(3))


def tangents(n):
    axis = min(range(3), key=lambda i: (abs(n[i]), i))
    t = unit(cross(n, AXES[axis]))
    return t, cross(n, t)


def finite_scalar(value, name, minimum=0., strict=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(name+' must be numeric')
    try:
        value = float(value)
    except OverflowError as exc:
        raise ValueError(name+' is not representable') from exc
    if not math.isfinite(value) or (value <= minimum if strict else value < minimum):
        raise ValueError(name+' outside its finite range')
    return value
