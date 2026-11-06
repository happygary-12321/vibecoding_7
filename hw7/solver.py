"""Projected sequential physical/friction rows and separate push/turn rows."""
from dataclasses import dataclass
import math
from Hw5.spatial import to_matrix
from .collision import radius_bound
from .math3 import ZERO, add, sub, mul, dot, cross, norm, mv, tmv, tangents


@dataclass(frozen=True)
class ImpulseReport:
    a: int
    b: int
    point: tuple
    normal: tuple
    normal_impulse: float
    tangent_impulse: tuple
    push_impulse: float
    normal_before: float
    normal_after: float


class Scratch:
    def __init__(self, body):
        self.body = body
        self.r = to_matrix(body.state.orientation)
        self.inv_mass = 0. if body.static else 1/body.shape.mass
        self.inv_i = (0.,)*3 if body.static else tuple(1/x for x in body.shape.inertia)
        self.v = body.state.velocity
        self.w = mv(self.r, body.state.omega)
        self.push_v = self.push_w = ZERO

    def inertia(self, torque):
        local = tmv(self.r, torque)
        return mv(self.r, tuple(x*i for x, i in zip(local, self.inv_i)))


class Row:
    def __init__(self, a, b, normal, point, opts):
        self.a, self.b, self.n, self.point = a, b, normal, point
        self.ra, self.rb = sub(point.point, a.body.state.position), sub(point.point, b.body.state.position)
        self.directions = (normal, *tangents(normal))
        self.angular_a = [a.inertia(cross(self.ra, d)) for d in self.directions]
        self.angular_b = [b.inertia(cross(self.rb, d)) for d in self.directions]
        self.linear_a = [mul(d, a.inv_mass) for d in self.directions]
        self.linear_b = [mul(d, b.inv_mass) for d in self.directions]
        self.kn = self.effective(0, 0)
        if self.kn <= 0 or not math.isfinite(self.kn):
            raise ValueError('nonpositive/nonfinite dynamic effective inverse mass')
        self.k11, self.k12, self.k22 = self.effective(1, 1), self.effective(1, 2), self.effective(2, 2)
        self.before = dot(normal, self.relative())
        self.target = -opts.restitution*self.before if not point.matched and self.before < -opts.restitution_threshold else 0.
        self.push_target = opts.beta*min(max(point.depth-opts.slop, 0.), opts.correction_depth_limit)/opts.dt
        self.normal_lambda = self.push_lambda = 0.
        self.tangent_lambda = (0., 0.)

    def effective(self, i, j):
        return ((self.a.inv_mass+self.b.inv_mass)*dot(self.directions[i], self.directions[j])
                +dot(cross(self.ra, self.directions[i]), self.angular_a[j])
                +dot(cross(self.rb, self.directions[i]), self.angular_b[j]))

    def relative(self, push=False):
        a, b = self.a, self.b
        va, wa = (a.push_v, a.push_w) if push else (a.v, a.w)
        vb, wb = (b.push_v, b.push_w) if push else (b.v, b.w)
        return sub(add(vb, cross(wb, self.rb)), add(va, cross(wa, self.ra)))

    def apply(self, amount, axis=0, push=False):
        if amount == 0:
            return
        a, b = self.a, self.b
        if push:
            a.push_v = sub(a.push_v, mul(self.linear_a[axis], amount))
            a.push_w = sub(a.push_w, mul(self.angular_a[axis], amount))
            b.push_v = add(b.push_v, mul(self.linear_b[axis], amount))
            b.push_w = add(b.push_w, mul(self.angular_b[axis], amount))
        else:
            a.v = sub(a.v, mul(self.linear_a[axis], amount))
            a.w = sub(a.w, mul(self.angular_a[axis], amount))
            b.v = add(b.v, mul(self.linear_b[axis], amount))
            b.w = add(b.w, mul(self.angular_b[axis], amount))


def solve_contacts(bodies, manifolds, opts, *, observer=None):
    """Fixed poses: returns scratch velocities and per-point impulse records."""
    if observer is not None:
        observer('solver_setup')
    scratch = {b.id: Scratch(b) for b in bodies}
    rows = [Row(scratch[m.a], scratch[m.b], m.normal, p, opts)
            for m in manifolds for p in m.points
            if p.gap <= opts.geometry_relative*max(1., 2*radius_bound(scratch[m.a].body.shape),
                                                  2*radius_bound(scratch[m.b].body.shape))]
    if observer is not None:
        observer('physical_impulses')
    for sweep in range(opts.velocity_iterations):
        for row in (rows if sweep % 2 == 0 else reversed(rows)):
            vn = dot(row.n, row.relative())
            value = max(0., row.normal_lambda+(row.target-vn)/row.kn)
            row.apply(value-row.normal_lambda)
            row.normal_lambda = value
            if opts.friction and value:
                u = row.relative()
                v1, v2 = dot(u, row.directions[1]), dot(u, row.directions[2])
                det = row.k11*row.k22-row.k12**2
                if det <= 0:
                    raise ValueError('singular tangential effective mass')
                x = row.tangent_lambda[0]-(row.k22*v1-row.k12*v2)/det
                y = row.tangent_lambda[1]-(row.k11*v2-row.k12*v1)/det
                length, limit = math.hypot(x, y), opts.friction*value
                if length > limit:
                    x, y = x*limit/length, y*limit/length
                row.apply(x-row.tangent_lambda[0], 1)
                row.apply(y-row.tangent_lambda[1], 2)
                row.tangent_lambda = (x, y)
            elif row.tangent_lambda != (0., 0.):
                row.apply(-row.tangent_lambda[0], 1)
                row.apply(-row.tangent_lambda[1], 2)
                row.tangent_lambda = (0., 0.)
    if observer is not None:
        observer('split_impulses')
    if opts.enable_split:
        for sweep in range(opts.split_iterations):
            for row in (rows if sweep % 2 == 0 else reversed(rows)):
                if row.push_target:
                    vn = dot(row.n, row.relative(push=True))
                    value = max(0., row.push_lambda+(row.push_target-vn)/row.kn)
                    row.apply(value-row.push_lambda, push=True)
                    row.push_lambda = value
    if observer is not None:
        observer('solver_reports')
    reports = tuple(ImpulseReport(r.a.body.id, r.b.body.id, r.point.point, r.n, r.normal_lambda,
                                  add(mul(r.directions[1], r.tangent_lambda[0]), mul(r.directions[2], r.tangent_lambda[1])),
                                  r.push_lambda, r.before, dot(r.n, r.relative())) for r in rows)
    if observer is not None:
        observer(None)
    return scratch, reports
