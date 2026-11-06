"""Short evidence-harness checks; never changes production physics."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time
import unittest
from hw7.model import Body, World, Options
from Hw5.geometry import Sphere
from Hw5.rigid import RigidState
from hw7.world import simulate
from hw7.verify import Tee
from .runner import p, OUTPUT, canonical, stepping, configure
from .audit import accept


class HarnessChecks(unittest.TestCase):
    def test_original_accepted_realized_state_still_passes(self):
        data = json.loads((p.ROOT/'hw7/evidence/serial_default.json').read_text())
        self.assertTrue(accept(data)['accepted'])

    def test_rejects_original_limit_violation(self):
        data = json.loads((p.ROOT/'hw7/evidence/serial_default.json').read_text())
        for key, value in (('max_penetration_after_m', .03001),
                           ('final_two_seconds_max_penetration_m', .01001),
                           ('body_body_impulse_rows', 0), ('max_quaternion_norm_error', 1e-10)):
            bad = deepcopy(data)
            bad['summary'][key] = value
            with self.assertRaises(AssertionError):
                accept(bad)

    def test_rejects_containment_static_and_nonfinite_state(self):
        data = json.loads((p.ROOT/'hw7/evidence/serial_default.json').read_text())
        for kind in ('outside', 'static', 'nan'):
            bad = deepcopy(data)
            if kind == 'outside':
                bad['final']['bodies'][0]['state']['position'][0] = 2.
            elif kind == 'static':
                bad['final']['bodies'][30]['state']['position'][0] += .1
            else:
                bad['final']['bodies'][0]['state']['velocity'][0] = float('nan')
            with self.assertRaises(AssertionError):
                accept(bad)

    def test_new_loop_exactly_matches_existing_simulate_and_canonical_digest(self):
        initial = World((Body(0, Sphere(1, 1)), Body(1, Sphere(1, 1), RigidState((1.99, 0, 0)))))
        opts = Options(gravity=(0, 0, 0))
        old = simulate(initial, opts, 8)
        world, reports, elapsed, io = stepping(initial, opts, 8, None)
        self.assertEqual(old.world, world)
        self.assertEqual(old.reports, reports)
        expected = p.sha(json.dumps([asdict(world), [asdict(r) for r in reports]], sort_keys=True, allow_nan=False).encode())
        self.assertEqual(expected, canonical(world, reports))
        self.assertGreater(elapsed, 0)
        self.assertEqual(io, 0)


def main():
    configure()
    with (OUTPUT/'harness_checks.log').open('x', encoding='utf-8') as log:
        stream = Tee(sys.stdout, log)
        print('Command:', sys.executable, *sys.orig_argv[1:], file=stream)
        start = time.perf_counter()
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(HarnessChecks))
        p.atomic_json(OUTPUT/'harness_checks.json', dict(tests=result.testsRun, failures=len(result.failures),
            errors=len(result.errors), successful=result.wasSuccessful(), seconds=time.perf_counter()-start))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
