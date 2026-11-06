"""Preserve Part 4 short test results without overwriting prior evidence."""
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from .parallel import THREAD_LIMITS

os.environ.update(THREAD_LIMITS)
ROOT = Path(__file__).resolve().parent/'evidence/parallel_pilot'


def main():
    from .profiling import atomic_json, sources
    from .verify import Tee
    label = sys.argv[1] if len(sys.argv) > 1 else 'tests'
    if not label.replace('_', '').isalnum():
        raise ValueError('invalid label')
    ROOT.mkdir(parents=True, exist_ok=True)
    temp = ROOT/'native_tmp/parent'
    temp.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(temp)
    os.environ['TMP'] = os.environ['TEMP'] = str(temp)
    modules = ['hw7.tests.test_parallel', 'hw7.tests.test_geometry',
               'hw7.tests.test_solver', 'hw7.tests.test_profiling']
    with (ROOT/(label+'.log')).open('x', encoding='utf-8') as log:
        stream = Tee(sys.stdout, log)
        print('Command:', sys.executable, *sys.orig_argv[1:], file=stream)
        suite = unittest.defaultTestLoader.loadTestsFromNames(modules)
        started = time.perf_counter()
        import hw7.tests.test_profiling as profiling_tests
        with patch('hw7.profiling.OUTPUT', ROOT/'profiling_tests'), patch.object(profiling_tests, 'OUTPUT', ROOT/'profiling_tests'):
            result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        atomic_json(ROOT/(label+'.json'), dict(command=[sys.executable, *sys.orig_argv[1:]],
            tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
            skipped=len(result.skipped), successful=result.wasSuccessful(), seconds=time.perf_counter()-started,
            source=sources()))
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
