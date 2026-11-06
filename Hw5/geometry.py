"""Uniform solids; analytic support with documented tie tolerances, display meshes."""

from dataclasses import dataclass
import itertools
import math
from .dynamics import _scalar, _vector
from .spatial import add, rotate, unrotate


@dataclass(frozen=True)
class Solid:
    """Use Prism, Sphere or Cylinder, rather than constructing this base."""

    mass: float

    @property
    def center_of_mass(self):
        return (0.0, 0.0, 0.0)

    @property
    def inertia_tensor(self):
        return tuple(tuple(self.inertia[i] if i == j else 0.0 for j in range(3)) for i in range(3))

    def _validate(self, dimensions):
        for name in ("mass", *dimensions):
            object.__setattr__(self, name, _scalar(getattr(self, name), name, positive=True))
        for moment in self.inertia:
            _scalar(moment, "inertia", positive=True)


@dataclass(frozen=True)
class Prism(Solid):
    a: float
    b: float
    c: float

    def __post_init__(self):
        self._validate(("a", "b", "c"))

    @property
    def inertia(self):
        return tuple(self.mass/12*(x*x+y*y) for x, y in
                     ((self.b, self.c), (self.a, self.c), (self.a, self.b)))

    def vertices(self):
        return tuple(itertools.product((-self.a/2, self.a/2),
                                       (-self.b/2, self.b/2), (-self.c/2, self.c/2)))


@dataclass(frozen=True)
class Sphere(Solid):
    radius: float

    def __post_init__(self):
        self._validate(("radius",))

    @property
    def inertia(self):
        return (0.4*self.mass*self.radius*self.radius,)*3


@dataclass(frozen=True)
class Cylinder(Solid):
    radius: float
    length: float

    def __post_init__(self):
        self._validate(("radius", "length"))

    @property
    def inertia(self):
        transverse = self.mass/12*(3*self.radius*self.radius+self.length*self.length)
        return (transverse, transverse, self.mass*self.radius*self.radius/2)


def validate_shape(shape):
    if type(shape) not in (Prism, Sphere, Cylinder):
        raise ValueError("expected Prism, Sphere or Cylinder")


def ground_support(shape, position, orientation):
    """Return (world COM-to-support lever arm, signed ground clearance)."""
    validate_shape(shape)
    position = _vector(position, "position")
    down = unrotate(orientation, (0, -1, 0))
    if isinstance(shape, Sphere):
        r = (0, -shape.radius, 0)
    elif isinstance(shape, Prism):
        vertices = tuple(rotate(orientation, v) for v in shape.vertices())
        lowest = min(v[1] for v in vertices)
        tied = [v for v in vertices if v[1] <= lowest + 1e-12]
        r = tuple(sum(v[i] for v in tied)/len(tied) for i in range(3))
    else:
        radial = math.hypot(down[0], down[1])
        x, y = (0, 0) if radial < 1e-14 else (
            shape.radius*down[0]/radial, shape.radius*down[1]/radial)
        z = 0 if abs(down[2]) < 1e-14 else math.copysign(shape.length/2, down[2])
        r = rotate(orientation, (x, y, z))
    return r, _scalar(position[1]+r[1], "clearance")


def world_mesh(shape, position, orientation, segments=24):
    """Return polygon faces in world coordinates; curvature is display-only."""
    validate_shape(shape)
    position = _vector(position, "position")
    if type(segments) is not int or segments < 8:
        raise ValueError("segments must be an integer >=8")
    if isinstance(shape, Prism):
        vertices = shape.vertices()
        faces = [[vertices[i] for i in face] for face in
                 ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1),
                  (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3))]
    elif isinstance(shape, Cylinder):
        rings = [[(shape.radius*math.cos(2*math.pi*j/segments),
                   shape.radius*math.sin(2*math.pi*j/segments), z)
                  for j in range(segments)] for z in (-shape.length/2, shape.length/2)]
        faces = [rings[0], rings[1]] + [
            [rings[0][j], rings[0][(j+1) % segments], rings[1][(j+1) % segments], rings[1][j]]
            for j in range(segments)]
    else:
        rings = [[(shape.radius*math.sin(math.pi*k/(segments//2))*math.cos(2*math.pi*j/segments),
                   shape.radius*math.sin(math.pi*k/(segments//2))*math.sin(2*math.pi*j/segments),
                   shape.radius*math.cos(math.pi*k/(segments//2)))
                  for j in range(segments)] for k in range(segments//2+1)]
        faces = [[rings[k][j], rings[k][(j+1) % segments],
                  rings[k+1][(j+1) % segments], rings[k+1][j]]
                 for k in range(segments//2) for j in range(segments)]
    return tuple(tuple(_vector(add(position, rotate(orientation, v)), "world vertex")
                       for v in face) for face in faces)
