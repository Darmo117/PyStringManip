from __future__ import annotations

import threading
import typing as typ

from . import operations as ops


class Pipeline:
    """Pipelines represent a sequence of operations to perform on a string.
    Each operation takes in the string returned by the operation preceding it.
    """

    def __init__(self, verbose: bool = False):
        """Creates a pipeline.

        :param verbose: If true, each intermediate result will be displayed.
        """
        self._verbose = verbose
        self._operations: typ.List[ops.Operation | Pipeline] = []

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
        parallel_pipeline = ParallelPipeline(self, delimiter, verbose=self._verbose)
        self._operations.append(parallel_pipeline)
        return parallel_pipeline

    def execute(self, s: str) -> str:
        """Executes this pipeline on the given string.
        If this pipeline is empty, the passed string is returned as is.

        :param s: The string to execute this pipeline on.
        :return: The transformed string.
        """
        if not self._operations:
            if self._verbose:
                print('warning: pipeline is empty')
            return s

        buffer = s
        for op in self._operations:
            if self._verbose:
                op_name = f'fork[delimiter={op.delimiter!r}]' if isinstance(op, ParallelPipeline) else op
                print(buffer, end=f'\n-> {op_name}\n')
            if isinstance(op, Pipeline):
                buffer = op.execute(buffer)
            else:
                buffer = op.apply(buffer)
        return buffer


class ParallelPipeline(Pipeline):
    """Parallel pipelines split the input string using a delimiter then passes each substring to a sub-thread.
    The sub-results must be merged by calling the `merge(str)` method.
    """

    def __init__(self, parent: Pipeline, delimiter: str, verbose: bool = False):
        """Creates a parallel pipeline.

        :param parent: This pipeline’s parent.
        :param delimiter: The delimiter to use to split the input string.
        :param verbose: If true, each intermediate result will be displayed.
        """
        super().__init__(verbose=verbose)
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
            p = Pipeline(verbose=self._verbose)
            p._operations = self._operations
            threads = [_ThreadWithReturnValue(target=p.execute, arg=substring) for substring in substrings]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            if self._verbose:
                print(f'-> merge[joiner={self._joiner!r}]')
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
