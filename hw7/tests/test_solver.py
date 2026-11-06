import math
import unittest
from dataclasses import replace
from Hw5.geometry import Prism, Sphere, Cylinder
from Hw5.rigid import RigidState
from Hw5.spatial import from_axis_angle
from hw7.model import Body, Options, World
from hw7.manifolds import ContactPoint, Manifold, narrow_phase
from hw7.solver import solve_contacts
from hw7.world import step_world, simulate


def energy(states, bodies):
    # Literal independent diagonal inertias in each test; world spheres isotropic.
    return sum(.5*b.shape.mass*sum(x*x for x in states[b.id].v)
               +.5*sum(i*w*w for i, w in zip(b.shape.inertia, states[b.id].w)) for b in bodies)


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


class ImpulseTests(unittest.TestCase):
    def vec(self, actual, expected, tolerance=1e-10):
        for a, b in zip(actual, expected):
            self.assertAlmostEqual(a, b, delta=tolerance)

    def central(self, masses, velocities, restitution):
        bodies = tuple(Body(i, Sphere(m, 1), RigidState((2*i, 0, 0), (v, 0, 0)))
                       for i, (m, v) in enumerate(zip(masses, velocities)))
        manifold = narrow_phase(*bodies)
        scratch, report = solve_contacts(bodies, (manifold,), Options(gravity=(0, 0, 0), friction=0,
                                            restitution=restitution, restitution_threshold=0, enable_split=False))
        return bodies, scratch, report

    def test_equal_mass_elastic_swaps_and_conserves(self):
        bodies, states, report = self.central((1, 1), (1, -1), 1)
        self.vec(states[0].v, (-1, 0, 0))
        self.vec(states[1].v, (1, 0, 0))
        self.vec(states[0].w, (0, 0, 0))
        self.assertAlmostEqual(report[0].normal_impulse, 2, delta=1e-10)
        self.assertAlmostEqual(energy(states, bodies), 1, delta=1e-10)
        self.assertAlmostEqual(sum(b.shape.mass*states[b.id].v[0] for b in bodies), 0, delta=1e-10)

    def test_equal_mass_inelastic_stops(self):
        _, states, report = self.central((1, 1), (1, -1), 0)
        self.vec(states[0].v, (0, 0, 0))
        self.vec(states[1].v, (0, 0, 0))
        self.assertAlmostEqual(report[0].normal_impulse, 1, delta=1e-10)

    def test_unequal_mass_restitution_energy_loss(self):
        bodies, states, report = self.central((2, 3), (2, 0), .5)
        self.vec(states[0].v, (.2, 0, 0))
        self.vec(states[1].v, (1.2, 0, 0))
        self.assertAlmostEqual(report[0].normal_impulse, 3.6, delta=1e-10)
        self.assertAlmostEqual(energy(states, bodies), 2.2, delta=1e-10)
        self.assertAlmostEqual(sum(b.shape.mass*states[b.id].v[0] for b in bodies), 4, delta=1e-10)
        self.assertAlmostEqual(report[0].normal_after, 1, delta=1e-10)

    def test_offcenter_world_inertia_angular_and_total_momentum(self):
        # Sphere radius sqrt(5) => I=2*m, giving Iz=4,6. Both contact arms (0,1,0).
        # A synthetic common point intentionally isolates the solver from geometry.
        for rotated in (False, True):
            q = from_axis_angle((0, 1, 0), math.pi/2) if rotated else (1, 0, 0, 0)
            velocity = (0, 0, -1) if rotated else (1, 0, 0)
            normal = velocity
            bodies = (Body(0, Sphere(2, math.sqrt(5)), RigidState(velocity=velocity, orientation=q)),
                      Body(1, Sphere(3, math.sqrt(5)), RigidState(orientation=q)))
            point = ContactPoint((0, 1, 0), (0, 1, 0), (0, 1, 0), 0)
            m = Manifold(0, 1, normal, (point,))
            states, reports = solve_contacts(bodies, (m,), Options(restitution=0, friction=0, enable_split=False))
            self.assertAlmostEqual(reports[0].normal_impulse, .8, delta=1e-10)
            self.vec(states[0].v, tuple(.6*x for x in velocity))
            self.vec(states[1].v, tuple(4/15*x for x in velocity))
            expected_a = (.2, 0, 0) if rotated else (0, 0, .2)
            expected_b = (-2/15, 0, 0) if rotated else (0, 0, -2/15)
            self.vec(states[0].w, expected_a)
            self.vec(states[1].w, expected_b)
            self.vec(tuple(4*states[0].w[k]+6*states[1].w[k] for k in range(3)), (0, 0, 0))
            self.assertAlmostEqual(reports[0].normal_after, 0, delta=1e-10)

    def test_static_floor_restitution_and_friction(self):
        a = Body(0, Sphere(2, 1), RigidState((0, 1, 0), (0, -3, 0)))
        b = Body(1, Prism(1, 10, .2, 10), RigidState((0, -.1, 0)), True)
        states, report = solve_contacts((a, b), (narrow_phase(a, b),), Options(restitution=.5, friction=0, enable_split=False))
        self.vec(states[0].v, (0, 1.5, 0))
        self.assertAlmostEqual(report[0].normal_impulse, 9, delta=1e-10)
        self.vec(states[1].v, (0, 0, 0))
        # 1 kg sphere, vy=-1 ensures normal lambda=1. Tangent impulse saturates at .2.
        a = Body(0, Sphere(1, 1), RigidState((0, 1, 0), (1, -1, 0)))
        states, report = solve_contacts((a, b), (narrow_phase(a, b),), Options(restitution=0, friction=.2, enable_split=False))
        self.vec(states[0].v, (.8, 0, 0))
        self.vec(states[0].w, (0, 0, -.5))
        self.vec(report[0].tangent_impulse, (.2, 0, 0))  # impulse on B; A receives its negative
        self.assertLess(energy({0: states[0]}, (a,)), 1.)

    def test_separating_grazing_and_restitution_cutoff(self):
        _, states, report = self.central((1, 1), (-1, 1), 1)
        self.assertEqual(report[0].normal_impulse, 0)
        self.vec(states[0].v, (-1, 0, 0))
        a = Body(0, Sphere(1, 1), RigidState((0, 1, 0), (1, -.1, 0)))
        b = Body(1, Prism(1, 10, .2, 10), RigidState((0, -.1, 0)), True)
        m = narrow_phase(a, b)
        states, _ = solve_contacts((a, b), (m,), Options(restitution=1, friction=0))
        self.vec(states[0].v, (1, 0, 0))
        # A matched high-speed contact does not repeatedly trigger restitution.
        a = replace(a, state=replace(a.state, velocity=(0, -2, 0)))
        m = replace(m, points=tuple(replace(p, matched=True) for p in m.points))
        states, _ = solve_contacts((a, b), (m,), Options(restitution=1, friction=0))
        self.vec(states[0].v, (0, 0, 0))

    def test_rotating_face_approaching_corner_resolved(self):
        a = Body(0, Prism(1, 1, 1, 1), RigidState((0, .5, 0), omega=(0, 0, 1)))
        b = Body(1, Prism(1, 10, .2, 10), RigidState((0, -.1, 0)), True)
        states, report = solve_contacts((a, b), (narrow_phase(a, b),), Options(restitution=0, friction=0))
        self.assertGreater(sum(r.normal_impulse for r in report), .01)
        for x in (-.5, .5):
            vy = states[0].v[1]+states[0].w[2]*x
            self.assertGreaterEqual(vy, -1e-9)

    def test_anisotropic_world_inertia_and_energy_hand_calculation(self):
        # Prism m=12, sides 2,4,6 => Ibody=(52,40,20).
        # qz=90 degrees maps body x inertia 52 onto world y.
        q = from_axis_angle((0, 0, 1), math.pi/2)
        a = Body(0, Prism(12, 2, 4, 6), RigidState(velocity=(1, 0, 0), orientation=q))
        b = Body(1, Sphere(1, 1), RigidState(), True)
        p = ContactPoint((0, 0, 1), (0, 0, 1), (0, 0, 1), 0)
        m = Manifold(0, 1, (1, 0, 0), (p,))
        states, records = solve_contacts((a, b), (m,), Options(restitution=0, friction=0, enable_split=False))
        self.assertAlmostEqual(records[0].normal_impulse, 39/4, delta=1e-10)
        self.vec(states[0].v, (3/16, 0, 0))
        self.vec(states[0].w, (0, -3/16, 0))
        # Independent world inertia about y=52, not body's Iy=40.
        final_energy = (12*(3/16)**2+52*(3/16)**2)/2
        self.assertAlmostEqual(final_energy, 1.125, delta=1e-12)
        self.assertAlmostEqual(6-final_energy, 39/8, delta=1e-12)

    def test_coulomb_sticking_contact_velocity(self):
        a = Body(0, Sphere(1, 1), RigidState((0, 1, 0), (.2, -1, 0)))
        b = Body(1, Prism(1, 10, .2, 10), RigidState((0, -.1, 0)), True)
        states, records = solve_contacts((a, b), (narrow_phase(a, b),), Options(restitution=0, friction=.2))
        self.assertAlmostEqual(records[0].normal_impulse, 1, delta=1e-10)
        self.assertAlmostEqual(records[0].tangent_impulse[0], 2/35, delta=1e-10)
        self.assertAlmostEqual(states[0].v[0], 1/7, delta=1e-10)
        self.assertAlmostEqual(states[0].w[2], -1/7, delta=1e-10)
        self.assertAlmostEqual(states[0].v[0]+states[0].w[2], 0, delta=1e-10)


class SplitAndValidationTests(unittest.TestCase):
    def test_stationary_overlap_hand_depth_and_zero_physical_energy(self):
        world = World((Body(0, Sphere(1, 1)), Body(1, Sphere(1, 1), RigidState((1.99, 0, 0)))))
        options = Options(gravity=(0, 0, 0), restitution=0, friction=0)
        result, report = step_world(world, options)
        self.assertAlmostEqual(report.penetration_after, .00802, delta=1e-12)
        self.assertLess(report.penetration_after, report.penetration_before)
        for b in result.bodies:
            self.assertEqual(b.state.velocity, (0, 0, 0))
            self.assertEqual(b.state.omega, (0, 0, 0))
        independent_kinetic = sum(.5*sum(v*v for v in b.state.velocity)+.2*sum(w*w for w in b.state.omega)
                                  for b in result.bodies)  # literal m=1, R=1 => I=.4
        self.assertEqual(independent_kinetic, 0.)
        result = simulate(result, options, 100).world
        distance = math.dist(result.bodies[0].state.position, result.bodies[1].state.position)
        self.assertAlmostEqual(2-distance, .0001, delta=1e-10)

    def test_stationary_rotated_prism_overlap_does_not_create_velocity(self):
        a = Body(0, Prism(1, 1, 1, 1), RigidState((0, .52, 0), orientation=from_axis_angle((0, 0, 1), .1)))
        b = Body(1, Prism(1, 10, .2, 10), RigidState((0, -.1, 0)), True)
        world, report = step_world(World((a, b)), Options(gravity=(0, 0, 0), restitution=0, friction=0))
        self.assertLess(report.penetration_after, report.penetration_before)
        self.assertEqual(world.bodies[0].state.velocity, (0, 0, 0))
        self.assertEqual(world.bodies[0].state.omega, (0, 0, 0))
        capped, record = step_world(World((a, b)), Options(gravity=(0, 0, 0), restitution=0, friction=0, max_rotation=1e-5))
        before, after = a.state.orientation, capped.bodies[0].state.orientation
        angle = 4*math.atan2(math.sqrt(sum((x-y)**2 for x, y in zip(before, after))),
                             math.sqrt(sum((x+y)**2 for x, y in zip(before, after))))
        self.assertLessEqual(angle, 1e-5+1e-12)
        self.assertGreaterEqual(record.correction_caps, 1)

    def test_split_disabled_slop_and_correction_caps(self):
        for depth in (5e-5, 1.01e-4, .5):
            w = World((Body(0, Sphere(1, 1)), Body(1, Sphere(1, 1), RigidState((2-depth, 0, 0)))))
            options = Options(gravity=(0, 0, 0), restitution=0, friction=0, max_translation=1e-4)
            disabled, report = step_world(w, replace(options, enable_split=False))
            self.assertEqual(tuple(b.state.position for b in disabled.bodies), tuple(b.state.position for b in w.bodies))
            result, report = step_world(w, options)
            for before, after in zip(w.bodies, result.bodies):
                self.assertLessEqual(math.dist(before.state.position, after.state.position), 1e-4+1e-12)
            if depth <= options.slop:
                self.assertAlmostEqual(report.penetration_after, depth, delta=1e-12)
            elif depth == .5:
                self.assertEqual(report.correction_caps, 2)

    def test_invalid_parameters_states_and_immutable_failures(self):
        for kwargs in ({'dt': 0}, {'dt': float('nan')}, {'velocity_iterations': True}, {'split_iterations': 0},
                       {'friction': -1}, {'restitution': 2}, {'gravity': (0, float('inf'), 0)}, {'enable_split': 1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Options(**kwargs)
        with self.assertRaises(ValueError):
            RigidState(velocity=(float('nan'), 0, 0))
        with self.assertRaises(ValueError):
            World((Body(0, Sphere(1, 1)), Body(0, Sphere(1, 1))))
        with self.assertRaises(ValueError):
            Body(1, Sphere(1, 1), RigidState(velocity=(1, 0, 0)), True)
        w = World((Body(0, Sphere(1, 1)),))
        before = repr(w)
        with self.assertRaises(ValueError):
            step_world(w, backend='parallel')
        with self.assertRaises(ValueError):
            simulate(w, Options(), -1)
        with self.assertRaises(ValueError):
            simulate(w, Options(), 0, backend='invalid')
        with self.assertRaises(ValueError):
            step_world(w, False)
        self.assertEqual(repr(w), before)

    def test_free_flight_clocks_and_determinism(self):
        w = World((Body(0, Sphere(2, .2), RigidState((0, 5, 0), (1, 0, 0))),))
        options = Options(dt=.01)
        a = simulate(w, options, 100)
        b = simulate(w, options, 100)
        self.assertEqual(a.world, b.world)
        self.assertEqual(a.reports, b.reports)
        s = a.world.bodies[0].state
        self.assertAlmostEqual(s.position[0], 1, delta=1e-12)
        self.assertAlmostEqual(s.position[1], 5-9.81*.01**2*100*101/2, delta=1e-12)
        self.assertEqual(s.step_count, 100)
        self.assertAlmostEqual(s.time, 1, delta=1e-12)
        self.assertTrue(all(math.isfinite(x) for x in (*s.position, *s.velocity, *s.orientation, *s.omega)))


if __name__ == '__main__':
    unittest.main(verbosity=2)
