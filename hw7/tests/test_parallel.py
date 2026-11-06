"""Real spawn tests: equality, scheduling, lifecycle and failure semantics."""
from dataclasses import replace
from itertools import combinations_with_replacement
import unittest
from unittest.mock import patch
from Hw5.geometry import Prism, Sphere, Cylinder
from Hw5.rigid import RigidState
from Hw5.spatial import from_axis_angle
from hw7.model import Body, World, Options
from hw7.world import detect, step_world, simulate, kinetic_energy
from hw7.parallel import ParallelDetector, WorkerError


def bodies():
    return (Body(0, Prism(1, 1, 1, 1), RigidState((0, .52, 0), (.1, -.2, 0),
                 from_axis_angle((0, 0, 1), .1), (.2, .1, .3))),
            Body(1, Cylinder(1, .4, .8), RigidState((2, .4, 0), (0, -.1, 0),
                 from_axis_angle((1, 0, 0), 1.5), (.1, .3, .2))),
            Body(2, Prism(1, 10, .2, 10), RigidState((0, -.1, 0)), True))


class ParallelTests(unittest.TestCase):
    def test_all_six_shape_pairs_cache_and_enrich_through_workers(self):
        shapes = (Prism(1, 2, 2, 2), Sphere(1, 1), Cylinder(1, 1, 2))
        opts = Options()
        with ParallelDetector(2, 1) as pool:
            for a, b in combinations_with_replacement(shapes, 2):
                for distance in (1.9, 2., 2.01):
                    pair = (Body(0, a), Body(1, b, RigidState((distance, 0, 0))))
                    expected = detect(pair, opts)
                    actual = detect(pair, opts, detector=pool)
                    self.assertEqual(expected, actual)
                    for enrich in (True, False):
                        self.assertEqual(detect(pair, opts, expected[1], enrich),
                                         detect(pair, opts, actual[1], enrich, detector=pool))
            self.assertGreater(sum(pool.worker_pairs.values()), 0)
        self.assertTrue(pool.statistics()['all_workers_exited'])

    def test_rotating_multistep_world_reports_cache_and_both_barriers(self):
        start, opts = World(bodies()), Options(dt=1/480)
        reference = simulate(start, opts, 6)
        self.assertTrue(any(r.manifolds for r in reference.reports))
        for workers, batch in ((1, 1), (2, 2), (4, 4)):
            result = simulate(start, opts, 6, backend='parallel', workers=workers, batch_size=batch)
            self.assertEqual(reference.world, result.world)
            self.assertEqual(reference.reports, result.reports)
            stats = result.backend_statistics
            self.assertEqual(stats['counts']['trial_calls'], 6)
            self.assertEqual(stats['counts']['diagnostic_calls'], 6)
            self.assertGreater(stats['counts']['worker_pairs'], 0)
            self.assertTrue(stats['all_workers_exited'])

    def test_pool_reuse_and_gather_under_forced_reverse_readiness(self):
        # Every result is produced by real workers. Change only the parent's
        # readiness consumption order to force later batches to be consumed first.
        opts = Options()
        pair = (Body(0, Sphere(1, 1)), Body(1, Sphere(1, 1), RigidState((1.99, 0, 0))))
        from hw7.manifolds import narrow_phase
        right = [replace(pair[1], state=RigidState((1.9+i*.01, 0, 0))) for i in range(4)]
        tasks = [(i, ((pair[0], right[i], None),), opts, True) for i in range(4)]
        with ParallelDetector(2, 1) as pool:
            original = tuple(p.pid for p in pool.processes)
            original_wait = pool._wait
            def last_first(pending):
                if pool.connections[1] in pending:
                    return original_wait({pool.connections[1]})
                return original_wait(pending)
            with patch.object(pool, '_wait', side_effect=last_first):
                got = pool.map_batches(tasks)
            self.assertNotEqual(pool.completion_orders[-1], sorted(pool.completion_orders[-1]))
            self.assertEqual(len(got), 4)
            self.assertEqual(got, tuple(narrow_phase(pair[0], b, None, opts) for b in right))
            detect(pair, opts, detector=pool)
            self.assertEqual(tuple(p.pid for p in pool.processes), original)

    def test_worker_error_propagates_and_cleans_without_fallback(self):
        pair = Body(0, Sphere(1, 1))
        pool = ParallelDetector(2, 1)
        with self.assertRaisesRegex(WorkerError, 'distinct body ids'):
            with pool:
                pool.map_batches([(0, ((pair, pair, None),), Options(), True)])
        self.assertFalse(pool.active)
        self.assertTrue(all(not p.is_alive() for p in pool.processes))
        with self.assertRaises(ValueError):
            pool.map_batches([])

    def test_parent_interrupt_cleans_owned_workers(self):
        pool = ParallelDetector(2)
        with self.assertRaises(KeyboardInterrupt):
            with pool:
                with patch.object(pool, '_wait', side_effect=KeyboardInterrupt):
                    pair = Body(0, Sphere(1, 1))
                    pool.map_batches([(0, ((pair, replace(pair, id=1), None),), Options(), True)])
        self.assertTrue(all(not p.is_alive() for p in pool.processes))

    def test_startup_failure_cleans_all_created_children(self):
        pool = ParallelDetector(2)
        with patch.object(pool, '_wait', side_effect=RuntimeError('readiness failure')):
            with self.assertRaisesRegex(RuntimeError, 'readiness failure'):
                pool.__enter__()
        self.assertTrue(pool.processes)
        self.assertTrue(all(not p.is_alive() for p in pool.processes))

    def test_unexpected_worker_exit_is_error_and_cleans_other_workers(self):
        pool = ParallelDetector(2)
        with self.assertRaises(WorkerError):
            with pool:
                pool.processes[0].terminate()
                pool.processes[0].join()
                pair = Body(0, Sphere(1, 1))
                pool.map_batches([(0, ((pair, replace(pair, id=1), None),), Options(), True)])
        self.assertTrue(all(not p.is_alive() for p in pool.processes))

    def test_invalid_settings_closed_pool_and_threshold(self):
        for kwargs in ({'workers': 0}, {'workers': True}, {'batch_size': 0}, {'batch_size': 1.5},
                       {'serial_threshold': -1}):
            with self.assertRaises(ValueError):
                ParallelDetector(**kwargs)
        with self.assertRaises(ValueError):
            step_world(World(bodies()), backend='parallel')
        with self.assertRaises(ValueError):
            simulate(World(bodies()), Options(), 0, backend='parallel', workers=0)
        pool = ParallelDetector(1, 1, 100)
        with pool:
            self.assertEqual(detect(bodies(), Options()), detect(bodies(), Options(), detector=pool))
            self.assertEqual(pool.counts['worker_pairs'], 0)
            self.assertGreater(pool.counts['serial_pairs'], 0)
        with self.assertRaises(ValueError):
            detect(bodies(), Options(), detector=pool)
        with self.assertRaises(ValueError):
            pool.__enter__()

    def test_stationary_split_exact_zero_energy(self):
        start = World((Body(0, Sphere(1, 1)), Body(1, Sphere(1, 1), RigidState((1.99, 0, 0)))))
        opts = Options(gravity=(0, 0, 0), restitution=0, friction=0)
        expected = simulate(start, opts, 8)
        actual = simulate(start, opts, 8, backend='parallel', workers=2, batch_size=1)
        self.assertEqual(expected.world, actual.world)
        self.assertEqual(expected.reports, actual.reports)
        self.assertEqual(kinetic_energy(actual.world), 0.)
        for b in actual.world.bodies:
            self.assertEqual(b.state.velocity, (0., 0., 0.))
            self.assertEqual(b.state.omega, (0., 0., 0.))


if __name__ == '__main__':
    unittest.main(verbosity=2)
