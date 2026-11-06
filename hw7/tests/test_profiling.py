"""Short tests of telemetry, graph accounting and failure/completion semantics."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
import uuid
from Hw5.geometry import Sphere
from Hw5.rigid import RigidState
from hw7.model import Body, World, Options
from hw7 import world as physics
from hw7.profiling import Telemetry, contact_graph, main, OUTPUT


class ProfilingTests(unittest.TestCase):
    def test_stage_and_plain_collision_results_are_exact(self):
        initial = World((Body(0, Sphere(1, 1)), Body(1, Sphere(1, 1), RigidState((1.99, 0, 0), (-1, 0, 0)))))
        opts = Options(gravity=(0, 0, 0))
        reference = physics.step_world(initial, opts)
        original = physics.step_world
        timer = Telemetry()
        with timer:
            measured = physics.step_world(initial, opts)
        self.assertEqual(reference, measured)
        self.assertIs(physics.step_world, original)
        record = timer.result()
        self.assertAlmostEqual(record['exclusive_sum_seconds'], record['inclusive_seconds']['step_total'], delta=1e-12)
        self.assertIn('physical_impulses', record['calls'])
        self.assertIn('split_impulses', record['calls'])

    def test_wrapped_bindings_restore_on_failure(self):
        original = physics.step_world
        with self.assertRaises(ValueError):
            with Telemetry():
                physics.step_world('invalid')
        self.assertIs(physics.step_world, original)

    def test_static_shared_bin_does_not_join_dynamic_islands(self):
        reports = SimpleNamespace(impulses=(SimpleNamespace(a=0, b=10), SimpleNamespace(a=1, b=10)))
        graph = contact_graph(reports, {10})
        self.assertEqual(graph['islands'], 2)
        self.assertEqual(graph['colors'], 1)
        self.assertEqual(graph['largest_island_row_share'], .5)
        chain = SimpleNamespace(impulses=(SimpleNamespace(a=0, b=1), SimpleNamespace(a=1, b=2)))
        graph = contact_graph(chain, set())
        self.assertEqual(graph['islands'], 1)
        self.assertEqual(graph['colors'], 2)

    def test_budgeted_profile_returns_nonzero_and_saves_partial(self):
        label = 'test_partial_'+uuid.uuid4().hex
        with redirect_stdout(io.StringIO()):
            code = main(['measure', '--label', label, '--mode', 'cprofile', '--steps', '10', '--max-seconds', '.000001'])
        self.assertEqual(code, 2)
        data = json.loads((OUTPUT/label/'run_00.json').read_text(encoding='utf-8'))
        self.assertFalse(data['complete'])
        self.assertEqual(data['status'], 'partial_budget')
        self.assertLess(data['completed_steps'], data['requested_steps'])
        self.assertTrue((OUTPUT/label/'run_00.prof').is_file())


if __name__ == '__main__':
    unittest.main(verbosity=2)
