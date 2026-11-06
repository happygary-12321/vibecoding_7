"""Run verbose serial checks, preserving output and generated files under hw7/."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest


class Tee:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, value):
        for stream in self.streams:
            stream.write(value)
            stream.flush()
        return len(value)

    def flush(self):
        for stream in self.streams:
            stream.flush()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite', choices=('hw7', 'hw5', 'focused'), default='hw7')
    args = parser.parse_args(argv)
    evidence = Path(__file__).resolve().parent/'evidence'
    evidence.mkdir(exist_ok=True)
    tmp = evidence/'tmp'
    tmp.mkdir(exist_ok=True)
    tempfile.tempdir = str(tmp)
    os.environ['TMP'] = os.environ['TEMP'] = str(tmp)
    os.environ['MPLCONFIGDIR'] = str(evidence/'mplconfig')
    os.environ['MPLBACKEND'] = 'Agg'
    loader = unittest.TestLoader()
    if args.suite == 'hw5':
        suite = loader.discover('Hw5', pattern='test_*.py', top_level_dir='.')
    elif args.suite == 'focused':
        suite = loader.loadTestsFromNames(['hw7.tests.test_geometry', 'hw7.tests.test_solver'])
    else:
        suite = loader.discover('hw7/tests', pattern='test_*.py', top_level_dir='.')
    original_out, original_err = sys.stdout, sys.stderr
    with (evidence/(args.suite+'_tests.log')).open('w', encoding='utf-8') as log:
        tee = Tee(original_out, log)
        sys.stdout = sys.stderr = tee
        try:
            print('Command:', sys.executable, '-B -m hw7.verify --suite', args.suite)
            print('Python:', sys.version)
            started = time.perf_counter()
            result = unittest.TextTestRunner(stream=tee, verbosity=2).run(suite)
            seconds = time.perf_counter()-started
        finally:
            sys.stdout, sys.stderr = original_out, original_err
    record = dict(python=sys.version, suite=args.suite, tests=result.testsRun,
                  failures=len(result.failures), errors=len(result.errors), skipped=len(result.skipped),
                  seconds=seconds, successful=result.wasSuccessful())
    (evidence/(args.suite+'_tests.json')).write_text(json.dumps(record, indent=2), encoding='utf-8')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
