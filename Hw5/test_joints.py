"""Independent joint mechanics and constraint/work oracles; budgets in LOG.md."""

import contextlib
import io
import math
from pathlib import Path
import tempfile
import unittest
from dataclasses import replace
from Hw5.geometry import Sphere, Prism, Cylinder
from Hw5.rigid import RigidState, advance
from Hw5.spatial import from_axis_angle, compose, angular_distance
from Hw5.joints import (Joint, Load, SolverOptions, ConstraintError, make_joint,
                        joint_coordinates, joint_residuals, project_velocities,
                        project_constraints, advance_system)


def plus(a, b):
    return tuple(x+y for x, y in zip(a, b))


def times(a, k):
    return tuple(x*k for x in a)


def product(a, b):
    return sum(x*y for x, y in zip(a, b))


def crossed(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def rotated(q, v):
    # Independent test-local matrix, no production frame/constraint helpers.
    w, x, y, z = q
    r = ((1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)),
         (2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)),
         (2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)))
    return tuple(product(row, v) for row in r)


def norm(a):
    return math.sqrt(product(a, a))


def endpoint(states, index, anchor, axis):
    if index is None:
        return anchor, (0, 0, 0), axis, (0, 0, 0), (1, 0, 0, 0), (0, 0, 0)
    s = states[index]
    arm = rotated(s.orientation, anchor)
    w = rotated(s.orientation, s.omega)
    return plus(s.position, arm), plus(s.velocity, crossed(w, arm)), rotated(s.orientation, axis), w, s.orientation, arm


def independent_residuals(states, joint):
    pa, va, axis, wa, qa, _ = endpoint(states, joint.a, joint.anchor_a, joint.axis_a)
    pb, vb, axis_b, wb, qb, _ = endpoint(states, joint.b, joint.anchor_b, joint.axis_b)
    d, dv, dw = plus(pb, times(pa, -1)), plus(vb, times(va, -1)), plus(wb, times(wa, -1))
    if joint.kind == 'prismatic':
        d = plus(d, times(axis, -product(axis, d)))
        original_d = plus(pb, times(pa, -1))
        dv = plus(dv, times(crossed(wa, original_d), -1))
        dv = plus(dv, times(axis, -product(axis, dv)))
    if joint.kind == 'revolute':
        orientation = math.atan2(norm(crossed(axis, axis_b)), product(axis, axis_b))
        dw = plus(dw, times(axis, -product(axis, dw)))
    else:
        # Independent relative orientation via Frobenius distance of basis images.
        squared = 0
        for e in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            expected = rotated(qa, rotated(joint.reference, e))
            actual = rotated(qb, e)
            squared += math.dist(actual, expected)**2
        orientation = 2*math.asin(min(1, math.sqrt(squared)/(2*math.sqrt(2))))
    return norm(d), orientation, norm(dv), norm(dw)


def energy(states, masses, inertias, gravity=0):
    return sum(m*product(s.velocity, s.velocity)/2
               +sum(i*w*w for i, w in zip(diag, s.omega))/2+m*gravity*s.position[1]
               for s, m, diag in zip(states, masses, inertias))


def momenta(states, masses, inertias):
    p, l = (0, 0, 0), (0, 0, 0)
    for s, m, diag in zip(states, masses, inertias):
        mv = times(s.velocity, m)
        p = plus(p, mv)
        l = plus(l, plus(crossed(s.position, mv), rotated(s.orientation, tuple(i*w for i, w in zip(diag, s.omega)))))
    return p, l


def pair(spin=.4):
    # COM at x=.2; consistent rigid rotation and common translation.
    states = tuple(RigidState((x, 0, 0), (.3, -.2+spin*(x-.2), .1), omega=(0, 0, spin))
                   for x in (-1, 1))
    return states, (Sphere(2, .5), Sphere(3, .5))  # literal I=.2,.3


class JointTests(unittest.TestCase):
    def vec(self, a, b, tol=1e-9):
        self.assertEqual(len(a), len(b))
        for x, y in zip(a, b):
            self.assertAlmostEqual(x, y, delta=tol)

    def bounded(self, states, joint, tol=5e-9):
        values = independent_residuals(states, joint)
        for value in values:
            self.assertLess(value, tol)
        return values

    def test_world_prismatic_arbitrary_axis_force(self):
        q = (math.sqrt(.5), 0, 0, math.sqrt(.5))
        states = (RigidState((1, 2, 3), orientation=q),)
        joint = make_joint('prismatic', states, None, 0, (1, 2, 3), (2, -1, 2))
        # m=4; F=12*n+(3,6,0), transverse dot n=0; a=3*n=(2,-1,2).
        for _ in range(100):
            states, _ = advance_system(states, (Prism(4, 1, 2, 3),), (joint,), .01,
                                       gravity=(0, 0, 0), loads=(Load(force=(11, 2, 8)),))
            self.bounded(states, joint)
        self.vec(states[0].velocity, (2, -1, 2))
        self.vec(states[0].position, (2.01, 1.495, 4.01))
        self.vec(states[0].omega, (0, 0, 0))
        self.assertAlmostEqual(joint_coordinates(states, joint), 1.515, delta=1e-9)

    def test_world_prismatic_transverse_load_resisted(self):
        states = (RigidState(),)
        joint = make_joint('prismatic', states, None, 0, axis=(2, -1, 2))
        for _ in range(30):
            states, _ = advance_system(states, (Sphere(4, 1),), (joint,), .01,
                                       gravity=(0, 0, 0), loads=(Load(force=(3, 6, 0)),))
        self.vec(states[0].position, (0, 0, 0), 1e-12)
        self.vec(states[0].velocity, (0, 0, 0), 1e-12)

    def test_revolute_offset_pivot_hand_acceleration(self):
        states = (RigidState((1, 0, 0)),)
        joint = make_joint('revolute', states, None, 0)
        # m=3, COM Iz=5, pivot distance=1: Ip=8. torque=16 => alpha=2.
        states, report = advance_system(states, (Prism(3, 2, 4, 2),), (joint,), .001,
                                        gravity=(0, 0, 0), loads=(Load(torque=(0, 0, 16)),))
        self.vec(states[0].omega, (0, 0, .002), 2e-10)
        self.vec(states[0].velocity, (0, .002, 0), 1e-8)
        self.bounded(states, joint)
        self.assertGreater(joint_coordinates(states, joint), 1e-6)
        self.assertEqual((states[0].time, states[0].step_count), (.001, 1))
        self.assertEqual(len(report.stages), 2)

    def test_world_fixed_pose_velocity_and_offcenter_load(self):
        initial = RigidState((1, 1, 0), orientation=from_axis_angle((1, 2, 3), .4))
        states = (initial,)
        joint = make_joint('fixed', states, None, 0)
        for _ in range(100):
            states, _ = advance_system(states, (Prism(3, 1, 2, 3),), (joint,), .01,
                                       loads=(Load(force=(2, -3, 5), torque=(1, 2, 3), force_point=(2, 3, -1)),))
            self.bounded(states, joint)
        self.vec(states[0].position, initial.position)
        self.vec(states[0].velocity, (0, 0, 0))
        self.vec(states[0].omega, (0, 0, 0))
        self.assertLess(angular_distance(states[0].orientation, initial.orientation), 1e-9)

    def test_two_body_fixed_coupling_and_whole_motion(self):
        states, shapes = pair(0)
        states = tuple(replace(s, velocity=(0, 0, 0)) for s in states)
        joint = make_joint('fixed', states, 0, 1)
        for _ in range(100):
            states, _ = advance_system(states, shapes, (joint,), .01, gravity=(0, 0, 0),
                                       loads=(Load(force=(5, 0, 0), torque=(0, 0, 2)), Load()))
            self.bounded(states, joint)
        center = tuple((2*states[0].position[i]+3*states[1].position[i])/5 for i in range(3))
        velocity = tuple((2*states[0].velocity[i]+3*states[1].velocity[i])/5 for i in range(3))
        self.vec(center, (.705, 0, 0))
        self.vec(velocity, (1, 0, 0))
        self.assertGreater(norm(states[1].omega), .1)
        self.assertGreater(angular_distance(states[0].orientation, (1, 0, 0, 0)), .05)
        self.assertAlmostEqual(math.dist(states[0].position, states[1].position), 2, delta=1e-9)

    def test_long_run_revolute_arbitrary_axis_nonidentity_and_sign(self):
        q = from_axis_angle((1, 2, 3), .6)
        axis, center = rotated(q, (0, 0, 1)), rotated(q, (1, 0, 0))
        velocity = crossed(times(axis, .3), center)
        a = (RigidState(center, velocity, q, (0, 0, .3)),)
        b = (replace(a[0], orientation=times(q, -1)),)
        joint = make_joint('revolute', a, None, 0, axis=axis)
        maxima = [0.0]*4
        for _ in range(600):
            kwargs = dict(gravity=(0, 0, 0), loads=(Load(torque=times(axis, .2)),))
            a, _ = advance_system(a, (Prism(3, 2, 4, 2),), (joint,), .002, **kwargs)
            b, _ = advance_system(b, (Prism(3, 2, 4, 2),), (joint,), .002, **kwargs)
            values = self.bounded(a, joint)
            maxima = [max(x, y) for x, y in zip(maxima, values)]
            self.assertLess(abs(norm(a[0].orientation)-1), 2e-14)
            self.assertLess(angular_distance(a[0].orientation, b[0].orientation), 1e-9)
            self.vec(a[0].position, b[0].position)
        self.assertGreater(abs(joint_coordinates(a, joint)), .3)
        print('600-step arbitrary-axis revolute max residuals (m,rad,m/s,rad/s):', maxima)

    def test_dynamic_prismatic_rotating_parent_transport(self):
        states = (RigidState((0, 0, 0), (0, -.3, 0), omega=(0, 0, .3)),
                  RigidState((2, 0, 0), (.2, .3, 0), omega=(0, 0, .3)))
        shapes = (Sphere(2, .5), Sphere(3, .5))
        joint = make_joint('prismatic', states, 0, 1, (1, 0, 0), (1, 0, 0))
        maxima = [0.0]*4
        for _ in range(500):
            states, _ = advance_system(states, shapes, (joint,), .002, gravity=(0, 0, 0))
            maxima = [max(x, y) for x, y in zip(maxima, self.bounded(states, joint))]
        self.assertGreater(joint_coordinates(states, joint), .1)
        self.assertGreater(angular_distance(states[0].orientation, (1, 0, 0, 0)), .1)
        print('500-step rotating-parent slider max residuals:', maxima)

    def test_two_body_revolute_relative_spin_allowed(self):
        states = (RigidState(omega=(0, 0, .5)), RigidState(omega=(0, 0, -.2)))
        shapes = (Sphere(2, .5), Sphere(3, .5))
        joint = make_joint('revolute', states, 0, 1, axis=(0, 0, 1))
        for _ in range(100):
            states, _ = advance_system(states, shapes, (joint,), .005, gravity=(0, 0, 0))
            self.bounded(states, joint)
        self.assertAlmostEqual(joint_coordinates(states, joint), -.35, delta=1e-6)
        self.assertGreater(norm(plus(states[1].omega, times(states[0].omega, -1))), .6)

    def test_acyclic_chain_couples_three_finite_bodies(self):
        states = tuple(RigidState((x, 0, 0)) for x in (0, 1, 2))
        shapes = (Sphere(1, .3), Sphere(2, .3), Sphere(3, .3))
        joints = (make_joint('prismatic', states, None, 0, axis=(1, 0, 0)),
                  make_joint('fixed', states, 0, 1, (.5, 0, 0)),
                  make_joint('revolute', states, 1, 2, (1.5, 0, 0)))
        # F=6 N on only the last body accelerates the total 6 kg assembly by 1 m/s^2.
        for _ in range(20):
            states, _ = advance_system(states, shapes, joints, .01, gravity=(0, 0, 0),
                                       loads=(Load(), Load(), Load(force=(6, 0, 0))))
            for joint in joints:
                self.bounded(states, joint)
        for index, s in enumerate(states):
            self.vec(s.velocity, (.2, 0, 0))
            self.vec(s.position, (index+.021, 0, 0))

    def test_joint_load_lifetime_and_optional_damping(self):
        axis = (2/3, -1/3, 2/3)
        states = (RigidState(),)
        shape = Prism(4, 1, 2, 3)
        joint = make_joint('prismatic', states, None, 0, axis=axis)
        states, _ = advance_system(states, (shape,), (joint,), .1, gravity=(0, 0, 0),
                                   loads=(Load(force=times(axis, 12)),))
        states, _ = advance_system(states, (shape,), (joint,), .1, gravity=(0, 0, 0))
        self.vec(states[0].velocity, times(axis, .3))
        self.vec(states[0].position, times(axis, .06))
        states, _ = advance_system(states, (shape,), (joint,), .1, gravity=(0, 0, 0),
                                   loads=(Load(linear_damping=2),))
        self.vec(states[0].velocity, times(axis, .285))
        self.vec(states[0].position, times(axis, .0885))
        # Damping torque about COM is transmitted through the offset-pivot inertia.
        hinge_states = (RigidState((1, 0, 0), (0, 1, 0), omega=(0, 0, 1)),)
        hinge = make_joint('revolute', hinge_states, None, 0)
        _, report = advance_system(hinge_states, (Prism(3, 2, 4, 2),), (hinge,), .001,
                                   gravity=(0, 0, 0), loads=(Load(angular_damping=4),))
        # Ip=5+3=8; alpha=-4/8. Inspect the kick before geometric drift projection.
        self.assertAlmostEqual(report.stages[0].after[0].omega[2], .9995, delta=1e-12)

    def test_isolated_momenta_and_energy_refinement(self):
        errors = []
        momentum_errors = []
        for count in (250, 500):
            states, shapes = pair()
            joint = make_joint('fixed', states, 0, 1)
            p0, l0 = momenta(states, (2, 3), ((.2,)*3, (.3,)*3))
            e0 = energy(states, (2, 3), ((.2,)*3, (.3,)*3))
            max_p = max_l = max_e = 0.0
            # Already consistent; no initialization projection in this conservation run.
            self.bounded(states, joint)
            for _ in range(count):
                states, _ = advance_system(states, shapes, (joint,), 1/count, gravity=(0, 0, 0))
                p, l = momenta(states, (2, 3), ((.2,)*3, (.3,)*3))
                max_p, max_l = max(max_p, math.dist(p, p0)), max(max_l, math.dist(l, l0))
                max_e = max(max_e, abs(energy(states, (2, 3), ((.2,)*3, (.3,)*3))-e0))
            self.assertLess(max_p, 1e-9)
            self.assertLess(max_l, .005)
            self.assertLess(max_e, .005)
            errors.append((max_l, max_e))
            momentum_errors.append(max_p)
        for coarse, fine in zip(errors[0], errors[1]):
            self.assertGreater(fine/coarse, .35)
            self.assertLess(fine/coarse, .65)
        print('isolated fixed assembly max L/energy errors h=.004,.002:', errors)
        print('isolated total linear momentum max errors kg*m/s:', momentum_errors)

    def test_revolute_pendulum_energy_and_first_order(self):
        # Independent scalar RK4 reference to theta''=-(19.62/2.032)*sin(theta).
        theta, speed, h_ref = .3, 0.0, 1/16384
        def f(t, w):
            return w, -(19.62/2.032)*math.sin(t)
        for _ in range(16384):
            a = f(theta, speed)
            b = f(theta+h_ref*a[0]/2, speed+h_ref*a[1]/2)
            c = f(theta+h_ref*b[0]/2, speed+h_ref*b[1]/2)
            d = f(theta+h_ref*c[0], speed+h_ref*c[1])
            theta += h_ref*(a[0]+2*b[0]+2*c[0]+d[0])/6
            speed += h_ref*(a[1]+2*b[1]+2*c[1]+d[1])/6
        errors = []
        for count in (100, 200, 400):
            q = (math.cos(.15), 0, 0, math.sin(.15))
            states = (RigidState((math.sin(.3), -math.cos(.3), 0), orientation=q),)
            joint = make_joint('revolute', states, None, 0)
            e0 = energy(states, (2,), ((.032,)*3,), 9.81)
            max_drift = 0
            for _ in range(count):
                states, _ = advance_system(states, (Sphere(2, .2),), (joint,), 1/count)
                self.bounded(states, joint)
                max_drift = max(max_drift, abs(energy(states, (2,), ((.032,)*3,), 9.81)-e0))
            measured = math.atan2(states[0].position[0], -states[0].position[1])
            error = abs(measured-theta)
            self.assertLess(error, .02)
            self.assertLess(max_drift, .15)
            errors.append((error, max_drift))
        for a, b in zip(errors, errors[1:]):
            for coarse, fine in zip(a, b):
                self.assertGreater(fine/coarse, .35)
                self.assertLess(fine/coarse, .65)
        print('pendulum reference theta=', theta, 'endpoint angle/energy errors h=.01,.005,.0025:', errors)

    def test_ideal_reaction_power_both_bodies(self):
        for kind in ('fixed', 'revolute', 'prismatic'):
            states, shapes = pair()
            joint = make_joint(kind, states, 0, 1, axis=(1, 0, 0) if kind == 'prismatic' else (0, 0, 1))
            if kind == 'prismatic':
                states = (states[0], replace(states[1], position=(1.4, 0, 0)))
            kicked = (replace(states[0], velocity=plus(states[0].velocity, (.3, -.2, .4)),
                              omega=(.1, -.2, .7)), states[1])
            after, stage = project_velocities(kicked, shapes, (joint,))
            reaction = stage.reactions[0]
            powers, anchor_powers = [], []
            for index, force, torque, anchor, axis in (
                (0, reaction.linear_a, reaction.angular_a, joint.anchor_a, joint.axis_a),
                (1, reaction.linear_b, reaction.angular_b, joint.anchor_b, joint.axis_b)):
                _, u, _, w, _, arm = endpoint(after, index, anchor, axis)
                powers.append(product(force, after[index].velocity)+product(torque, w))
                couple = plus(torque, times(crossed(arm, force), -1))
                anchor_powers.append(product(force, u)+product(couple, w))
            self.assertGreater(max(abs(x) for x in powers), 1e-4)
            self.assertAlmostEqual(sum(powers), 0, delta=1e-10)
            self.assertAlmostEqual(sum(anchor_powers), 0, delta=1e-10)
            self.vec(plus(reaction.linear_a, reaction.linear_b), (0, 0, 0), 1e-10)
            total_torque = plus(plus(crossed(after[0].position, reaction.linear_a), reaction.angular_a),
                                plus(crossed(after[1].position, reaction.linear_b), reaction.angular_b))
            self.vec(total_torque, (0, 0, 0), 1e-10)
            self.bounded(after, joint)
            print(kind, 'impulse-velocity pairings per body / sum (J):', powers, sum(powers))

    def test_stationary_world_power_and_initialization_energy(self):
        states = (RigidState((1, 0, 0), (0, 1, 0), omega=(0, 0, 1)),)
        joint = make_joint('revolute', states, None, 0)
        kicked = (replace(states[0], velocity=(.2, 1.3, .4)),)
        with self.assertRaises(ConstraintError):
            advance_system(kicked, (Sphere(2, .5),), (joint,), .01)
        result, report = project_constraints(kicked, (Sphere(2, .5),), (joint,))
        reaction = report.stages[0].reactions[0]
        work = product(reaction.linear_b, result[0].velocity)+product(reaction.angular_b, result[0].omega)
        self.assertAlmostEqual(work, 0, delta=1e-10)
        before = energy(kicked, (2,), ((.2,)*3,))
        after = energy(result, (2,), ((.2,)*3,))
        self.assertLess(after, before)
        delta_v = plus(result[0].velocity, times(kicked[0].velocity, -1))
        delta_w = plus(result[0].omega, times(kicked[0].omega, -1))
        quadratic = product(reaction.linear_b, delta_v)+product(reaction.angular_b, delta_w)
        self.assertAlmostEqual(after-before, -.5*quadratic, delta=1e-10)
        self.assertEqual((result[0].time, result[0].step_count), (0, 0))
        print('explicit initialization energy before/after J:', before, after)

    def test_scene_rotation_symmetry(self):
        gq = from_axis_angle((1, 2, -1), .7)
        for kind in ('fixed', 'revolute', 'prismatic'):
            states, shapes = pair(.2)
            axis, anchor = (2, -1, 2), (.1, .2, -.1)
            joint = make_joint(kind, states, 0, 1, anchor, axis)
            transformed = tuple(replace(s, position=rotated(gq, s.position),
                                        velocity=rotated(gq, s.velocity), orientation=compose(gq, s.orientation)) for s in states)
            other_joint = make_joint(kind, transformed, 0, 1, rotated(gq, anchor), rotated(gq, axis))
            loads = (Load(force=(.4, -.2, .3), torque=(.2, .1, -.3), force_point=(.3, .7, -.2)), Load())
            other_loads = tuple(Load(rotated(gq, l.force), rotated(gq, l.torque),
                                     None if l.force_point is None else rotated(gq, l.force_point)) for l in loads)
            for _ in range(30):
                states, _ = advance_system(states, shapes, (joint,), .002, gravity=(0, 0, 0), loads=loads)
                transformed, _ = advance_system(transformed, shapes, (other_joint,), .002,
                                                 gravity=(0, 0, 0), loads=other_loads)
                for a, b in zip(states, transformed):
                    self.vec(b.position, rotated(gq, a.position), 1e-8)
                    self.vec(b.velocity, rotated(gq, a.velocity), 1e-8)
                    self.vec(b.omega, a.omega, 1e-8)
                    self.assertLess(angular_distance(b.orientation, compose(gq, a.orientation)), 1e-8)

    def test_translation_invariance_world_support_moves(self):
        shift = (3, -2, 4)
        a = (RigidState((1, 0, 0)),)
        b = (replace(a[0], position=plus(a[0].position, shift)),)
        ja = make_joint('revolute', a, None, 0)
        jb = make_joint('revolute', b, None, 0, shift)
        for _ in range(100):
            a, _ = advance_system(a, (Sphere(2, .5),), (ja,), .005)
            b, _ = advance_system(b, (Sphere(2, .5),), (jb,), .005)
            self.vec(b[0].position, plus(a[0].position, shift), 1e-8)
            self.vec(b[0].velocity, a[0].velocity, 1e-8)
            self.vec(b[0].omega, a[0].omega, 1e-8)

    def test_equilibrium_zero_damping_and_no_joint_regression(self):
        for kind in ('fixed', 'revolute', 'prismatic'):
            states = (RigidState((1, 2, 3)),)
            j = make_joint(kind, states, None, 0, (1, 2, 3), (1, 2, 3))
            b, _ = advance_system(states, (Sphere(2, 1),), (j,), .01, gravity=(0, 0, 0))
            c, _ = advance_system(states, (Sphere(2, 1),), (j,), .01, gravity=(0, 0, 0), loads=(Load(linear_damping=0, angular_damping=0),))
            self.assertEqual(b, c)
            self.assertEqual(b[0].position, states[0].position)
        states, shapes = pair()
        loads = (Load(force=(1, 2, 3), linear_damping=.2), Load(torque=(.1, .2, .3), angular_damping=.1))
        result, report = advance_system(states, shapes, (), .01, loads=loads, ground=True)
        for i, (s, shape, load) in enumerate(zip(states, shapes, loads)):
            expected, contact = advance(s, shape, .01, force=load.force, torque=load.torque,
                                         linear_damping=load.linear_damping, angular_damping=load.angular_damping)
            self.assertEqual((result[i], report.contacts[i]), (expected, contact))

    def test_validation_topology_failures_and_inputs_unchanged(self):
        states, shapes = pair(0)
        j = make_joint('fixed', states, 0, 1)
        snapshot = repr((states, shapes, j))
        for axis in ((0, 0, 0), (1, 2), (True, 0, 0), (float('nan'), 0, 1)):
            with self.assertRaises(ValueError):
                make_joint('revolute', states, 0, 1, axis=axis)
        for a, b in ((0, 0), (0, 2), (True, 1), (-1, 1), (0, None)):
            with self.assertRaises(ValueError):
                make_joint('fixed', states, a, b)
        for bad in (lambda: make_joint('spring', states, 0, 1),
                    lambda: Load(force=(0, float('inf'), 0)), lambda: SolverOptions(position=0),
                    lambda: SolverOptions(max_iterations=True), lambda: Joint('fixed', 0, 1, (1, 2), (0, 0, 0)),
                    lambda: Joint('prismatic', None, 0, (0, 0, 0), (0, 0, 0), (1, 0, 0), (0, 1, 0))):
            with self.assertRaises(ValueError):
                bad()
        world = make_joint('fixed', states, None, 0)
        world_b = make_joint('fixed', states, None, 1)
        for joints, kwargs in (((j, j), {}), ((world, j, world_b), {}), ((j,), {'ground': True}),
                               ((replace(j, b=3),), {})):
            with self.assertRaises(ValueError):
                advance_system(states, shapes, joints, .01, **kwargs)
        with self.assertRaises(ValueError):
            advance_system((states[0], replace(states[1], time=1)), shapes, (j,), .01)
        # One nonlinear projection iteration is insufficient for this offset hinge.
        origin = (RigidState((1, 0, 0)),)
        hinge = make_joint('revolute', origin, None, 0)
        perturbed = (replace(origin[0], orientation=from_axis_angle((0, 1, 0), .2)),)
        with self.assertRaises(ConstraintError):
            project_constraints(perturbed, (Sphere(2, .5),), (hinge,), options=SolverOptions(max_iterations=1))
        corrected, report = project_constraints(perturbed, (Sphere(2, .5),), (hinge,))
        self.bounded(corrected, hinge)
        self.assertGreater(report.position_iterations, 1)
        with self.assertRaises(ConstraintError):
            project_constraints(origin, (Sphere(2, .5),), (replace(hinge, axis_b=(0, 0, -1)),))
        world_fixed = make_joint('fixed', (RigidState(),), None, 0)
        with self.assertRaises(ConstraintError):
            project_constraints((RigidState(orientation=from_axis_angle((1, 1, 1), .7)),),
                                (Sphere(2, .5),), (world_fixed,))
        with self.assertRaises(ConstraintError):
            project_constraints((replace(origin[0], position=(2, 0, 0)),), (Sphere(2, .5),), (hinge,))
        # An acyclic but numerically singular mass-ratio configuration is rejected.
        with self.assertRaises(ConstraintError):
            project_velocities(states, (Sphere(1e-20, 1), Sphere(1e20, 1)), (world, j))
        # Finite extreme parameters can overflow a residual; NaN must not pass max checks.
        huge = (RigidState((1e308, 1e308, 1e308)),)
        huge_joint = Joint('fixed', None, 0, (-1e308, -1e308, -1e308), (0, 0, 0))
        with self.assertRaises(ValueError):
            project_constraints(huge, (Sphere(2, .5),), (huge_joint,))
        advance_system(states, shapes, (j,), .01, gravity=(0, 0, 0))
        self.assertEqual(repr((states, shapes, j)), snapshot)
        self.assertEqual(joint_residuals(states, (j,)).position_m, 0)

    def test_joint_example_headless_smoke(self):
        from Hw5.joints_example import main
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(main(['--headless']), 0)
        self.assertIn('prismatic', output.getvalue())
        self.assertIn('revolute', output.getvalue())
        self.assertIn('fixed', output.getvalue())
        self.assertIn('residual', output.getvalue())

    def test_joint_example_snapshot_smoke(self):
        from Hw5.joints_example import main
        with tempfile.TemporaryDirectory() as folder, contextlib.redirect_stdout(io.StringIO()):
            path = Path(folder)/'joints.png'
            self.assertEqual(main(['--headless', '--snapshot', str(path)]), 0)
            self.assertGreater(path.stat().st_size, 10000)
            self.assertEqual(path.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')


if __name__ == '__main__':
    unittest.main(verbosity=2)
