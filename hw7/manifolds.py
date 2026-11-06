"""Persistent analytic-surface anchors, face clipping and perturbation enrichment."""
from dataclasses import dataclass, replace
import math
from Hw5.geometry import Prism, Sphere, Cylinder
from Hw5.spatial import compose, from_axis_angle
from .collision import Proxy, distance_or_penetration
from .model import Options
from .math3 import add, sub, mul, dot, cross, norm, tangents, mv, tmv


@dataclass(frozen=True)
class ContactPoint:
    local_a: tuple
    local_b: tuple
    point: tuple
    gap: float
    matched: bool = False

    @property
    def depth(self):
        return max(0., -self.gap)


@dataclass(frozen=True)
class Manifold:
    a: int
    b: int
    normal: tuple
    points: tuple
    method: str = ''


def _surface_distance(p, shape):
    if isinstance(shape, Sphere):
        return abs(norm(p)-shape.radius)
    if isinstance(shape, Prism):
        q = tuple(abs(x)-h/2 for x, h in zip(p, (shape.a, shape.b, shape.c)))
        return abs(norm(tuple(max(0., x) for x in q))+min(max(q), 0.))
    q = (math.hypot(p[0], p[1])-shape.radius, abs(p[2])-shape.length/2)
    return abs(math.hypot(max(0., q[0]), max(0., q[1]))+min(max(q), 0.))


def _point(a, b, pa, pb, n, matched=False):
    return ContactPoint(a.local(pa), b.local(pb), mul(add(pa, pb), .5), dot(n, sub(pb, pa)), matched)


def _face(proxy, direction, angle):
    if not isinstance(proxy.shape, Prism):
        return None
    local = tmv(proxy.r, direction)
    axis = max(range(3), key=lambda i: abs(local[i]))
    if abs(local[axis]) < math.cos(angle):
        return None
    sign = 1 if local[axis] >= 0 else -1
    half = (proxy.shape.a/2, proxy.shape.b/2, proxy.shape.c/2)
    others = [j for j in range(3) if j != axis]
    polygon = []
    for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        p = [0., 0., 0.]
        p[axis], p[others[0]], p[others[1]] = sign*half[axis], u*half[others[0]], v*half[others[1]]
        polygon.append(proxy.world(tuple(p)))
    return axis, sign, half, polygon


def _features(proxy, direction, angle):
    s = proxy.shape
    local = tmv(proxy.r, direction)
    if isinstance(s, Prism):
        best = dot(local, proxy.local(proxy.support(direction)))
        tolerance = math.sin(angle)*proxy.radius*2
        return [proxy.world(v) for v in s.vertices() if best-dot(local, v) <= tolerance]
    if isinstance(s, Cylinder):
        rho = math.hypot(local[0], local[1])
        if rho <= math.sin(angle):
            z = math.copysign(s.length/2, local[2])
            return [proxy.world(p) for p in ((0, 0, z), (s.radius, 0, z), (-s.radius, 0, z),
                                              (0, s.radius, z), (0, -s.radius, z))]
        if abs(local[2]) <= math.sin(angle):
            return [proxy.world((s.radius*local[0]/rho, s.radius*local[1]/rho, z))
                    for z in (-s.length/2, s.length/2)]
    return [proxy.support(direction)]


def _clip(poly, direction, offset, eps):
    if not poly:
        return []
    result = []
    a = poly[-1]
    da = dot(direction, a)-offset
    for b in poly:
        db = dot(direction, b)-offset
        if (da <= eps) != (db <= eps):
            result.append(add(a, mul(sub(b, a), da/(da-db))))
        if db <= eps:
            result.append(b)
        a, da = b, db
    return result


def _face_seeds(a, b, n, opts, eps):
    """Clip incident box face, or project exact support features to box face."""
    points = []
    for ref, inc, rn, swapped in ((a, b, n, False), (b, a, mul(n, -1), True)):
        face = _face(ref, rn, opts.face_angle)
        if face is None:
            continue
        axis, sign, half, _ = face
        local_n = tuple(sign if i == axis else 0. for i in range(3))
        fn = mv(ref.r, local_n)
        plane_point = ref.world(mul(local_n, half[axis]))
        incident = _face(inc, mul(fn, -1), math.pi/2)
        poly = incident[3] if incident else _features(inc, mul(fn, -1), opts.face_angle)
        if incident:
            for j in range(3):
                if j == axis:
                    continue
                direction = tuple(ref.r[k][j] for k in range(3))
                for sign_side in (-1, 1):
                    side = mul(direction, sign_side)
                    poly = _clip(poly, side, dot(side, ref.x)+half[j], eps)
        for pb in poly:
            local = ref.local(pb)
            if any(abs(local[j]) > half[j]+eps for j in range(3) if j != axis):
                continue
            pa = sub(pb, mul(fn, dot(fn, sub(pb, plane_point))))
            points.append(_point(a, b, pb, pa, n) if swapped else _point(a, b, pa, pb, n))
    return points


def _cap_seeds(a, b, n, opts, eps):
    if not (isinstance(a.shape, Cylinder) and isinstance(b.shape, Cylinder)):
        return []
    points = []
    for ref, inc, rn, swapped in ((a, b, n, False), (b, a, mul(n, -1), True)):
        local = tmv(ref.r, rn)
        if abs(local[2]) < math.cos(opts.face_angle):
            continue
        fn = mul(tuple(ref.r[k][2] for k in range(3)), math.copysign(1., local[2]))
        plane = ref.world((0., 0., math.copysign(ref.shape.length/2, local[2])))
        inc_direction = tmv(inc.r, mul(fn, -1))
        if abs(inc_direction[2]) >= math.cos(opts.incident_cap_angle):
            z = math.copysign(inc.shape.length/2, inc_direction[2])
            radius = inc.shape.radius
            features = [inc.world(p) for p in ((0, 0, z), (radius, 0, z), (-radius, 0, z), (0, radius, z), (0, -radius, z))]
        else:
            features = _features(inc, mul(fn, -1), opts.face_angle)
        for pb in features:
            pa = sub(pb, mul(fn, dot(fn, sub(pb, plane))))
            if _surface_distance(ref.local(pa), ref.shape) <= eps:
                points.append(_point(a, b, pb, pa, n) if swapped else _point(a, b, pa, pb, n))
    return points


def _hull_area(points, n):
    t1, t2 = tangents(n)
    coords = sorted(set((dot(p.point, t1), dot(p.point, t2)) for p in points))
    def turn(a, b, c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    halves = []
    for seq in (coords, list(reversed(coords))):
        chain = []
        for p in seq:
            while len(chain) >= 2 and turn(chain[-2], chain[-1], p) <= 0:
                chain.pop()
            chain.append(p)
        halves.extend(chain[:-1])
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a, b in zip(halves, halves[1:]+halves[:1])))/2 if halves else 0.


def _reduce(points, n, merge):
    points = sorted(points, key=lambda p: (p.gap, p.local_a, p.local_b))
    unique = []
    for p in points:
        if not any(norm(sub(p.point, q.point)) <= merge for q in unique):
            unique.append(p)
    if len(unique) <= 4:
        return tuple(sorted(unique, key=lambda p: (p.local_a, p.local_b)))
    chosen = [unique.pop(0)]
    for count in (1, 2, 3):
        def score(p):
            if count == 1:
                delta = sub(p.point, chosen[0].point)
                return dot(delta, delta)-dot(delta, n)**2
            if count == 2:
                return abs(dot(n, cross(sub(chosen[1].point, chosen[0].point), sub(p.point, chosen[0].point))))
            return _hull_area(chosen+[p], n)
        p = max(unique, key=score)
        chosen.append(p)
        unique.remove(p)
    return tuple(sorted(chosen, key=lambda p: (p.local_a, p.local_b)))


def narrow_phase(body_a, body_b, cached_manifold=None, options=None, *, enrich=True):
    opts = Options() if options is None else options
    if not isinstance(opts, Options):
        raise ValueError('expected Options')
    if body_a.id == body_b.id:
        raise ValueError('collision requires distinct body ids')
    if body_a.id > body_b.id:
        m = narrow_phase(body_b, body_a, None, opts, enrich=enrich)
        if m is None:
            return None
        return Manifold(body_a.id, body_b.id, mul(m.normal, -1),
                        tuple(ContactPoint(p.local_b, p.local_a, p.point, p.gap, p.matched) for p in m.points), m.method)
    a, b = Proxy(body_a), Proxy(body_b)
    ell = max(1., 2*a.radius, 2*b.radius)
    eps, breaking = opts.geometry_relative*ell, opts.break_relative*ell
    witness = distance_or_penetration(a, b, opts)
    if witness.gap > opts.contact_factor*eps:
        return None
    n = witness.normal
    points = [_point(a, b, witness.a, witness.b, n)]
    old = cached_manifold
    if (old is not None and witness.method != 'finite-face' and (old.a, old.b) == (body_a.id, body_b.id)
            and dot(old.normal, n) >= math.cos(opts.cache_angle)):
        for p in old.points:
            pa, pb = a.world(p.local_a), b.world(p.local_b)
            delta = sub(pb, pa)
            gap = dot(n, delta)
            tangent = sub(delta, mul(n, gap))
            if gap <= breaking and norm(tangent) <= breaking and max(_surface_distance(p.local_a, a.shape),
                                                                                    _surface_distance(p.local_b, b.shape)) <= breaking:
                points.append(_point(a, b, pa, pb, n, p.gap <= eps))
        points[0] = replace(points[0], matched=any(norm(sub(points[0].point, p.point)) <= breaking and p.matched for p in points[1:]))
    if enrich and not (isinstance(a.shape, Sphere) or isinstance(b.shape, Sphere)):
        points.extend(p for p in _face_seeds(a, b, n, opts, eps*opts.contact_factor)
                      if witness.gap-breaking <= p.gap <= eps*opts.contact_factor)
        points.extend(p for p in _cap_seeds(a, b, n, opts, eps*opts.contact_factor)
                      if witness.gap-breaking <= p.gap <= eps*opts.contact_factor)
        points = list(_reduce(points, n, breaking/2))
        if len(points) < 4 and witness.method != 'finite-face':
            target = a if a.radius <= b.radius else b
            theta = min(opts.perturb_angle, breaking/target.radius)
            for tangent in tangents(n):
                for sign in (-1, 1):
                    state = replace(target.body.state, orientation=compose(from_axis_angle(tangent, sign*theta), target.body.state.orientation))
                    perturbed = Proxy(replace(target.body, state=state))
                    w = distance_or_penetration(perturbed if target is a else a,
                                                perturbed if target is b else b, opts)
                    pa = a.world(perturbed.local(w.a)) if target is a else w.a
                    pb = b.world(perturbed.local(w.b)) if target is b else w.b
                    delta = sub(pb, pa)
                    gap = dot(n, delta)
                    if (abs(gap-witness.gap) <= breaking and norm(sub(delta, mul(n, gap))) <= breaking
                            and max(_surface_distance(a.local(pa), a.shape), _surface_distance(b.local(pb), b.shape)) <= breaking):
                        points.append(_point(a, b, pa, pb, n))
    # Sphere contacts are geometrically single points; cache only supplies restitution matching.
    if isinstance(a.shape, Sphere) or isinstance(b.shape, Sphere):
        points = points[:1]
    return Manifold(body_a.id, body_b.id, n, _reduce(points, n, breaking/2), witness.method)
