import json
import math
from pathlib import Path
import unittest
from dataclasses import replace
from Hw5.geometry import Prism, Sphere, Cylinder
from Hw5.rigid import RigidState
from Hw5.spatial import from_axis_angle
from hw7.model import Body, World, Options
from hw7.world import simulate, detect
from hw7.scene import make_scene
from hw7.falling_objects import summary, main


class RestingAndStackingTests(unittest.TestCase):
    def fixture(self, shape, *, count=1, height=1., orientation=(1, 0, 0, 0), dt=1/240, steps=2400):
        bodies = tuple(Body(i, shape, RigidState((0, height*(i+.5), 0), orientation=orientation)) for i in range(count))
        floor = Body(count, Prism(1, 10, .2, 10), RigidState((0, -.1, 0)), True)
        initial = World(bodies+(floor,))
        result = simulate(initial, Options(dt=dt, restitution=0), steps, frame_stride=max(1, round(1/dt)))
        max_depth = max(r.penetration_after for r in result.reports)
        print(f'\nrest fixture {type(shape).__name__} count={count}: max_depth={max_depth:.9g}, '
              f'final_depth={result.reports[-1].penetration_after:.9g}, '
              f'max_speed={max(math.hypot(*b.state.velocity) for b in result.world.bodies if not b.static):.9g}', flush=True)
        self.assertEqual(result.world.bodies[-1], floor)
        self.assertLessEqual(max_depth, .005 if count > 1 else .002)
        for b, before in zip(result.world.bodies, initial.bodies):
            if b.static:
                continue
            self.assertTrue(all(math.isfinite(x) for x in (*b.state.position, *b.state.velocity, *b.state.orientation, *b.state.omega)))
            self.assertAlmostEqual(sum(x*x for x in b.state.orientation), 1, delta=1e-12)
            self.assertLess(abs(b.state.position[1]-before.state.position[1]), .01 if count > 1 else .005)
            self.assertLess(math.hypot(*b.state.velocity), .02)
            self.assertLess(math.hypot(*b.state.omega), .05)
            self.assertLess(math.hypot(b.state.position[0], b.state.position[2]), .005)
        if steps*dt >= 10:
            start = result.frames[-3]
            for a, b in zip(start.bodies, result.world.bodies):
                self.assertLess(math.dist(a.state.position, b.state.position), .005)
        return result

    def test_prism_resting_ten_seconds(self):
        self.fixture(Prism(1, 1, 1, 1))

    def test_sphere_resting_ten_seconds(self):
        self.fixture(Sphere(1, .5))

    def test_upright_cylinder_resting_ten_seconds(self):
        self.fixture(Cylinder(1, .4, .6), height=.6, orientation=from_axis_angle((1, 0, 0), math.pi/2))

    def test_horizontal_cylinder_resting_ten_seconds(self):
        self.fixture(Cylinder(1, .4, .6), height=.8)

    def test_three_box_stack_ten_seconds(self):
        self.fixture(Prism(1, 1, 1, 1), count=3)

    def test_three_cylinder_stack_ten_seconds(self):
        self.fixture(Cylinder(1, .4, .6), count=3, height=.6, orientation=from_axis_angle((1, 0, 0), math.pi/2))

    def test_timestep_refinement_reduces_resting_penetration(self):
        a = self.fixture(Sphere(1, .5), steps=480)
        b = self.fixture(Sphere(1, .5), dt=1/480, steps=960)
        # Steady endpoint depth is slop+4*g*h^2 for beta=.2 (one contact).
        # After n steps: d[n]=slop+4*g*h^2 plus the decaying .8^n transient.
        self.assertAlmostEqual(a.reports[-1].penetration_after, .0001+4*9.81/240**2, delta=1e-10)
        self.assertAlmostEqual(b.reports[-1].penetration_after, .0001+4*9.81/480**2, delta=1e-10)


class ExampleTests(unittest.TestCase):
    def test_thirty_body_three_second_contact_smoke(self):
        initial = make_scene()
        result = simulate(initial, Options(dt=1/480), 1440)
        report = summary(result)
        print('\n30-body 3 s smoke:', json.dumps(report, sort_keys=True))
        self.assertEqual(report['finite_mass_bodies'], 30)
        self.assertEqual(report['body_counts'], {'Prism': 10, 'Sphere': 10, 'Cylinder': 10})
        self.assertEqual(report['static_colliders'], 5)
        self.assertTrue(report['finite_states'])
        self.assertGreater(report['body_body_impulse_rows'], 0)
        self.assertGreater(report['body_bin_impulse_rows'], 0)
        self.assertLessEqual(report['max_penetration_after_m'], .03)
        self.assertLessEqual(report['final_penetration_m'], .01)
        self.assertEqual(report['escaped_body_ids'], [])
        active = {i for r in result.reports for p in r.impulses if p.normal_impulse > 1e-8 for i in (p.a, p.b) if i < 30}
        self.assertEqual({type(initial.bodies[i].shape).__name__ for i in active}, {'Prism', 'Sphere', 'Cylinder'})
        for a, b in zip(initial.bodies, result.world.bodies):
            if a.static:
                self.assertEqual(a, b)
            else:
                self.assertEqual(b.state.step_count, 1440)
                self.assertAlmostEqual(b.state.time, 3, delta=1e-12)

    def test_headless_cli_and_json(self):
        # All generated files stay inside hw7, not an arbitrary temp directory.
        path = Path('hw7/evidence/test_cli.json')
        self.assertEqual(main(['--headless', '--steps', '2', '--seed', '11', '--json', str(path)]), 0)
        report = json.loads(path.read_text(encoding='utf-8'))
        self.assertEqual(report['summary']['steps'], 2)
        self.assertEqual(len(report['initial']['bodies']), 35)


if __name__ == '__main__':
    unittest.main(verbosity=2)
