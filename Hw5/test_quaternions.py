"""Independent quaternion oracles; budgets selected before execution (LOG.md)."""

import copy
import math
import unittest
from Hw5.spatial import (from_axis_angle, conjugate, inverse, compose, to_matrix,
                         from_matrix, angular_distance, rotate, unrotate, quaternion)
from Hw5.geometry import Prism, Sphere, Cylinder, ground_support, world_mesh
from Hw5.rigid import RigidState, advance


def rodrigues(axis, angle, vector):
    """Test-local Illinois TAM212 reference, no production helper calls."""
    norm = math.sqrt(sum(x*x for x in axis))
    x, y, z = (a/norm for a in axis)
    a, b, c = vector
    crossed = (y*c-z*b, z*a-x*c, x*b-y*a)
    projection = x*a+y*b+z*c
    return tuple(v*math.cos(angle)+w*math.sin(angle)+u*projection*(1-math.cos(angle))
                 for v, w, u in zip(vector, crossed, (x, y, z)))


def apply(matrix, vector):
    return tuple(sum(a*b for a, b in zip(row, vector)) for row in matrix)


def determinant(m):
    return (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1])
            -m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
            +m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))


class QuaternionTests(unittest.TestCase):
    def vec(self, a, b, tol=2e-12):
        self.assertEqual(len(a), len(b))
        for x, y in zip(a, b):
            self.assertAlmostEqual(x, y, delta=tol)

    def test_identity_and_coordinate_quarter_turns(self):
        self.vec(rotate((1, 0, 0, 0), (2, -3, 4)), (2, -3, 4))
        for axis, expected, matrix in (
            ((1, 0, 0), (2, -4, -3), ((1, 0, 0), (0, 0, -1), (0, 1, 0))),
            ((0, 1, 0), (4, -3, -2), ((0, 0, 1), (0, 1, 0), (-1, 0, 0))),
            ((0, 0, 1), (3, 2, 4), ((0, -1, 0), (1, 0, 0), (0, 0, 1))),
        ):
            q = from_axis_angle(axis, math.pi/2)
            self.vec(rotate(q, (2, -3, 4)), expected)
            for row, exact in zip(to_matrix(q), matrix):
                self.vec(row, exact)
            self.vec(rotate(from_matrix(matrix), (2, -3, 4)), expected)

    def test_rodrigues_arbitrary_axis_and_matrix(self):
        for axis, angle in (((2, -3, 6), .7), ((-1, 4, 2), -1.2), ((1, 1, 1), 2.4)):
            q = from_axis_angle(axis, angle)
            # Independent matrix columns are Rodrigues images of the basis.
            columns = [rodrigues(axis, angle, e) for e in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
            expected_matrix = tuple(tuple(columns[j][i] for j in range(3)) for i in range(3))
            matrix = to_matrix(q)
            for row, exact in zip(matrix, expected_matrix):
                self.vec(row, exact)
            for vector in ((2, -3, 5), (0, 0, 0), axis):
                expected = rodrigues(axis, angle, vector)
                self.vec(rotate(q, vector), expected)
                self.vec(apply(matrix, vector), expected)
                self.vec(rotate(from_matrix(expected_matrix), vector), expected)

    def test_noncommuting_composition_order(self):
        x = from_axis_angle((1, 0, 0), math.pi/2)
        z = from_axis_angle((0, 0, 1), math.pi/2)
        x_then_z, z_then_x = compose(z, x), compose(x, z)
        self.vec(rotate(x_then_z, (0, 1, 0)), (0, 0, 1))
        self.vec(rotate(z_then_x, (0, 1, 0)), (-1, 0, 0))
        self.assertGreater(angular_distance(x_then_z, z_then_x), 1)
        self.vec(apply(to_matrix(x_then_z), (2, 3, 4)),
                 apply(to_matrix(z), apply(to_matrix(x), (2, 3, 4))))

    def test_sign_equivalence_vectors_geometry_and_trajectories(self):
        q = from_axis_angle((2, -3, 6), .7)
        negative = tuple(-x for x in q)
        self.assertEqual(angular_distance(q, negative), 0)
        self.vec(rotate(q, (2, -3, 5)), rotate(negative, (2, -3, 5)))
        for shape in (Prism(3, 1, 2, 3), Sphere(2, .8), Cylinder(4, .7, 2)):
            mesh_a = world_mesh(shape, (1, 2, 3), q, 8)
            mesh_b = world_mesh(shape, (1, 2, 3), negative, 8)
            for fa, fb in zip(mesh_a, mesh_b):
                for va, vb in zip(fa, fb):
                    self.vec(va, vb)
            self.assertEqual(ground_support(shape, (1, 2, 3), q),
                             ground_support(shape, (1, 2, 3), negative))
            a = RigidState((0, .1, 0), (1, -1, .5), q, (.3, .7, .5))
            b = RigidState(a.position, a.velocity, negative, a.omega)
            for _ in range(60):
                a, ca = advance(a, shape, .01)
                b, cb = advance(b, shape, .01)
                self.vec(a.position, b.position)
                self.vec(a.velocity, b.velocity)
                self.vec(a.omega, b.omega)
                self.assertLess(angular_distance(a.orientation, b.orientation), 2e-12)
                self.assertEqual(ca, cb)

    def test_inverse_and_magnitude_preservation(self):
        q = from_axis_angle((2, -3, 6), 1.7)
        vector = (2, -3, 5)
        rotated = rotate(tuple(7*x for x in q), vector)
        self.vec(rotate(inverse(q), rotated), vector)
        self.vec(unrotate(q, rotated), vector)
        self.vec(conjugate(q), inverse(q))
        self.assertAlmostEqual(math.dist(rotated, (0, 0, 0)), math.sqrt(38), delta=2e-12)
        state = RigidState(orientation=tuple(7*x for x in q), omega=(2, -3, 5))
        self.assertEqual(state.omega, (2, -3, 5))
        self.assertLess(angular_distance(compose(q, inverse(q)), (1, 0, 0, 0)), 2e-12)

    def test_matrix_properties_and_orientation_round_trips(self):
        for axis in ((1, 0, 0), (0, 1, 0), (0, 0, 1), (2, -3, 6)):
            for angle in (0, 1e-12, .7, math.pi, math.pi-1e-10, math.pi+1e-10, -2.8):
                q = from_axis_angle(axis, angle)
                matrix = to_matrix(q)
                self.assertAlmostEqual(determinant(matrix), 1, delta=2e-12)
                for i in range(3):
                    for j in range(3):
                        self.assertAlmostEqual(sum(matrix[k][i]*matrix[k][j] for k in range(3)),
                                               int(i == j), delta=2e-12)
                recovered = from_matrix(matrix)
                self.assertLess(angular_distance(q, recovered), 2e-12)
                # Round-trip check is supplemented by independent rotated vectors.
                self.vec(rotate(recovered, (2, 3, -4)), rodrigues(axis, angle, (2, 3, -4)))

    def test_exact_half_turn_matrices_and_small_angles(self):
        fixtures = (((1, 0, 0), ((1, 0, 0), (0, -1, 0), (0, 0, -1))),
                    ((0, 1, 0), ((-1, 0, 0), (0, 1, 0), (0, 0, -1))),
                    ((0, 0, 1), ((-1, 0, 0), (0, -1, 0), (0, 0, 1))))
        for axis, matrix in fixtures:
            self.vec(rotate(from_matrix(matrix), (2, 3, 4)), rodrigues(axis, math.pi, (2, 3, 4)))
        # An exact pi quaternion with zero scalar and a non-axis-aligned direction.
        q = (0, 2/7, -3/7, 6/7)
        self.assertLess(angular_distance(q, from_matrix(to_matrix(q))), 2e-12)
        tiny = from_axis_angle((0, 0, 1), 1e-12)
        self.assertGreater(tiny[3], 0)
        self.assertAlmostEqual(angular_distance(tiny, (1, 0, 0, 0))/1e-12, 1, delta=1e-12)
        self.assertEqual(from_axis_angle((0, 0, 0), 0), (1, 0, 0, 0))
        self.vec(rotate(from_axis_angle((1e308, 0, 0), .7), (1, 2, 3)),
                 rodrigues((1, 0, 0), .7, (1, 2, 3)))

    def test_long_run_norm_with_changing_omega(self):
        s = RigidState(omega=(.3, .4, .5))
        maximum = 0
        for _ in range(10000):
            s, _ = advance(s, Prism(12, 2, 4, 6), .001, ground=False)
            maximum = max(maximum, abs(math.sqrt(sum(x*x for x in s.orientation))-1))
        self.assertLess(maximum, 1e-14)
        self.assertGreater(math.dist(s.omega, (.3, .4, .5)), .01)
        print('quaternion norm max residual over 10000 varying-omega steps:', maximum)

    def test_constant_z_spin_phase_error_and_refinement(self):
        errors = []
        for n in (100, 200, 400):
            h, omega, duration = 2/n, 1.3, 2
            s = RigidState(omega=(0, 0, omega))
            for _ in range(n):
                s, _ = advance(s, Sphere(3, 2), h, ground=False)
            discrete_angle = n*2*math.atan(h*omega/2)
            actual_angle = 2*math.atan2(s.orientation[3], s.orientation[0])
            self.assertAlmostEqual(actual_angle, discrete_angle, delta=3e-12)
            phase_error = omega*duration-actual_angle
            predicted_error = omega*duration-discrete_angle
            self.assertAlmostEqual(phase_error, predicted_error, delta=3e-12)
            self.assertGreater(phase_error, 0)
            self.assertLess(phase_error, omega**3*duration*h*h/12)
            errors.append(phase_error)
        for coarse, fine in zip(errors, errors[1:]):
            self.assertGreater(fine/coarse, .249)
            self.assertLess(fine/coarse, .251)
        print('constant-z phase error h=.02,.01,.005 rad:', errors)

    def test_sphere_arbitrary_axis_spin(self):
        omega = (2/7, -3/7, 6/7)  # magnitude 1 rad/s, physically fixed for sphere
        s = RigidState(omega=omega)
        for _ in range(500):
            s, _ = advance(s, Sphere(3, 2), .002, ground=False)
        self.vec(s.omega, omega)
        discrete_angle = 1000*math.atan(.001)
        vector = (2, -3, 5)
        self.vec(rotate(s.orientation, vector), rodrigues(omega, discrete_angle, vector), 5e-12)
        self.vec(rotate(s.orientation, vector), rodrigues(omega, 1, vector), 3e-6)

    def test_body_kinematics_right_multiplication(self):
        q0 = (math.sqrt(.5), math.sqrt(.5), 0, 0)  # active Rx(pi/2)
        s = RigidState(orientation=q0, omega=(0, 0, 2))
        for _ in range(100):
            s, _ = advance(s, Sphere(2, 1), .01, ground=False)
        angle = 200*math.atan(.01)
        # R(q0)*Rz(angle)*ex differs from Rz(angle)*R(q0)*ex.
        self.vec(rotate(s.orientation, (1, 0, 0)), (math.cos(angle), 0, math.sin(angle)))
        self.assertGreater(abs(rotate(s.orientation, (1, 0, 0))[2]), .5)

    def test_invalid_inputs_and_unchanged_sequences(self):
        axis, q = [2, -3, 6], [1, 2, 3, 4]
        matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        before = copy.deepcopy((axis, q, matrix))
        from_axis_angle(axis, .7)
        for function in (conjugate, inverse, to_matrix, quaternion):
            function(q)
        compose(q, q)
        angular_distance(q, q)
        from_matrix(matrix)
        self.assertEqual((axis, q, matrix), before)
        bad_matrices = (None, [], [[1, 0], [0, 1]],
                        [[1, 0, 0], [0, 1, 0], [0, 0, -1]],
                        [[1, .001, 0], [0, 1, 0], [0, 0, 1]],
                        [[1+1e-8, 0, 0], [0, 1, 0], [0, 0, 1]])
        for value in (float('nan'), float('inf'), True, '1', 10**400):
            bad_matrices += ([[value, 0, 0], [0, 1, 0], [0, 0, 1]],)
        for bad in bad_matrices:
            snapshot = repr(bad)
            with self.assertRaises(ValueError):
                from_matrix(bad)
            self.assertEqual(repr(bad), snapshot)
        for bad_axis, angle in (((0, 0, 0), .1), ((0, 0, 0), 2*math.pi),
                                ((1, 2), 0), ((float('nan'), 0, 0), 0),
                                ((1, 0, 0), True), ((1, 0, 0), float('inf'))):
            with self.assertRaises(ValueError):
                from_axis_angle(bad_axis, angle)
        for bad in (None, (0, 0, 0, 0), (1, 2), (True, 0, 0, 0), (1, float('inf'), 0, 0)):
            for function in (conjugate, inverse, to_matrix):
                with self.assertRaises(ValueError):
                    function(bad)
            for function in (compose, angular_distance):
                with self.assertRaises(ValueError):
                    function(q, bad)
                with self.assertRaises(ValueError):
                    function(bad, q)
        almost = [[1+1e-12, 0, 0], [0, 1, 0], [0, 0, 1]]
        self.assertLess(angular_distance(from_matrix(almost), (1, 0, 0, 0)), 2e-12)


if __name__ == '__main__':
    unittest.main(verbosity=2)
