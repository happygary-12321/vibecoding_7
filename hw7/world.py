"""Endpoint integration and serial multi-body contact pipeline."""
from dataclasses import dataclass, replace
import math
import time
from Hw5.rigid import RigidState, advance
from Hw5.spatial import rotate, unrotate, compose, from_axis_angle
from .model import Body, World, Options
from .math3 import add, sub, mul, dot, norm
from .collision import Proxy, radius_bound, world_aabb, sweep_bounds
from .manifolds import narrow_phase, ContactPoint, Manifold
from .solver import solve_contacts
from .parallel import ParallelDetector


@dataclass(frozen=True)
class StepReport:
    candidates: int
    manifolds: int
    impulses: tuple
    penetration_before: float
    penetration_after: float
    correction_caps: int
    new_corrected_pairs: int
    deepest_pair_before: tuple | None
    deepest_pair_after: tuple | None


def detect(bodies, opts, cache=(), enrich=True, *, detector=None):
    by_id = {b.id: b for b in bodies}
    old = {(m.a, m.b): m for m in cache}
    pairs = sweep_bounds(tuple((b.id, world_aabb(b, opts.contact_factor*opts.geometry_relative*
                                                 max(1., 2*radius_bound(b.shape))), b.static) for b in bodies))
    if detector is not None:
        return pairs, tuple(m for m in detector.query(by_id, pairs, old, opts, enrich) if m is not None)
    contacts = []
    for i, j in pairs:
        m = narrow_phase(by_id[i], by_id[j], old.get((i, j)), opts, enrich=enrich)
        if m:
            contacts.append(m)
    return pairs, tuple(contacts)


def step_world(world, options=None, *, backend='serial', detector=None):
    if not isinstance(world, World) or backend not in ('serial', 'parallel'):
        raise ValueError('expected World and serial/parallel backend')
    if (backend == 'parallel' and (not isinstance(detector, ParallelDetector) or not detector.active)
            or backend == 'serial' and detector is not None):
        raise ValueError('parallel steps require a live detector; serial steps require none')
    opts = Options() if options is None else options
    if not isinstance(opts, Options):
        raise ValueError('expected Options')
    predicted = []
    for body in world.bodies:
        if body.static:
            predicted.append(body)
            continue
        s = body.state
        free, _ = advance(s, body.shape, opts.dt, gravity=opts.gravity, ground=False)
        # Body kick is computed at old R. Preserve that world angular velocity
        # when presenting the state at the predicted endpoint orientation.
        w = rotate(s.orientation, free.omega)
        state = replace(free, omega=unrotate(free.orientation, w))
        predicted.append(replace(body, state=state))
    pairs, manifolds = detect(predicted, opts, world.cache, detector=detector)
    before = max((p.depth for m in manifolds for p in m.points), default=0.)
    scratch, impulses = solve_contacts(predicted, manifolds, opts)
    result, caps = [], 0
    for body in predicted:
        if body.static:
            result.append(body)
            continue
        data = scratch[body.id]
        h = opts.dt
        dx, angle = h*norm(data.push_v), h*norm(data.push_w)
        scale = min(1., opts.max_translation/dx if dx else 1., opts.max_rotation/angle if angle else 1.)
        caps += scale < 1.
        q = body.state.orientation
        if angle:
            q = compose(from_axis_angle(data.push_w, angle*scale), q)
        state = RigidState(add(body.state.position, mul(data.push_v, h*scale)), data.v,
                           q, unrotate(q, data.w), body.state.time, body.state.step_count)
        result.append(replace(body, state=state))
    _, corrected = detect(result, opts, enrich=False, detector=detector)
    after = max((p.depth for m in corrected for p in m.points), default=0.)
    # Preserve spread local anchors rather than replacing a resting patch with
    # the single diagnostic EPA witness at the corrected pose.
    proxies = {b.id: Proxy(b) for b in result}
    cache = []
    for m in manifolds:
        a, b = proxies[m.a], proxies[m.b]
        points = []
        for p in m.points:
            pa, pb = a.world(p.local_a), b.world(p.local_b)
            points.append(replace(p, point=mul(add(pa, pb), .5), gap=dot(m.normal, sub(pb, pa))))
        cache.append(replace(m, points=tuple(points)))
    new = len({(m.a, m.b) for m in corrected}-{(m.a, m.b) for m in manifolds})
    worst_before = max(manifolds, key=lambda m: max(p.depth for p in m.points), default=None)
    worst_after = max(corrected, key=lambda m: max(p.depth for p in m.points), default=None)
    return (World(tuple(result), tuple(cache), world.time+opts.dt, world.step_count+1),
            StepReport(len(pairs), len(manifolds), impulses, before, after, caps, new,
                       (worst_before.a, worst_before.b) if worst_before else None,
                       (worst_after.a, worst_after.b) if worst_after else None))


@dataclass(frozen=True)
class RunResult:
    world: World
    reports: tuple
    frames: tuple
    physics_seconds: float
    dt: float
    backend_statistics: dict | None = None


def simulate(world, options, steps, *, backend='serial', frame_stride=None,
             workers=4, batch_size=4, serial_threshold=0):
    if not isinstance(world, World) or not isinstance(options, Options) or backend not in ('serial', 'parallel'):
        raise ValueError('simulate requires World, Options and serial/parallel backend')
    # Validate settings even for zero-step calls, before any child starts.
    pool = ParallelDetector(workers, batch_size, serial_threshold) if backend == 'parallel' else None
    if type(steps) is not int or steps < 0:
        raise ValueError('steps must be a nonnegative integer')
    if frame_stride is not None and (type(frame_stride) is not int or frame_stride < 1):
        raise ValueError('frame_stride must be a positive integer')
    if pool is not None:
        with pool:
            result = _simulate(world, options, steps, backend, frame_stride, pool)
        return replace(result, backend_statistics=pool.statistics())
    return _simulate(world, options, steps, backend, frame_stride, None)


def _simulate(world, options, steps, backend, frame_stride, detector):
    frames = [world] if frame_stride else []
    reports = []
    started = time.perf_counter()
    for i in range(steps):
        world, report = step_world(world, options, backend=backend, detector=detector)
        reports.append(report)
        if frame_stride and ((i+1) % frame_stride == 0 or i+1 == steps):
            frames.append(world)
    return RunResult(world, tuple(reports), tuple(frames), time.perf_counter()-started, options.dt)


def kinetic_energy(world):
    return sum(.5*b.shape.mass*dot(b.state.velocity, b.state.velocity)
               +.5*sum(i*w*w for i, w in zip(b.shape.inertia, b.state.omega))
               for b in world.bodies if not b.static)
