from __future__ import annotations

import sys
import threading
import typing as typ

from . import operations as ops


class Logger:
    NONE = 0
    OPERATIONS = 1
    INTERMEDIARY_RESULTS = 2
    DEBUG = 3

    def __init__(self, name: str, level: int = NONE):
        self._name = name
        self._level = level

    def warning(self, o):
        self._print(o, prefix='[WARN]', out=sys.stderr)

    def print_operation(self, s: str):
        if self._level >= self.OPERATIONS:
            self._print(f'-> {s}')

    def print_intermediary_result(self, s: str):
        if self._level >= self.INTERMEDIARY_RESULTS:
            self._print('input:\n' + s)

    def debug(self, o):
        if self._level >= self.DEBUG:
            self._print(o, prefix='[DEBUG]')

    def _print(self, o, prefix: str = '', out=sys.stdout):
        print(f'[{self._name}]' + prefix, o, file=out)


class Pipeline:
    """Pipelines represent a sequence of operations to perform on a string.
    Each operation takes in the string returned by the operation preceding it.
    """

    def __init__(self, name: str = 'main', verbosity: int = Logger.NONE):
        """Creates a pipeline.

        :param name: Name of this pipeline.
        :param verbosity: The verbosity level.
        """
        self._name = name
        self._verbosity = verbosity
        self._operations: typ.List[ops.Operation | Pipeline] = []
        self._logger = Logger(name, verbosity)

    @property
    def name(self) -> str:
        return self._name

    def then(self, op: ops.Operation) -> Pipeline:
        """Appends an operation to this pipeline.

        :param op: The operation to append.
        :return: This pipeline.
        """
        self._operations.append(op)
        return self

    def fork(self, delimiter: str = '\n') -> ParallelPipeline:
        """Splits the input string using the given delimiter then treats each resulting substring in a separate thread.

        :param delimiter: The string to split on.
        :return: A parallel pipeline.
        """
        parallel_pipeline = ParallelPipeline(self, delimiter, verbosity=self._verbosity)
        self._operations.append(parallel_pipeline)
        return parallel_pipeline

    def execute(self, s: str) -> str:
        """Executes this pipeline on the given string.
        If this pipeline is empty, the passed string is returned as is.

        :param s: The string to execute this pipeline on.
        :return: The transformed string.
        """
        if not self._operations:
            self._logger.warning('pipeline is empty')
            return s

        buffer = s
        for op in self._operations:
            self._logger.print_intermediary_result(buffer)
            self._logger.print_operation(
                f'fork[delimiter={op.delimiter!r}]' if isinstance(op, ParallelPipeline) else op)
            if isinstance(op, Pipeline):
                buffer = op.execute(buffer)
            else:
                buffer = op.apply(buffer)
        return buffer


class ParallelPipeline(Pipeline):
    """Parallel pipelines split the input string using a delimiter then passes each substring to a sub-thread.
    The sub-results must be merged by calling the `merge(str)` method.
    """

    def __init__(self, parent: Pipeline, delimiter: str, verbosity: int = 0):
        """Creates a parallel pipeline.

        :param parent: This pipeline’s parent.
        :param delimiter: The delimiter to use to split the input string.
        :param verbosity: The verbosity level.
        """
        super().__init__(name=parent.name, verbosity=verbosity)
        self._parent = parent
        self._delimiter = delimiter
        self._joiner = None

    @property
    def delimiter(self) -> str:
        return self._delimiter

    @property
    def joiner(self) -> str | None:
        return self._joiner

    def merge(self, joiner: str = '\n') -> Pipeline:
        """Merges the results of all parallel pipelines that were previously forked.
        Results are guaranted to be merged in the same order as the original substrings were before they were forked.

        :param joiner: The string to use to join each result.
        :return: The results of all sub-pipelines joined with the given string.
        """
        if self._joiner is not None:
            raise RuntimeError('pipeline has already been merged')
        if not isinstance(joiner, str):
            raise ValueError('joiner must be a string')
        self._joiner = joiner
        return self._parent

    def execute(self, s: str) -> str:
        if self._joiner is None:
            raise RuntimeError('forked pipeline has not been merged')

        if self._delimiter in s:
            substrings = filter(None, s.split(self._delimiter))
            threads = []
            for i, substring in enumerate(substrings):
                p = Pipeline(name=f'{self.name}.{i + 1}', verbosity=self._verbosity)
                p._operations = self._operations
                threads.append(_ThreadWithReturnValue(target=p.execute, arg=substring))
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self._logger.print_operation(f'merge[joiner={self._joiner!r}]')
            return self._joiner.join(thread.result for thread in threads)
        else:
            return super().execute(s)


class _ThreadWithReturnValue(threading.Thread):
    """Adds a way to get the result of a thread’s target."""

    def __init__(self, target: typ.Callable[[str], str], arg: str):
        super().__init__(target=target, args=(arg,))
        self._result = None

    @property
    def result(self) -> str:
        return self._result

    def run(self):
        # noinspection PyUnresolvedReferences
        self._result = self._target(*self._args)
