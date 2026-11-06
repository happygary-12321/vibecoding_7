"""Independent damping trajectories, discrete hand arithmetic and power balance."""

import contextlib
import io
import math
import unittest
from Hw5.geometry import Prism, Sphere, Cylinder
from Hw5.rigid import RigidState, advance


def kinetic_energy(state, mass, diagonal):
    """Test-only energy from literal independently checked inertia, no sim helper."""
    return mass*sum(v*v for v in state.velocity)/2 + sum(
        i*w*w for i, w in zip(diagonal, state.omega))/2


class DampingTests(unittest.TestCase):
    def vec(self, a, b, tolerance=1e-11):
        self.assertEqual(len(a), len(b))
        for x, y in zip(a, b):
            self.assertAlmostEqual(x, y, delta=tolerance)

    def test_default_and_zero_exact_undamped_regression(self):
        for shape in (Prism(3, 1, 2, 3), Sphere(3, .8), Cylinder(3, .7, 2)):
            a = RigidState((0, .1, 0), (1, -2, .5), omega=(.3, .7, .5))
            b = a
            contacts = 0
            for _ in range(60):
                loads = dict(force=(.2, .1, -.3), torque=(.1, -.2, .3), force_point=(1, 2, 3))
                a, ca = advance(a, shape, .01, **loads)
                b, cb = advance(b, shape, .01, linear_damping=0, angular_damping=0, **loads)
                self.assertEqual((a, ca), (b, cb))
                contacts += ca is not None
            self.assertGreater(contacts, 0)

    def test_linear_exponential_and_position_refinement(self):
        errors = []
        for n in (50, 100, 200):
            h = 1/n
            initial = RigidState((1, -2, 3), (2, -3, 4))
            s = initial
            for _ in range(n):
                s, _ = advance(s, Sphere(2.5, 2), h, gravity=(0, 0, 0),
                               ground=False, linear_damping=1.25)
            decay = math.exp(-.5)
            exact_v = tuple(v*decay for v in (2, -3, 4))
            exact_x = tuple(x+2*v*(1-decay) for x, v in zip((1, -2, 3), (2, -3, 4)))
            discrete = (1-.5*h)**n
            self.vec(s.velocity, tuple(v*discrete for v in initial.velocity))
            self.vec(s.position, tuple(x+2*v*(1-.5*h)*(1-discrete)
                                      for x, v in zip(initial.position, initial.velocity)))
            ev, ex = math.dist(s.velocity, exact_v), math.dist(s.position, exact_x)
            self.assertLess(ev, h)  # integration allowance, NOT roundoff tolerance
            self.assertLess(ex, 3*h)
            self.assertEqual(s.omega, (0, 0, 0))
            errors.append((ev, ex))
        self.refines(errors)
        print('linear damping endpoint (velocity,position) errors h=.02,.01,.005:', errors)

    def refines(self, errors):
        for old, new in zip(errors, errors[1:]):
            for coarse, fine in zip(old, new):
                self.assertGreater(coarse, 1e-8)
                self.assertGreater(fine/coarse, .48)
                self.assertLess(fine/coarse, .52)

    def test_sphere_angular_exponential_and_refinement(self):
        errors = []
        for n in (50, 100, 200):
            h = 1/n
            s = RigidState((1, -2, 3), (2, -3, 4), omega=(1, -2, 3))
            for _ in range(n):
                s, _ = advance(s, Sphere(5, 2), h, gravity=(0, 0, 0),
                               ground=False, angular_damping=4)  # literal I=8, rate=.5
            exact = tuple(w*math.exp(-.5) for w in (1, -2, 3))
            self.vec(s.omega, tuple(w*(1-.5*h)**n for w in (1, -2, 3)))
            error = math.dist(s.omega, exact)
            self.assertLess(error, h)
            self.vec(s.velocity, (2, -3, 4))
            self.vec(s.position, (3, -5, 7))
            errors.append((error,))
        self.refines(errors)
        print('sphere angular damping endpoint errors h=.02,.01,.005:', errors)

    def test_combined_hand_step_and_inputs_unchanged(self):
        initial = RigidState((1, 2, 3), (2, -4, 6), omega=(1, 2, -3), time=1, step_count=4)
        shape = Sphere(5, 2)  # I=(8,8,8)
        before = repr((initial, shape))
        s, contact = advance(initial, shape, .25, gravity=(0, 0, 0), ground=False,
                             linear_damping=2, angular_damping=4)
        self.vec(s.velocity, (1.8, -3.6, 5.4))
        self.vec(s.position, (1.45, 1.1, 4.35))
        self.vec(s.omega, (.875, 1.75, -2.625))
        qnorm = math.sqrt(1+.109375**2+.21875**2+.328125**2)
        self.vec(s.orientation, tuple(x/qnorm for x in (1, .109375, .21875, -.328125)))
        self.assertEqual((s.time, s.step_count), (1.25, 5))
        self.assertIsNone(contact)
        self.assertEqual(repr((initial, shape)), before)

    def test_linear_angular_and_combined_sphere_energy_decay(self):
        for c, cw in ((2, 0), (0, 4), (2, 4)):
            s = RigidState(velocity=(2, -4, 6), omega=(1, 2, -3))
            initial = s
            previous = kinetic_energy(s, 5, (8, 8, 8))
            for _ in range(100):
                s, _ = advance(s, Sphere(5, 2), .01, ground=False, gravity=(0, 0, 0),
                               linear_damping=c, angular_damping=cw)
                energy = kinetic_energy(s, 5, (8, 8, 8))
                self.assertLess(energy, previous)
                previous = energy
            if c == 0:
                self.assertEqual(s.velocity, initial.velocity)
            if cw == 0:
                self.assertEqual(s.omega, initial.omega)

    def test_nonspherical_gyro_and_body_damping_contribution(self):
        initial = RigidState(omega=(1, 2, 3), orientation=(math.sqrt(.5), 0, 0, math.sqrt(.5)))
        shape = Prism(12, 2, 4, 6)  # literal I=(52,40,20)
        undamped, _ = advance(initial, shape, .01, ground=False)
        damped, _ = advance(initial, shape, .01, ground=False, angular_damping=2)
        # Gyroscopic alpha=(30/13,-2.4,1.2), subtract (2/52,4/40,6/20).
        self.vec(damped.omega, (1+.01*(30/13-1/26), 2+.01*(-2.4-.1), 3+.01*(1.2-.3)))
        self.vec(tuple(d-u for d, u in zip(damped.omega, undamped.omega)),
                 (-.01/26, -.001, -.003))
        # A component can increase despite dissipative torque; no componentwise exponential claim.
        self.assertGreater(damped.omega[0], initial.omega[0])

    def test_power_balance_rate_converges_nonspherical(self):
        initial = RigidState(velocity=(2, -1, 3), omega=(1, 2, 3))
        shape = Prism(12, 2, 4, 6)
        initial_energy = kinetic_energy(initial, 12, (52, 40, 20))
        # Independent instantaneous damping power, gyro has identically zero power.
        power = -.8*14-.6*14  # -19.6 W
        alpha = (30/13-.6/52, -2.4-1.2/40, 1.2-1.8/20)
        acceleration = tuple(-.8*v/12 for v in (2, -1, 3))
        quadratic = (12*sum(a*a for a in acceleration)
                     + sum(i*a*a for i, a in zip((52, 40, 20), alpha)))/2
        errors = []
        for h in (.02, .01, .005, .0025):
            s, _ = advance(initial, shape, h, ground=False, gravity=(0, 0, 0),
                           linear_damping=.8, angular_damping=.6)
            rate = (kinetic_energy(s, 12, (52, 40, 20))-initial_energy)/h
            self.assertAlmostEqual(rate-power, h*quadratic, delta=2e-9)
            errors.append(abs(rate-power))
            self.assertLess(rate, 0)
        self.refines([(x,) for x in errors])
        print('power balance: target W=', power, 'quadratic=', quadratic,
              'rate errors h=.02,.01,.005,.0025:', errors)

    def test_gyro_numerical_drift_can_exceed_dissipation(self):
        # Damping bounds alone cannot guarantee energy decay for explicit gyro.
        s = RigidState(omega=(1, 2, 3))
        b, _ = advance(s, Prism(12, 2, 4, 6), .1, ground=False, gravity=(0, 0, 0),
                       angular_damping=.001)
        self.assertGreater(kinetic_energy(b, 12, (52, 40, 20)), kinetic_energy(s, 12, (52, 40, 20)))

    def test_external_loads_lifetime_and_no_com_drag_moment(self):
        initial = RigidState((1, 2, 3), (2, 0, 0))
        # External r=(1,0,0), F=(0,4,0) yields world torque (0,0,4).
        b, _ = advance(initial, Sphere(5, 2), .25, gravity=(0, 0, 0), ground=False,
                       force=(0, 4, 0), force_point=(2, 2, 3), linear_damping=2)
        self.vec(b.omega, (0, 0, .125))
        self.vec(b.velocity, (1.8, .2, 0))
        c, _ = advance(b, Sphere(5, 2), .25, gravity=(0, 0, 0), ground=False)
        self.vec(c.velocity, b.velocity)
        self.vec(c.omega, b.omega)

    def test_invalid_coefficients_and_step_boundaries(self):
        initial = RigidState(velocity=(2, -4, 6), omega=(1, 2, -3))
        shape = Sphere(5, 2)
        snapshot = repr((initial, shape))
        for name in ('linear_damping', 'angular_damping'):
            for bad in (-1, True, False, None, '1', complex(1), float('nan'), float('inf'), -float('inf'), 10**400):
                with self.subTest(name=name, bad=str(bad)[:25]), self.assertRaises(ValueError):
                    advance(initial, shape, .1, **{name: bad})
                self.assertEqual(repr((initial, shape)), snapshot)
        # h=.5: c=10 -> hc/m=1; c_omega=16 -> hc_omega/I=1. Equality accepted.
        b, _ = advance(initial, shape, .5, ground=False, gravity=(0, 0, 0),
                       linear_damping=10, angular_damping=16)
        self.assertEqual(b.velocity, (0, 0, 0))
        self.assertEqual(b.omega, (0, 0, 0))
        self.assertEqual(b.position, initial.position)
        for kwargs in ({'linear_damping': 10.000001}, {'angular_damping': 16.000001},
                       {'linear_damping': 1e308}):
            with self.assertRaises(ValueError):
                advance(initial, shape, .5, **kwargs)
            self.assertEqual(repr((initial, shape)), snapshot)
        # Nonisotropic angular restriction uses smallest moment (20), not an average.
        with self.assertRaises(ValueError):
            advance(initial, Prism(12, 2, 4, 6), .5, angular_damping=40.000001)

    def test_headless_example_smoke(self):
        from Hw5.damping_example import main
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(['--headless']), 0)
        self.assertIn('energy_J', output.getvalue())
        self.assertIn('damped', output.getvalue())


if __name__ == '__main__':
    unittest.main(verbosity=2)
