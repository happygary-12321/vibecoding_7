"""Development diagnostics, not a production backend or test oracle."""
import json
import sys
from dataclasses import replace
from pathlib import Path
from Hw5.geometry import Prism, Sphere, Cylinder
from Hw5.rigid import RigidState
from hw7.model import Body, World, Options
from hw7.world import detect, simulate
from hw7.manifolds import narrow_phase
from Hw5.spatial import from_axis_angle


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'stack':
        count = 3
        cylinder = len(sys.argv) > 2 and sys.argv[2] == 'cylinder'
        shape = Cylinder(1, .4, .6) if cylinder else Prism(1, 1, 1, 1)
        h = .6 if cylinder else 1.
        q = from_axis_angle((1, 0, 0), 3.141592653589793/2) if cylinder else (1, 0, 0, 0)
        bodies = tuple(Body(i, shape, RigidState((0, h*(i+.5), 0), orientation=q)) for i in range(count))
        floor = Body(count, Prism(1, 10, .2, 10), RigidState((0, -.1, 0)), True)
        iterations = int(sys.argv[3]) if len(sys.argv) > 3 else 30
        steps = int(sys.argv[4]) if len(sys.argv) > 4 else 2400
        result = simulate(World(bodies+(floor,)), Options(restitution=0, velocity_iterations=iterations), steps)
        print('stack', cylinder, iterations, 'steps', steps, 'max_depth', max(r.penetration_after for r in result.reports), flush=True)
        for b in result.world.bodies:
            print(b.id, b.state, flush=True)
        print('final impulses', result.reports[-1], flush=True)
        return
    if len(sys.argv) > 1:
        shape = Cylinder(1, .4, .6)
        a = Body(0, shape, RigidState((0, .4, 0)))
        floor = Body(1, Prism(1, 10, .2, 10), RigidState((0, -.1, 0)), True)
        result = simulate(World((a, floor)), Options(restitution=0), 240)
        print('horizontal cylinder after 1s', result.world.bodies[0].state, flush=True)
        print('last impulses', result.reports[-1], flush=True)
        print('manifold', narrow_phase(*result.world.bodies), flush=True)
        return
    data = json.loads(Path('hw7/evidence/first_720.json').read_text())
    bodies = []
    for entry in data['final']['bodies']:
        dims = entry['shape']
        kind = Prism if 'a' in dims else Cylinder if 'length' in dims else Sphere
        bodies.append(Body(entry['id'], kind(**dims), RigidState(**entry['state']), entry['static']))
    pairs, ms = detect(tuple(bodies), Options())
    for m in sorted(ms, key=lambda m: min(p.gap for p in m.points))[:6]:
        a, b = bodies[m.a], bodies[m.b]
        print('pair', m.a, m.b, type(a.shape).__name__, type(b.shape).__name__,
              'depth', max(p.depth for p in m.points), 'normal', m.normal, 'positions', a.state.position, b.state.position,
              'points', m.points, flush=True)


if __name__ == '__main__':
    main()
