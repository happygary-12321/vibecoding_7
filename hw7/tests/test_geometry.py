import itertools
import math
import random
import unittest
from dataclasses import replace
from Hw5.geometry import Prism, Sphere, Cylinder
from Hw5.rigid import RigidState
from Hw5.spatial import from_axis_angle, compose
from hw7.model import Body, Options
from hw7.collision import AABB, sweep_bounds, sweep_and_prune, world_aabb, CollisionError
from hw7.manifolds import narrow_phase
from hw7.scene import make_bin, make_scene


def body(shape, pos=(0, 0, 0), q=(1, 0, 0, 0), i=0, static=False):
    return Body(i, shape, RigidState(position=pos, orientation=q), static)


def brute(records):
    # Independent reference: no production overlap, bounds or SAP helper.
    result = []
    for (i, a, sa), (j, b, sb) in itertools.combinations(records, 2):
        overlap = True
        for axis in range(3):
            if a.maximum[axis] < b.minimum[axis] or b.maximum[axis] < a.minimum[axis]:
                overlap = False
        if overlap and not (sa and sb):
            result.append(tuple(sorted((i, j))))
    return tuple(sorted(result))


def rz(p, theta):
    # Test-local active Rodrigues special case; no production rotation helper.
    c, s = math.cos(theta), math.sin(theta)
    return (c*p[0]-s*p[1], s*p[0]+c*p[1], p[2])


class BroadPhaseTests(unittest.TestCase):
    def test_randomized_completeness_and_order(self):
        rng = random.Random(41)
        for count in (0, 1, 2, 30, 35, 100):
            for _ in range(10):
                records = []
                for i in range(count):
                    lo = tuple(rng.uniform(-5, 5) for _ in range(3))
                    hi = tuple(x+rng.uniform(0, 4) for x in lo)
                    records.append((i, AABB(lo, hi), i % 7 == 0))
                expected = brute(records)
                self.assertEqual(sweep_bounds(tuple(records)), expected)
                rng.shuffle(records)
                self.assertEqual(sweep_bounds(tuple(records)), expected)

    def test_touching_equal_nested_static_intervals(self):
        records = [(0, AABB((0, 0, 0), (1, 1, 1)), False),
                   (1, AABB((1, 1, 1), (2, 2, 2)), True),
                   (2, AABB((0, 0, 0), (2, 2, 2)), True),
                   (3, AABB((.5, .5, .5), (.5, .5, .5)), False)]
        self.assertEqual(sweep_bounds(tuple(records)), brute(records))
        self.assertIn((0, 1), sweep_bounds(tuple(records)))
        self.assertNotIn((1, 2), sweep_bounds(tuple(records)))

    def test_oriented_prism_and_sphere_bounds(self):
        theta = .713
        p = body(Prism(1, 2, 4, 6), (3, 4, 5), from_axis_angle((0, 0, 1), theta))
        box = world_aabb(p)
        corners = [rz(v, theta) for v in itertools.product((-1, 1), (-2, 2), (-3, 3))]
        for k in range(3):
            self.assertAlmostEqual(box.minimum[k], p.state.position[k]+min(v[k] for v in corners), delta=1e-12)
            self.assertAlmostEqual(box.maximum[k], p.state.position[k]+max(v[k] for v in corners), delta=1e-12)
        sphere = world_aabb(body(Sphere(1, .7), (1, 2, 3), p.state.orientation))
        for actual, expected in zip((*sphere.minimum, *sphere.maximum), (.3, 1.3, 2.3, 1.7, 2.7, 3.7)):
            self.assertAlmostEqual(actual, expected, delta=1e-12)

    def test_cylinder_45_degree_bounds_and_rim_enclosure(self):
        theta = math.pi/4
        p = body(Cylinder(1, 1, 4), q=from_axis_angle((1, 0, 0), theta))
        box = world_aabb(p)
        self.assertAlmostEqual(box.maximum[0], 1, delta=1e-12)
        self.assertAlmostEqual(box.maximum[1], 3/math.sqrt(2), delta=1e-12)
        self.assertAlmostEqual(box.maximum[2], 3/math.sqrt(2), delta=1e-12)
        for phi in range(360):
            x, y = math.cos(math.radians(phi)), math.sin(math.radians(phi))
            for z in (-2, 2):
                world = (x, (y-z)/math.sqrt(2), (y+z)/math.sqrt(2))
                self.assertTrue(all(box.minimum[k]-1e-12 <= world[k] <= box.maximum[k]+1e-12 for k in range(3)))

    def test_scene_initial_separation_and_static_candidates(self):
        scene = make_scene()
        self.assertEqual(len(scene.bodies), 35)
        self.assertEqual(scene, make_scene())
        self.assertEqual({type(b.shape).__name__: sum(type(c.shape) is type(b.shape) for c in scene.bodies if not c.static)
                          for b in scene.bodies if not b.static}, {'Prism': 10, 'Sphere': 10, 'Cylinder': 10})
        self.assertEqual(sweep_and_prune(scene.bodies), ())

    def test_invalid_bounds_and_duplicate_ids(self):
        with self.assertRaises(ValueError):
            AABB((1, 0, 0), (0, 1, 1))
        with self.assertRaises(ValueError):
            AABB((float('nan'), 0, 0), (1, 1, 1))
        a = body(Sphere(1, 1))
        with self.assertRaises(ValueError):
            sweep_and_prune((a, a))


class NarrowPhaseTests(unittest.TestCase):
    shapes = (Prism(1, 2, 2, 2), Sphere(1, 1), Cylinder(1, 1, 2))

    def check_pair(self, a, b, gap, tol=1e-6):
        m = narrow_phase(a, b)
        if gap > 1e-6:
            self.assertIsNone(m)
            return
        self.assertIsNotNone(m)
        self.assertAlmostEqual(sum(x*x for x in m.normal), 1, delta=1e-10)
        self.assertAlmostEqual(min(p.gap for p in m.points), gap, delta=tol)
        reverse = narrow_phase(b, a)
        for x, y in zip(m.normal, reverse.normal):
            self.assertAlmostEqual(x, -y, delta=1e-10)

    def _axis_pair(self, ia, ib):
        for d in (2.01, 2., 1.9):
            with self.subTest(distance=d):
                self.check_pair(body(self.shapes[ia]), body(self.shapes[ib], (d, 0, 0), i=1), d-2)
        theta = .47
        q = from_axis_angle((0, 0, 1), theta)
        for d in (2.01, 2., 1.9):
            with self.subTest(rotated_distance=d):
                self.check_pair(body(self.shapes[ia], q=q), body(self.shapes[ib], rz((d, 0, 0), theta), q, 1), d-2)

    def test_prism_prism_separated_touching_penetrating_rotated(self):
        self._axis_pair(0, 0)

    def test_prism_sphere_separated_touching_penetrating_rotated(self):
        self._axis_pair(0, 1)

    def test_prism_cylinder_separated_touching_penetrating_rotated(self):
        self._axis_pair(0, 2)

    def test_sphere_sphere_separated_touching_penetrating_rotated(self):
        self._axis_pair(1, 1)

    def test_sphere_cylinder_separated_touching_penetrating_rotated(self):
        self._axis_pair(1, 2)

    def test_cylinder_cylinder_separated_touching_penetrating_rotated(self):
        self._axis_pair(2, 2)

    def test_box_corner_sphere_rejects_aabb_false_positive(self):
        a = body(self.shapes[0])
        for offset in (.8, 1/math.sqrt(2), .6):
            self.check_pair(a, body(self.shapes[1], (1+offset, 1+offset, 0), i=1), math.sqrt(2)*offset-1)

    def test_cylinder_sphere_rim_and_containment(self):
        for factor in (1.1, 1., .9):
            self.check_pair(body(Cylinder(1, 1, 2)), body(Sphere(1, .5), (1+.3*factor, 0, 1+.4*factor), i=1), .5*factor-.5)
        m = narrow_phase(body(Sphere(1, .2)), body(Cylinder(1, 1, 4), i=1))
        self.assertAlmostEqual(m.points[0].depth, 1.2, delta=1e-12)

    def test_cylinder_cap_cap_and_perpendicular_interior(self):
        for d in (1.01, 1., .99):
            self.check_pair(body(Cylinder(1, .5, .8)), body(Cylinder(1, .7, 1.2), (0, 0, d), i=1), d-1)
        q = from_axis_angle((0, 1, 0), math.pi/2)
        m = narrow_phase(body(Cylinder(1, .5, 2)), body(Cylinder(1, .5, 2), (.1, .1, .1), q, 1))
        self.assertIsNotNone(m)  # origin is strictly inside both cylinders, independently.
        self.assertGreater(min(p.depth for p in m.points), .1)

    def test_coincident_spheres_and_prism_containment(self):
        m = narrow_phase(body(Sphere(1, 1)), body(Sphere(1, 1), i=1))
        self.assertEqual(m.normal, (1., 0., 0.))
        self.assertEqual(m.points[0].depth, 2.)
        self.check_pair(body(Prism(1, 4, 4, 4)), body(Prism(1, 1, 1, 1), i=1), -2.5)

    def test_every_bin_face_shape_and_rotation(self):
        # Literal interior plane offsets and inward directions, independent of support helpers.
        faces = ((0, 0., (0, 1, 0)), (1, -2., (1, 0, 0)), (2, 2., (-1, 0, 0)),
                 (3, -2., (0, 0, 1)), (4, 2., (0, 0, -1)))
        theta = .31
        for wall_index, plane, inward in faces:
            axis = next(i for i, x in enumerate(inward) if x)
            for shape in (Prism(1, .4, .6, .8), Sphere(1, .2), Cylinder(1, .2, .6)):
                for rotated in (False, True):
                    # Rotation only around z; derive projection directly from literal matrix.
                    q = from_axis_angle((0, 0, 1), theta) if rotated else (1, 0, 0, 0)
                    angle = theta if rotated else 0.
                    if isinstance(shape, Prism):
                        extents = (abs(math.cos(angle))*.2+abs(math.sin(angle))*.3,
                                   abs(math.sin(angle))*.2+abs(math.cos(angle))*.3, .4)
                    elif isinstance(shape, Sphere):
                        extents = (.2, .2, .2)
                    else:
                        extents = (.2, .2, .3)
                    for gap in (.01, 0., -.005):
                        pos = [0., 1., 0.]
                        pos[axis] = plane+inward[axis]*(extents[axis]+gap)
                        with self.subTest(wall=wall_index, shape=type(shape).__name__, rotated=rotated, gap=gap):
                            self.check_pair(body(shape, tuple(pos), q), make_bin()[wall_index], gap, 2e-6)

    def test_finite_wall_end_not_infinite_plane(self):
        self.assertIsNone(narrow_phase(body(Sphere(1, .1), (-1.95, 2.6, 0)), make_bin()[1]))

    def test_spread_face_cap_and_generatrix_manifolds(self):
        floor = body(Prism(1, 10, .2, 10), (0, -.1, 0), i=1, static=True)
        for shape, q, y, minimum in ((Prism(1, 1, 1, 1), (1, 0, 0, 0), .5, 4),
                                     (Cylinder(1, .4, .6), from_axis_angle((1, 0, 0), math.pi/2), .3, 3),
                                     (Cylinder(1, .4, .6), (1, 0, 0, 0), .4, 2)):
            m = narrow_phase(body(shape, (0, y, 0), q), floor)
            self.assertGreaterEqual(len(m.points), minimum)
            self.assertGreater(max(math.dist(a.point, b.point) for a, b in itertools.combinations(m.points, 2)), .3)

    def test_iteration_failure_is_explicit(self):
        a = body(Cylinder(1, .7, 2), q=from_axis_angle((1, 2, 3), .43))
        b = body(Prism(1, 1, 1, 1), (.4, .2, .1), i=1)
        with self.assertRaises(CollisionError):
            narrow_phase(a, b, options=Options(gjk_iterations=1))

    def test_rotated_boxes_against_independent_fifteen_axis_sat(self):
        rng = random.Random(83)
        def rotate_axis(p, axis, theta):
            length = math.sqrt(sum(x*x for x in axis))
            u = [x/length for x in axis]
            cp = (u[1]*p[2]-u[2]*p[1], u[2]*p[0]-u[0]*p[2], u[0]*p[1]-u[1]*p[0])
            projection = sum(u[i]*p[i] for i in range(3))
            return tuple(p[i]*math.cos(theta)+cp[i]*math.sin(theta)+u[i]*projection*(1-math.cos(theta)) for i in range(3))
        def crossed(a, b):
            return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
        for index in range(60):
            axis_a, axis_b = (1, 2, 3), (3, -1, 2)
            angle_a, angle_b = rng.uniform(-2, 2), rng.uniform(-2, 2)
            center = tuple(rng.uniform(-1.8, 1.8) for _ in range(3))
            basis = ((1, 0, 0), (0, 1, 0), (0, 0, 1))
            axes_a = [rotate_axis(v, axis_a, angle_a) for v in basis]
            axes_b = [rotate_axis(v, axis_b, angle_b) for v in basis]
            gaps = []
            for direction in axes_a+axes_b+[crossed(x, y) for x in axes_a for y in axes_b]:
                length = math.sqrt(sum(x*x for x in direction))
                if length < 1e-12:
                    continue
                n = [x/length for x in direction]
                extent = sum(abs(sum(n[k]*v[k] for k in range(3)))*h
                             for v, h in zip(axes_a+axes_b, (.4, .5, .6, .6, .3, .5)))
                gaps.append(abs(sum(n[k]*center[k] for k in range(3)))-extent)
            expected = max(gaps) <= 0
            a = body(Prism(1, .8, 1., 1.2), q=from_axis_angle(axis_a, angle_a))
            b = body(Prism(1, 1.2, .6, 1.), center, from_axis_angle(axis_b, angle_b), 1)
            self.assertEqual(narrow_phase(a, b) is not None, expected, f'fixture {index}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
