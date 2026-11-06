"""Vector algebra and active Hamilton (w,x,y,z) body-to-world rotations."""

import math
from .dynamics import _scalar, _vector


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def scale(a, s):
    return tuple(x * s for x in a)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def quaternion(q):
    """Copy/normalize finite nonzero (w,x,y,z), robust to large magnitudes."""
    if not isinstance(q, (list, tuple)) or len(q) != 4:
        raise ValueError("orientation must have four components")
    q = tuple(_scalar(x, "quaternion") for x in q)
    largest = max(abs(x) for x in q)
    if largest == 0:
        raise ValueError("zero quaternion")
    q = tuple(x/largest for x in q)
    norm = math.sqrt(dot(q, q))
    return tuple(x/norm for x in q)


def multiply(q, p):
    """Internal algebraic product of validated four-vectors; no normalization."""
    return (q[0]*p[0]-dot(q[1:], p[1:]),
            *add(add(scale(p[1:], q[0]), scale(q[1:], p[0])), cross(q[1:], p[1:])))


def rotate(q, vector):
    """Body to world, with validated vector and normalized orientation."""
    q, vector = quaternion(q), _vector(vector, "vector")
    t = scale(cross(q[1:], vector), 2)
    return _vector(add(vector, add(scale(t, q[0]), cross(q[1:], t))), "rotated vector")


def unrotate(q, vector):
    q = quaternion(q)
    return rotate((q[0], -q[1], -q[2], -q[3]), vector)


def from_axis_angle(axis, angle):
    """Construct an active right-handed rotation; angle in radians (SPEC.md)."""
    axis, angle = _vector(axis, "axis"), _scalar(angle, "angle")
    if angle == 0:
        return (1.0, 0.0, 0.0, 0.0)
    largest = max(abs(x) for x in axis)
    if largest == 0:
        raise ValueError("nonzero angle requires a nonzero axis")
    unit = tuple(x/largest for x in axis)
    length = math.sqrt(dot(unit, unit))
    return quaternion((math.cos(angle/2),
                       *(x/length*math.sin(angle/2) for x in unit)))


def conjugate(q):
    """Conjugate of normalized rotation q; its world-to-body inverse."""
    w, x, y, z = quaternion(q)
    return (w, -x, -y, -z)


def inverse(q):
    """Rotation inverse (not general non-unit quaternion algebra)."""
    return conjugate(q)


def compose(after, before):
    """Apply before, then after: normalized Hamilton product after*before."""
    return quaternion(multiply(quaternion(after), quaternion(before)))


def to_matrix(q):
    """Return R for world column vector R*v_body, in immutable rows."""
    w, x, y, z = quaternion(q)
    return ((1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)),
            (2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)),
            (2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)))


MATRIX_TOL = 1e-10  # absolute bound on each R^T R-I entry and det(R)-1


def from_matrix(matrix):
    """Validate a proper rotation and extract its largest quaternion component.

    Accept residuals <=MATRIX_TOL; recovered-rotation discrepancy is governed
    by that tolerance, not necessarily machine roundoff. No arbitrary projection.
    Largest-component branching remains well-conditioned at a half turn.
    """
    if not isinstance(matrix, (tuple, list)) or len(matrix) != 3:
        raise ValueError("matrix must have three rows")
    r = tuple(_vector(row, "matrix row") for row in matrix)
    for i in range(3):
        for j in range(3):
            if abs(sum(r[k][i]*r[k][j] for k in range(3))-(i == j)) > MATRIX_TOL:
                raise ValueError("matrix is not orthogonal within tolerance")
    determinant = _scalar(dot(r[0], cross(r[1], r[2])), "determinant")
    if abs(determinant-1) > MATRIX_TOL:
        raise ValueError("matrix must have determinant +1")
    candidates = (1+r[0][0]+r[1][1]+r[2][2],
                  1+r[0][0]-r[1][1]-r[2][2],
                  1-r[0][0]+r[1][1]-r[2][2],
                  1-r[0][0]-r[1][1]+r[2][2])
    index = max(range(4), key=lambda i: candidates[i])
    s = 2*math.sqrt(candidates[index])
    if index == 0:
        q = (s/4, (r[2][1]-r[1][2])/s, (r[0][2]-r[2][0])/s, (r[1][0]-r[0][1])/s)
    elif index == 1:
        q = ((r[2][1]-r[1][2])/s, s/4, (r[0][1]+r[1][0])/s, (r[0][2]+r[2][0])/s)
    elif index == 2:
        q = ((r[0][2]-r[2][0])/s, (r[0][1]+r[1][0])/s, s/4, (r[1][2]+r[2][1])/s)
    else:
        q = ((r[1][0]-r[0][1])/s, (r[0][2]+r[2][0])/s, (r[1][2]+r[2][1])/s, s/4)
    return quaternion(q)


def angular_distance(q, p):
    """Stable sign-invariant orientation difference in radians, in [0,pi]."""
    q, p = quaternion(q), quaternion(p)
    difference = math.dist(q, p)
    total = math.sqrt(sum((a+b)**2 for a, b in zip(q, p)))
    return 4*math.atan2(min(difference, total), max(difference, total))
