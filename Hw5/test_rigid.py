"""Independent physical/discrete/contact oracles; see LOG.md for budgets."""

import math
import unittest
from dataclasses import replace
from Hw5 import State, Parameters, step
from Hw5.geometry import Prism, Sphere, Cylinder, ground_support, world_mesh
from Hw5.rigid import RigidState, advance, angular_acceleration, resolve_ground, contact_velocity
from Hw5.spatial import rotate, unrotate, multiply, quaternion


def world_vector(q, v):
    # Independent rotation matrix, not the production cross-product formula.
    w, x, y, z = q
    matrix = ((1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)),
              (2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)),
              (2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)))
    return tuple(sum(row[j]*v[j] for j in range(3)) for row in matrix)


class RigidTests(unittest.TestCase):
    def close(self, a, b, tol=1e-11):
        self.assertAlmostEqual(a, b, delta=tol)

    def vec(self, a, b, tol=1e-11):
        self.assertEqual(len(a), len(b))
        for x, y in zip(a, b):
            self.close(x, y, tol)

    def test_hand_inertia_and_symmetry(self):
        for shape, diagonal in ((Prism(12, 2, 4, 6), (52, 40, 20)),
                                (Sphere(5, 2), (8, 8, 8)),
                                (Cylinder(6, 2, 6), (24, 24, 12))):
            self.vec(shape.inertia, diagonal)
            self.assertEqual(shape.center_of_mass, (0, 0, 0))
            for i in range(3):
                self.vec(shape.inertia_tensor[i], tuple(diagonal[i] if i == j else 0 for j in range(3)))
        cube = Prism(3, 2, 2, 2)
        self.vec(cube.inertia, (2, 2, 2))
        axis = (1/3, 2/3, 2/3)
        self.close(sum(cube.inertia[i]*axis[i]**2 for i in range(3)), 2)

    def test_quaternion_frames_and_mesh(self):
        q = (math.sqrt(.5), 0, 0, math.sqrt(.5))
        self.vec(rotate(q, (2, 3, 4)), (-3, 2, 4))
        self.vec(unrotate(q, (-3, 2, 4)), (2, 3, 4))
        self.vec(multiply(q, q), (0, 0, 0, 1))
        self.vec(quaternion((2, 0, 0, 0)), (1, 0, 0, 0))
        for shape in (Prism(2, 2, 4, 6), Sphere(2, 2), Cylinder(2, 2, 6)):
            local = world_mesh(shape, (0, 0, 0), (1, 0, 0, 0), 8)
            world = world_mesh(shape, (5, 6, 7), q, 8)
            for lf, wf in zip(local, world):
                for (x, y, z), v in zip(lf, wf):
                    self.vec(v, (5-y, 6+x, 7+z))

    def test_zero_spin_agrees_with_part1(self):
        for shape in (Prism(2, 2, 3, 4), Sphere(2, 1), Cylinder(2, 1, 3)):
            a, b = State((1, 2, 3), (2, -1, 4)), RigidState((1, 2, 3), (2, -1, 4))
            for _ in range(20):
                a = step(a, Parameters(2, .01, (1, -2, 3)), (2, 4, -6))
                b, contact = advance(b, shape, .01, gravity=(1, -2, 3), force=(2, 4, -6), ground=False)
                self.assertIsNone(contact)
                self.assertEqual((b.position, b.velocity, b.time, b.step_count),
                                 (a.position, a.velocity, a.time, a.step_count))
                self.assertEqual((b.orientation, b.omega), ((1, 0, 0, 0), (0, 0, 0)))

    def test_principal_axis_rotation_and_torque(self):
        shape = Prism(12, 2, 4, 6)  # Iz=20
        s = RigidState(omega=(0, 0, 2))
        for _ in range(100):
            s, _ = advance(s, shape, .01, gravity=(0, 0, 0), ground=False)
        self.vec(s.omega, (0, 0, 2))
        angle = 200*math.atan(.01)
        self.vec(s.orientation, (math.cos(angle/2), 0, 0, math.sin(angle/2)))
        self.close(angle, 2, 7e-5)  # constant-axis special-case angle error
        s, _ = advance(RigidState(omega=(0, 0, 2)), shape, .25,
                       torque=(0, 0, 40), gravity=(0, 0, 0), ground=False)
        self.vec(s.omega, (0, 0, 2.5))
        self.vec(s.orientation, (1/math.sqrt(1+.3125**2), 0, 0,
                                 .3125/math.sqrt(1+.3125**2)))

    def test_gyroscopic_hand_step(self):
        shape = Prism(12, 2, 4, 6)
        self.vec(angular_acceleration(shape, (1, 2, 3), (0, 0, 0)), (30/13, -2.4, 1.2))
        s, _ = advance(RigidState(omega=(1, 2, 3)), shape, .01, ground=False)
        self.vec(s.omega, (1+3/130, 1.976, 3.012))

    def test_torque_free_invariants_refine(self):
        # Literal inertia, independent world matrix and energy, maximum over run.
        errors = []
        q0 = (math.cos(.3), math.sin(.3), 0, 0)
        initial_L = world_vector(q0, (52*.3, 40*.4, 20*.5))
        initial_E = (52*.3**2+40*.4**2+20*.5**2)/2
        for n in (100, 200, 400):
            s = RigidState(orientation=q0, omega=(.3, .4, .5))
            max_l = max_e = 0
            for _ in range(n):
                s, _ = advance(s, Prism(12, 2, 4, 6), 1/n, ground=False)
                momentum = world_vector(s.orientation, tuple(i*w for i, w in zip((52, 40, 20), s.omega)))
                energy = sum(i*w*w for i, w in zip((52, 40, 20), s.omega))/2
                max_l = max(max_l, math.dist(momentum, initial_L)/math.sqrt(sum(x*x for x in initial_L)))
                max_e = max(max_e, abs(energy-initial_E)/initial_E)
            self.assertLess(max_l, .005)
            self.assertLess(max_e, .005)
            errors.append((max_l, max_e))
        for old, new in zip(errors, errors[1:]):
            for a, b in zip(old, new):
                self.assertGreater(a, 1e-8)
                self.assertGreater(b/a, .4)
                self.assertLess(b/a, .6)
        print("torque-free relative max (L,E), h=.01,.005,.0025:", errors)

    def test_translation_invariant_rotation(self):
        a = RigidState(omega=(.3, .7, -.2))
        b = replace(a, position=(10, -3, 5), velocity=(2, 3, 4))
        for _ in range(100):
            a, _ = advance(a, Cylinder(3, .7, 2), .01, ground=False)
            b, _ = advance(b, Cylinder(3, .7, 2), .01, ground=False)
            self.assertEqual((a.omega, a.orientation), (b.omega, b.orientation))

    def test_world_offcenter_load_and_lifetime(self):
        q = (math.sqrt(.5), 0, 0, math.sqrt(.5))
        s = RigidState(position=(3, 4, 5), orientation=q)
        # arm world=(0,0,2), F=(0,4,0): torque=(-8,0,0), body=(0,8,0).
        b, _ = advance(s, Prism(12, 2, 4, 6), .25, gravity=(0, 0, 0),
                       force=(0, 4, 0), force_point=(3, 4, 7), ground=False)
        self.vec(b.omega, (0, .05, 0))
        self.vec(b.velocity, (0, 1/12, 0))
        c, _ = advance(b, Prism(12, 2, 4, 6), .25, gravity=(0, 0, 0), ground=False)
        self.vec(c.omega, b.omega)
        self.vec(c.velocity, b.velocity)

    def test_oriented_clearance(self):
        qz = (math.sqrt(.5), 0, 0, math.sqrt(.5))
        qx = (math.sqrt(.5), math.sqrt(.5), 0, 0)
        prism, cylinder = Prism(2, 2, 4, 6), Cylinder(2, 1, 6)
        for shape, q, before, after in ((prism, qz, 8, 9), (cylinder, qx, 9, 7)):
            self.close(ground_support(shape, (0, 10, 0), (1, 0, 0, 0))[1], before)
            self.close(ground_support(shape, (0, 10, 0), q)[1], after)
        q45 = (math.cos(math.pi/8), math.sin(math.pi/8), 0, 0)
        self.close(ground_support(cylinder, (0, 10, 0), q45)[1], 10-4/math.sqrt(2))

    def test_sphere_centered_impact_and_endpoints(self):
        for e in (0, .5, 1):
            s = RigidState((0, .8, 0), (2, -3, 4))
            b, c = resolve_ground(s, Sphere(2, 1), e)
            self.vec(b.position, (0, 1, 0))
            self.vec(b.velocity, (2, 3*e, 4))
            self.assertEqual(b.omega, (0, 0, 0))
            self.close(c.impulse, 6*(1+e))
            self.close(c.penetration, .2)
            self.assertEqual((b.time, b.step_count), (0, 0))

    def test_offcenter_impulse_hand_calculation(self):
        # Prism m=3, a=2,b=4,c=2 => Iz=5. At 45 degrees r=(1,-3,0)/sqrt(2).
        # k=1/3 + (1/2)/5=13/30; vn=-2; e=.5 => j=90/13.
        q = (math.cos(math.pi/8), 0, 0, math.sin(math.pi/8))
        s = RigidState((0, 2, 0), (0, -2, 0), q)
        b, c = resolve_ground(s, Prism(3, 2, 4, 2), .5)
        self.vec(c.lever_arm, (1/math.sqrt(2), -3/math.sqrt(2), 0))
        self.close(c.impulse, 90/13)
        self.vec(b.velocity, (0, 4/13, 0))
        self.vec(b.omega, (0, 0, 18/(13*math.sqrt(2))))
        self.close(c.normal_speed_after, 1)
        self.close(b.position[1], 3/math.sqrt(2))
        # Independently check loss: -(1-e^2)*vn^2/(2*k).
        final_k = 3*b.velocity[1]**2/2 + 5*b.omega[2]**2/2
        self.close(final_k-6, -45/13)

    def test_contact_point_direction_and_manifold_limit(self):
        shape = Prism(3, 2, 4, 2)
        q = (math.cos(math.pi/8), 0, 0, math.sin(math.pi/8))
        separating = RigidState((0, 2, 0), (0, -1, 0), q, (0, 0, 2))
        b, c = resolve_ground(separating, shape)
        self.assertGreater(c.normal_speed_before, 0)
        self.assertEqual(c.impulse, 0)
        self.assertEqual(b.velocity, separating.velocity)
        inward = replace(separating, velocity=(0, 1, 0), omega=(0, 0, -2))
        _, c = resolve_ground(inward, shape)
        self.assertGreater(c.impulse, 0)
        # Tied flat face: selected centroid vn=0 while one corner approaches.
        flat = RigidState((0, 2, 0), omega=(0, 0, 1))
        b, c = resolve_ground(flat, shape)
        self.assertEqual(c.impulse, 0)
        self.assertLess(contact_velocity(flat, (-1, -2, 1))[1], 0)
        self.assertEqual(b.omega, flat.omega)
        above = replace(flat, position=(0, 3, 0))
        self.assertEqual(resolve_ground(above, shape), (above, None))

    def test_cylinder_ground_and_advance_clock(self):
        shape = Cylinder(2, .5, 2)
        q = (math.cos(.3), math.sin(.3), 0, 0)
        s = RigidState((0, .3, 0), (0, -2, 0), q, (.2, .1, .3), time=2, step_count=7)
        b, c = advance(s, shape, .01, restitution=.8)
        self.assertIsNotNone(c)
        self.assertGreater(c.impulse, 0)
        self.close(c.normal_speed_after, -.8*c.normal_speed_before)
        self.close(ground_support(shape, b.position, b.orientation)[1], 0)
        self.assertEqual((b.time, b.step_count), (2.01, 8))

    def test_validation_and_immutability(self):
        for bad in (0, -1, True, float('inf'), float('nan'), '2'):
            for factory in (lambda: Prism(2, bad, 3, 4), lambda: Sphere(bad, 2),
                            lambda: Cylinder(2, 1, bad)):
                with self.assertRaises(ValueError):
                    factory()
        for kwargs in ({'orientation': (0, 0, 0, 0)}, {'omega': (1, 2)},
                       {'velocity': (0, float('inf'), 0)}, {'time': -1}):
            with self.assertRaises(ValueError):
                RigidState(**kwargs)
        s, shape = RigidState((1, 3, 4)), Sphere(2, 1)
        before = repr((s, shape))
        for kwargs in ({'dt': 0}, {'dt': .1, 'force': (1, 2)},
                       {'dt': .1, 'torque': (0, 0, float('nan'))},
                       {'dt': .1, 'force_point': (1, 2)}, {'dt': .1, 'restitution': 2},
                       {'dt': .1, 'ground': 1}, {'dt': 1e308, 'force': (1e308, 0, 0)}):
            with self.assertRaises(ValueError):
                advance(s, shape, **kwargs)
            self.assertEqual(repr((s, shape)), before)
        with self.assertRaises(ValueError):
            world_mesh(shape, s.position, s.orientation, 3)
        with self.assertRaises(ValueError):
            ground_support(None, s.position, s.orientation)
        with self.assertRaises(ValueError):
            advance(None, shape, .1)
        source = [0, 0, 2]
        copied = RigidState(omega=source)
        source[2] = 99
        self.assertEqual(copied.omega, (0, 0, 2))


if __name__ == '__main__':
    unittest.main(verbosity=2)
