"""Headless end-to-end scene checks and static plotting smoke test."""

import math
from pathlib import Path
import tempfile
import unittest
from Hw5.showcase import simulate, main


class ShowcaseTests(unittest.TestCase):
    def test_three_body_headless_scene(self):
        shapes, frames, impacts = simulate()
        self.assertEqual(len(shapes), 3)
        self.assertEqual(len(frames), 91)
        self.assertTrue(all(n > 0 for n in impacts))
        for i in range(3):
            final = frames[-1][i]
            self.assertEqual(final.step_count, 720)
            self.assertAlmostEqual(final.time, 3, delta=1e-12)
            self.assertNotEqual(frames[0][i].orientation, frames[10][i].orientation)
            self.assertAlmostEqual(sum(x*x for x in final.orientation), 1, delta=1e-12)
            self.assertTrue(all(math.isfinite(x) for x in (*final.position, *final.omega)))

    def test_snapshot_smoke(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'scene.png'
            self.assertEqual(main(['--headless', '--snapshot', str(path)]), 0)
            self.assertGreater(path.stat().st_size, 10000)
            self.assertEqual(path.read_bytes()[:8], b'\x89PNG\r\n\x1a\n')


if __name__ == '__main__':
    unittest.main(verbosity=2)
