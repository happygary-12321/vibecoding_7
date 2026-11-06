"""Independent Part 1 oracles; tolerances selected before execution (LOG.md)."""

from dataclasses import FrozenInstanceError
import math
import unittest

from Hw5 import Parameters, State, step


class DynamicsTests(unittest.TestCase):
    def close(self, actual, expected):
        self.assertTrue(math.isclose(actual, expected, abs_tol=1e-11, rel_tol=1e-13),
                        f"{actual!r} != {expected!r}")

    def vector_close(self, actual, expected):
        self.assertEqual(len(actual), 3)
        for a, b in zip(actual, expected):
            self.close(a, b)

    def test_hand_step(self):
        initial = State((1, -2, 3), (2, -3, 4))
        result = step(initial, Parameters(2, 0.25, (0, -10, 0)), (4, 6, -8))
        self.vector_close(result.velocity, (2.5, -4.75, 3))
        self.vector_close(result.position, (1.625, -3.1875, 3.75))
        self.assertEqual((result.time, result.step_count), (0.25, 1))
        self.assertEqual(initial, State((1, -2, 3), (2, -3, 4)))

    def test_constant_force_trajectory_and_bias(self):
        for mass, acceleration in ((2, (2, -7, -4)), (4, (1, -8.5, -2))):
            with self.subTest(mass=mass):
                s = State((1, -2, 3), (2, -3, 4))
                p = Parameters(mass, 0.01, (0, -10, 0))
                for n in range(1, 101):
                    s = step(s, p, (4, 6, -8))
                    t = n * 0.01
                    for i, (x0, v0, a) in enumerate(zip((1, -2, 3), (2, -3, 4), acceleration)):
                        self.close(s.velocity[i], v0 + a*t)
                        exact = x0 + v0*t + a*t*t/2
                        self.close(s.position[i] - exact, a*0.01*t/2)
                    self.close(s.time, t)
                    self.assertEqual(s.step_count, n)

    def test_gravity_is_mass_independent(self):
        for mass in (0.25, 7):
            s = step(State(), Parameters(mass, 0.1))
            self.vector_close(s.velocity, (0, -0.981, 0))
            self.vector_close(s.position, (0, -0.0981, 0))

    def test_arbitrary_gravity_hand_step_mass_independence(self):
        # Hand calculation: dv=(.25,-.5,.75); updated v times h gives
        # dx=(.5625,-.875,1.1875). Every operation is binary-exact here,
        # so use exact equality, with no roundoff or integration allowance.
        results = []
        for mass in (0.5, 8.0):
            with self.subTest(mass=mass):
                initial = State((1, -2, 3), (2, -3, 4), time=2, step_count=8)
                parameters = Parameters(mass, 0.25, (1, -2, 3))
                force = [0, 0, 0]
                result = step(initial, parameters, force)
                self.assertEqual(result.velocity, (2.25, -3.5, 4.75))
                self.assertEqual(result.position, (1.5625, -2.875, 4.1875))
                self.assertEqual((result.time, result.step_count), (2.25, 9))
                self.assertIsNot(result, initial)
                self.assertEqual(initial.position, (1, -2, 3))
                self.assertEqual(initial.velocity, (2, -3, 4))
                self.assertEqual((initial.time, initial.step_count), (2, 8))
                self.assertEqual((parameters.mass, parameters.dt, parameters.gravity),
                                 (mass, 0.25, (1, -2, 3)))
                self.assertEqual(force, [0, 0, 0])
                results.append(result)
        self.assertEqual(results[0], results[1])

    def test_uniform_motion_and_momentum(self):
        s = State((1, 2, 3), (1.25, -2.5, 0.75))
        p = Parameters(4, 0.01, (0, 0, 0))
        for n in range(1, 101):
            s = step(s, p)
            self.vector_close(s.position, (1+1.25*n*.01, 2-2.5*n*.01, 3+.75*n*.01))
            self.vector_close(tuple(4*v for v in s.velocity), (5, -10, 3))

    def test_galilean_boost(self):
        # Paired simulations, without an analytical trajectory reference.
        boost = (1.7, -0.8, 2.3)
        for mass in (0.5, 3):
            for h in (0.02, 0.01):
                a = State((0.3, -0.7, 1.2), (-0.4, 1.1, 0.6))
                b = State(a.position, tuple(v+u for v, u in zip(a.velocity, boost)))
                p = Parameters(mass, h, (0, -2, 0))
                for n in range(1, round(1/h)+1):
                    a = step(a, p, (0.6, -0.3, 0.9))
                    b = step(b, p, (0.6, -0.3, 0.9))
                    self.vector_close(tuple(vb-va for va, vb in zip(a.velocity, b.velocity)), boost)
                    self.vector_close(tuple(xb-xa for xa, xb in zip(a.position, b.position)),
                                      tuple(u*n*h for u in boost))

    def test_first_order_position_convergence(self):
        errors = []
        for count in (20, 40, 80, 160):
            s = State((1, 2, 3), (2, -1, 0.5))
            for _ in range(count):
                s = step(s, Parameters(2, 1/count, (0, -10, 0)), (4, 6, -8))
            # Continuous endpoint at T=1, a=(2,-7,-4).
            error = math.dist(s.position, (4, -2.5, 1.5))
            self.assertGreater(error, 0)
            errors.append(error)
            self.vector_close(s.velocity, (4, -8, -3.5))
            self.close(s.time, 1)
        for coarse, fine in zip(errors, errors[1:]):
            self.assertLess(fine, coarse)
            self.assertAlmostEqual(math.log2(coarse/fine), 1, delta=1e-9)

    def test_force_lifetime_and_independent_bodies(self):
        p = Parameters(2, 0.5, (0, 0, 0))
        initial = State()
        a = step(initial, p, (4, -8, 12))
        a = step(a, p)
        self.vector_close(a.velocity, (1, -2, 3))
        self.vector_close(a.position, (1, -2, 3))
        self.assertEqual(step(initial, p).position, (0, 0, 0))

    def test_invalid_construction(self):
        bad_scalars = (True, "1", None, float("nan"), float("inf"), -float("inf"), 10**400)
        for value in bad_scalars + (0, -1):
            for field in ("mass", "dt"):
                with self.subTest(field=field, value=str(value)[:30]), self.assertRaises(ValueError):
                    Parameters(**{field: value})
        bad_vectors = (None, "123", (), (1, 2), (1, 2, 3, 4)) + tuple((0, v, 0) for v in bad_scalars)
        for vector in bad_vectors:
            for constructor, field in ((State, "position"), (State, "velocity"), (Parameters, "gravity")):
                with self.subTest(field=field), self.assertRaises(ValueError):
                    constructor(**{field: vector})
        for count in (-1, 1.5, True, "0"):
            with self.assertRaises(ValueError):
                State(step_count=count)
        for time in bad_scalars + (-1,):
            with self.assertRaises(ValueError):
                State(time=time)

    def test_rejection_preserves_inputs(self):
        s = State((1, 2, 3), (4, 5, 6))
        p = Parameters()
        for force in ((1, 2), (1, float("nan"), 3), (True, 0, 0), "123"):
            with self.assertRaises(ValueError):
                step(s, p, force)
            self.assertEqual(s, State((1, 2, 3), (4, 5, 6)))
            self.assertEqual(p, Parameters())
        for a, b in ((None, p), (s, None)):
            with self.assertRaises(ValueError):
                step(a, b)
        for initial, params, force in (
            (s, Parameters(1e-308), (1e308, 0, 0)),
            (State(velocity=(1e308, 0, 0)), Parameters(dt=2), (0, 0, 0)),
            (State(time=1e308), Parameters(dt=1), (0, 0, 0)),
        ):
            before = (initial.position, initial.velocity, initial.time, initial.step_count)
            with self.assertRaises(ValueError):
                step(initial, params, force)
            self.assertEqual(before, (initial.position, initial.velocity, initial.time, initial.step_count))

    def test_immutable_vectors_and_clock(self):
        source = [1, 2, 3]
        s = State(position=source, time=2, step_count=7)
        source[0] = 99
        self.assertEqual(s.position, (1, 2, 3))
        with self.assertRaises(FrozenInstanceError):
            s.time = 4
        s = step(s, Parameters(dt=0.25))
        s = step(s, Parameters(dt=0.5))
        self.assertEqual((s.time, s.step_count), (2.75, 9))


if __name__ == "__main__":
    unittest.main(verbosity=2)
