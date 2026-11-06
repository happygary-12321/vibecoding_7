"""Persistent spawn workers for read-only collision queries in ONE world."""
from collections import Counter
from multiprocessing.connection import wait
import multiprocessing as mp
import os
from pathlib import Path
import tempfile
import time
import traceback

THREAD_LIMITS = {key: '1' for key in
                 ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS')}
TEMP_ROOT = Path(__file__).resolve().parent/'evidence/parallel_pilot/native_tmp'


def _batch(task):
    """Importable worker kernel; returns points in their original order."""
    from .manifolds import narrow_phase
    index, queries, opts, enrich = task
    return index, tuple(narrow_phase(a, b, old, opts, enrich=enrich) for a, b, old in queries)


def _worker(connection):
    try:
        os.environ.update(THREAD_LIMITS)
        directory = TEMP_ROOT/str(os.getpid())
        directory.mkdir(parents=True, exist_ok=True)
        tempfile.tempdir = str(directory)
        os.environ['TMP'] = os.environ['TEMP'] = str(directory)
        # Import before declaring readiness; startup includes native imports.
        from .manifolds import narrow_phase  # noqa: F401
        connection.send(('ready', os.getpid(), dict(THREAD_LIMITS)))
        while True:
            task = connection.recv()
            if task is None:
                return
            try:
                index, results = _batch(task)
                connection.send(('result', index, results, os.getpid()))
            except BaseException as exc:
                connection.send(('error', type(exc).__name__, str(exc), traceback.format_exc()))
                return
    finally:
        connection.close()


class WorkerError(RuntimeError):
    pass


class ParallelDetector:
    def __init__(self, workers=4, batch_size=4, serial_threshold=0):
        for name, value, minimum in (('workers', workers, 1), ('batch_size', batch_size, 1),
                                     ('serial_threshold', serial_threshold, 0)):
            if type(value) is not int or value < minimum:
                raise ValueError(f'{name} must be an integer >= {minimum}')
        self.workers, self.batch_size, self.serial_threshold = workers, batch_size, serial_threshold
        self.processes, self.connections, self.ready = [], [], []
        self.active = False
        self.startup_seconds = self.shutdown_seconds = 0.
        self.counts, self.worker_pairs = Counter(), Counter()
        self.completion_orders = []

    def __enter__(self):
        if self.active or self.processes:
            raise ValueError('detector contexts are single-use')
        started = time.perf_counter()
        previous = {key: os.environ.get(key) for key in THREAD_LIMITS}
        try:
            os.environ.update(THREAD_LIMITS)
            context = mp.get_context('spawn')
            for _ in range(self.workers):
                parent, child = context.Pipe()
                process = context.Process(target=_worker, args=(child,))
                try:
                    process.start()
                except BaseException:
                    parent.close()
                    child.close()
                    raise
                child.close()
                self.processes.append(process)
                self.connections.append(parent)
            pending = set(self.connections)
            deadline = time.monotonic()+60
            while pending:
                if time.monotonic() > deadline:
                    raise WorkerError('worker startup exceeded 60 seconds')
                for pipe in self._wait(pending):
                    message = pipe.recv()
                    if message[0] != 'ready':
                        raise WorkerError(f'invalid readiness message: {message}')
                    self.ready.append(message)
                    pending.remove(pipe)
            self.active = True
            self.startup_seconds = time.perf_counter()-started
            return self
        except BaseException:
            self.close(abort=True)
            raise
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def _wait(self, connections):
        while True:
            for process in self.processes:
                if process.exitcode is not None:
                    raise WorkerError(f'worker {process.pid} exited with code {process.exitcode}')
            available = wait(list(connections), timeout=.1)
            if available:
                return available

    def map_batches(self, tasks):
        """Dynamic scheduling, ordered reduction; failures invalidate the pool."""
        if not self.active:
            raise ValueError('parallel detector must be active')
        results, order, pending = {}, [], set()
        iterator = iter(tasks)
        try:
            for pipe in self.connections:
                task = next(iterator, None)
                if task is None:
                    break
                pipe.send(task)
                pending.add(pipe)
            while pending:
                for pipe in self._wait(pending):
                    message = pipe.recv()
                    if message[0] == 'error':
                        raise WorkerError('\n'.join(message[1:]))
                    if message[0] != 'result':
                        raise WorkerError(f'invalid result message: {message[0]}')
                    _, index, values, pid = message
                    results[index] = values
                    order.append(index)
                    self.worker_pairs[pid] += len(values)
                    task = next(iterator, None)
                    if task is None:
                        pending.remove(pipe)
                    else:
                        pipe.send(task)
            self.completion_orders.append(order)
            return tuple(value for index in sorted(results) for value in results[index])
        except BaseException as exc:
            self.close(abort=True)
            if isinstance(exc, (OSError, EOFError)):
                raise WorkerError(f'worker transport failed: {exc}') from exc
            raise

    def query(self, bodies, pairs, old, opts, enrich):
        if not self.active:
            raise ValueError('parallel detector must be active')
        self.counts['trial_calls' if enrich else 'diagnostic_calls'] += 1
        self.counts['candidate_pairs'] += len(pairs)
        if len(pairs) <= self.serial_threshold:
            from .manifolds import narrow_phase
            self.counts['serial_pairs'] += len(pairs)
            self.counts['serial_calls'] += 1
            return tuple(narrow_phase(bodies[i], bodies[j], old.get((i, j)), opts, enrich=enrich) for i, j in pairs)
        tasks = []
        for offset in range(0, len(pairs), self.batch_size):
            queries = tuple((bodies[i], bodies[j], old.get((i, j))) for i, j in pairs[offset:offset+self.batch_size])
            tasks.append((len(tasks), queries, opts, enrich))
        self.counts['worker_pairs'] += len(pairs)
        self.counts['batches'] += len(tasks)
        return self.map_batches(tasks)

    def close(self, abort=False):
        started = time.perf_counter()
        try:
            if not abort:
                for pipe in self.connections:
                    try:
                        pipe.send(None)
                    except (OSError, EOFError):
                        abort = True
            for process in self.processes:
                if abort and process.is_alive():
                    process.terminate()
            for process in self.processes:
                process.join(timeout=5)
                if process.is_alive():
                    process.terminate()
                    process.join()
        finally:
            for pipe in self.connections:
                pipe.close()
            self.active = False
            self.shutdown_seconds += time.perf_counter()-started

    def __exit__(self, kind, value, tb):
        if self.active:
            self.close(abort=kind is not None)

    def statistics(self):
        return dict(backend='parallel', workers=self.workers, batch_size=self.batch_size,
                    serial_threshold=self.serial_threshold, startup_seconds=self.startup_seconds,
                    shutdown_seconds=self.shutdown_seconds, ready=self.ready, counts=dict(self.counts),
                    worker_pairs=dict(self.worker_pairs), all_workers_exited=all(p.exitcode is not None for p in self.processes),
                    completion_orders=self.completion_orders)
