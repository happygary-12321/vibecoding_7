"""Analytic supports, deterministic SAP, witness GJK and support-polytope EPA.

SciPy triangulates EPA support hulls. All support queries use the true solids.
No bounding volume or display mesh is used as a final collision test.
"""
from dataclasses import dataclass
from itertools import combinations, product
import math
from scipy.spatial import ConvexHull, QhullError
from Hw5.geometry import Prism, Sphere, Cylinder
from Hw5.spatial import to_matrix
from Hw5.dynamics import _vector
from .math3 import ZERO, AXES, add, sub, mul, dot, cross, norm, unit, mv, tmv
from .model import Options


class CollisionError(RuntimeError):
    pass


def radius_bound(shape):
    if isinstance(shape, Prism):
        return math.hypot(shape.a, shape.b, shape.c)/2
    if isinstance(shape, Sphere):
        return shape.radius
    return math.hypot(shape.radius, shape.length/2)


@dataclass(frozen=True)
class AABB:
    minimum: tuple
    maximum: tuple

    def __post_init__(self):
        lo, hi = _vector(self.minimum, 'AABB minimum'), _vector(self.maximum, 'AABB maximum')
        if any(a > b for a, b in zip(lo, hi)):
            raise ValueError('AABB minimum exceeds maximum')
        object.__setattr__(self, 'minimum', lo)
        object.__setattr__(self, 'maximum', hi)


class Proxy:
    def __init__(self, body):
        self.body, self.shape = body, body.shape
        self.x, self.r = body.state.position, to_matrix(body.state.orientation)
        self.radius = radius_bound(body.shape)

    def world(self, p):
        return add(self.x, mv(self.r, p))

    def local(self, p):
        return tmv(self.r, sub(p, self.x))

    def support(self, direction):
        a = tmv(self.r, direction)
        shape = self.shape
        if isinstance(shape, Prism):
            p = tuple(math.copysign(h/2, v) if v else h/2
                      for h, v in zip((shape.a, shape.b, shape.c), a))
        elif isinstance(shape, Sphere):
            p = mul(unit(a), shape.radius)
        else:
            rho = math.hypot(a[0], a[1])
            p = (shape.radius*a[0]/rho, shape.radius*a[1]/rho) if rho else (shape.radius, 0.)
            p = (*p, math.copysign(shape.length/2, a[2]) if a[2] else shape.length/2)
        return self.world(p)


def world_aabb(body, padding=0.):
    if not math.isfinite(padding) or padding < 0:
        raise ValueError('padding must be finite and nonnegative')
    p = Proxy(body)
    shape = p.shape
    if isinstance(shape, Prism):
        ext = tuple(sum(abs(p.r[i][j])*h/2 for j, h in enumerate((shape.a, shape.b, shape.c)))
                    for i in range(3))
    elif isinstance(shape, Sphere):
        ext = (shape.radius,)*3
    else:
        ext = tuple(shape.length/2*abs(p.r[i][2])+shape.radius*math.sqrt(max(0., 1-p.r[i][2]**2))
                    for i in range(3))
    return AABB(tuple(x-e-padding for x, e in zip(p.x, ext)),
                tuple(x+e+padding for x, e in zip(p.x, ext)))


def sweep_and_prune(bodies, padding=0.):
    """Closed intervals: start endpoints precede ends at equal coordinates.

    padding=None uses the per-body Options-default contact envelope.
    """
    bodies = tuple(bodies)
    if len({b.id for b in bodies}) != len(bodies):
        raise ValueError('duplicate body ids')
    bounds = {b.id: world_aabb(b, 5e-8*max(1., 2*radius_bound(b.shape)) if padding is None else padding)
              for b in bodies}
    return sweep_bounds(tuple((b.id, bounds[b.id], b.static) for b in bodies))


def sweep_bounds(proxies):
    """SAP on (id,AABB,static) records; useful for independent test fixtures."""
    records = {i: (box, static) for i, box, static in proxies}
    if len(records) != len(proxies):
        raise ValueError('duplicate proxy ids')
    endpoints = sorted((coordinate, kind, i) for i, (box, _) in records.items()
                       for kind, coordinate in ((0, box.minimum[0]), (1, box.maximum[0])))
    active, pairs = set(), []
    for _, kind, i in endpoints:
        if kind:
            active.remove(i)
        else:
            a, sa = records[i]
            for j in sorted(active):
                b, sb = records[j]
                if not (sa and sb) and all(a.minimum[k] <= b.maximum[k] and b.minimum[k] <= a.maximum[k]
                                          for k in (1, 2)):
                    pairs.append((min(i, j), max(i, j)))
            active.add(i)
    return tuple(sorted(pairs))


@dataclass(frozen=True)
class Vertex:
    w: tuple
    a: tuple
    b: tuple


@dataclass(frozen=True)
class Witness:
    normal: tuple
    a: tuple
    b: tuple
    gap: float
    method: str


def _support(a, b, direction):
    pa, pb = a.support(direction), b.support(mul(direction, -1))
    return Vertex(sub(pa, pb), pa, pb)


def _affine(points):
    """Closest point to origin in the affine span, or None if degenerate."""
    p = points[0]
    if len(points) == 1:
        return (1.,)
    e = [sub(q, p) for q in points[1:]]
    if len(e) == 1:
        den = dot(e[0], e[0])
        if den < 1e-28:
            return None
        v = -dot(e[0], p)/den
        return (1-v, v)
    if len(e) == 2:
        normal = cross(e[0], e[1])
        det = dot(normal, normal)
        if det <= 1e-28*max(dot(e[0], e[0])*dot(e[1], e[1]), 1e-100):
            return None
        foot = sub(p, mul(normal, dot(normal, p)/det))
        delta = mul(foot, -1)
        u, v = dot(cross(delta, e[1]), normal)/det, dot(cross(e[0], delta), normal)/det
        return (1-u-v, u, v)
    det = dot(e[0], cross(e[1], e[2]))
    if abs(det) < 1e-14*max(norm(e[0])*norm(e[1])*norm(e[2]), 1e-100):
        return None
    minus = mul(p, -1)
    u = dot(minus, cross(e[1], e[2]))/det
    v = dot(e[0], cross(minus, e[2]))/det
    w = dot(e[0], cross(e[1], minus))/det
    return (1-u-v-w, u, v, w)


def _closest(vertices):
    best = None
    for size in range(1, min(4, len(vertices))+1):
        for ids in combinations(range(len(vertices)), size):
            weights = _affine([vertices[i].w for i in ids])
            if weights is None or min(weights) < -1e-12:
                continue
            weights = tuple(max(0., w) for w in weights)
            total = sum(weights)
            weights = tuple(w/total for w in weights)
            q = tuple(sum(w*vertices[i].w[k] for i, w in zip(ids, weights)) for k in range(3))
            distance2 = dot(q, q)
            if best is None or distance2 < best[0]:
                best = (distance2, ids, weights, q)
    if best is None:
        raise CollisionError('simplex closest-point failure')
    _, ids, weights, q = best
    return [vertices[i] for i in ids], weights, q


def _witness(vertices, weights, n, method):
    a = tuple(sum(w*v.a[k] for w, v in zip(weights, vertices)) for k in range(3))
    b = tuple(sum(w*v.b[k] for w, v in zip(weights, vertices)) for k in range(3))
    return Witness(n, a, b, dot(n, sub(b, a)), method)


def _analytic_sphere(a, b):
    """Sphere A versus exact solid B, including an interior sphere center."""
    shape, radius = b.shape, a.shape.radius
    if isinstance(shape, Sphere):
        n = unit(sub(b.x, a.x))
        pa, pb = add(a.x, mul(n, radius)), sub(b.x, mul(n, shape.radius))
        return Witness(n, pa, pb, norm(sub(b.x, a.x))-radius-shape.radius, 'sphere-sphere')
    c = b.local(a.x)
    if isinstance(shape, Prism):
        half = (shape.a/2, shape.b/2, shape.c/2)
        inside = all(abs(x) <= h for x, h in zip(c, half))
        p = tuple(max(-h, min(h, x)) for x, h in zip(c, half))
        if inside:
            axis = min(range(3), key=lambda j: (half[j]-abs(c[j]), j))
            p = list(c)
            p[axis] = math.copysign(half[axis], c[axis]) if c[axis] else half[axis]
            p = tuple(p)
    else:
        rho, half = math.hypot(c[0], c[1]), shape.length/2
        inside = rho <= shape.radius and abs(c[2]) <= half
        radial = (c[0]/rho, c[1]/rho) if rho else (1., 0.)
        p = (*((shape.radius*radial[0], shape.radius*radial[1]) if rho > shape.radius else c[:2]),
             max(-half, min(half, c[2])))
        if inside:
            if shape.radius-rho <= half-abs(c[2]):
                p = (shape.radius*radial[0], shape.radius*radial[1], c[2])
            else:
                p = (c[0], c[1], math.copysign(half, c[2]) if c[2] else half)
    delta = sub(p, c)
    if norm(delta):
        local_n = mul(unit(delta), -1 if inside else 1)
    else:
        # Center exactly on boundary: deterministic outward face, then inward normal.
        if isinstance(shape, Prism):
            j = min(range(3), key=lambda j: abs(abs(c[j])-half[j]))
            local_n = mul(AXES[j], -math.copysign(1., c[j]))
        elif abs(abs(c[2])-shape.length/2) < 1e-12:
            local_n = (0., 0., -math.copysign(1., c[2]))
        else:
            local_n = mul(unit((c[0], c[1], 0.)), -1)
    n = mv(b.r, local_n)
    pa, pb = add(a.x, mul(n, radius)), b.world(p)
    return Witness(n, pa, pb, dot(n, sub(pb, pa)), 'sphere-solid')


def distance_or_penetration(a, b, options):
    """Return exact analytic or iterative signed witness; raises on exhaustion."""
    ell = max(1., 2*a.radius, 2*b.radius)
    eps = options.geometry_relative*ell
    if isinstance(a.shape, Sphere):
        return _analytic_sphere(a, b)
    if isinstance(b.shape, Sphere):
        w = _analytic_sphere(b, a)
        return Witness(mul(w.normal, -1), w.b, w.a, w.gap, w.method)
    for shape, box, swapped in ((a, b, False), (b, a, True)):
        if not isinstance(box.shape, Prism):
            continue
        half = (box.shape.a/2, box.shape.b/2, box.shape.c/2)
        center = box.local(shape.x)
        outside = [j for j in range(3) if abs(center[j]) >= half[j]]
        if len(outside) != 1:
            continue
        axis = outside[0]
        footprint_inside = True
        for j in range(3):
            if j == axis:
                continue
            direction = tuple(box.r[k][j] for k in range(3))
            lo = box.local(shape.support(mul(direction, -1)))[j]
            hi = box.local(shape.support(direction))[j]
            if lo < -half[j]-eps or hi > half[j]+eps:
                footprint_inside = False
        if footprint_inside:
            outward = mul(tuple(box.r[k][axis] for k in range(3)), math.copysign(1., center[axis]))
            n = mul(outward, -1)
            pa = shape.support(n)
            plane = box.world(tuple(math.copysign(half[axis], center[axis]) if j == axis else 0. for j in range(3)))
            gap = dot(outward, sub(pa, plane))
            pb = sub(pa, mul(outward, gap))
            return Witness(mul(n, -1), pb, pa, gap, 'finite-face') if swapped else Witness(n, pa, pb, gap, 'finite-face')
    direction = sub(b.x, a.x)
    vertices = [_support(a, b, unit(direction))]
    weights, q = (1.,), vertices[0].w
    for _ in range(options.gjk_iterations):
        distance = norm(q)
        if distance <= eps:
            return _epa(a, b, vertices, options, eps)
        n = mul(q, -1/distance)
        v = _support(a, b, n)
        advance = dot(sub(v.w, q), n)
        if advance <= eps or any(norm(sub(v.w, p.w)) <= eps*.01 for p in vertices):
            return _witness(vertices, weights, n, 'gjk-distance')
        vertices.append(v)
        vertices, weights, q = _closest(vertices)
    raise CollisionError(f'GJK exhausted pair {a.body.id,b.body.id}; simplex={vertices!r}')


def _epa(a, b, simplex, options, eps):
    vertices = list(simplex)
    directions = list(AXES)+[mul(e, -1) for e in AXES]+list(product((-1., 1.), repeat=3))
    for d in directions:
        p = _support(a, b, d)
        if all(norm(sub(p.w, v.w)) > eps*.01 for v in vertices):
            vertices.append(p)
    for _ in range(16):
        try:
            hull = ConvexHull([v.w for v in vertices])
        except QhullError as exc:
            raise CollisionError(f'EPA seed degenerate pair {a.body.id,b.body.id}') from exc
        worst = max(range(len(hull.equations)), key=lambda i: hull.equations[i][3])
        plane = hull.equations[worst]
        if plane[3] <= eps*.01:
            break
        d = tuple(plane[:3])
        p = _support(a, b, d)
        if dot(d, p.w) <= eps:
            ids = hull.simplices[worst]
            face, weights, _ = _closest([vertices[int(i)] for i in ids])
            return _witness(face, weights, d, 'gjk-touch')
        if any(norm(sub(p.w, v.w)) < eps*.01 for v in vertices):
            raise CollisionError('EPA enclosure could not advance')
        vertices.append(p)
    else:
        raise CollisionError('EPA enclosure exhausted')
    for _ in range(options.epa_iterations):
        try:
            hull = ConvexHull([v.w for v in vertices])
        except QhullError as exc:
            raise CollisionError(f'EPA hull failure pair {a.body.id,b.body.id}') from exc
        faces = [(tuple(map(int, ids)), tuple(float(x) for x in plane[:3]), max(0., -float(plane[3])))
                 for ids, plane in zip(hull.simplices, hull.equations)]
        if len(faces) > options.epa_faces:
            raise CollisionError('EPA face cap exceeded')
        ids, n, depth = min(faces, key=lambda f: (f[2], f[0]))
        p = _support(a, b, n)
        advance = dot(n, p.w)-depth
        if advance <= eps:
            # Nearest coplanar triangle may not contain the foot; search all ties.
            choices = []
            for ids, fn, fd in faces:
                if abs(fd-depth) <= eps and dot(fn, n) > 1-1e-8:
                    vs, weights, q = _closest([vertices[t] for t in ids])
                    choices.append((dot(q, q), vs, weights))
            _, vs, weights = min(choices, key=lambda c: c[0])
            return _witness(vs, weights, n, 'epa')
        if any(norm(sub(p.w, v.w)) < eps*.001 for v in vertices):
            raise CollisionError(f'EPA duplicate without convergence pair {a.body.id,b.body.id}, advance={advance}')
        vertices.append(p)
    raise CollisionError(f'EPA exhausted pair {a.body.id,b.body.id}')
