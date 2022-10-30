import abc
import functools
import operator
import typing as typ

import numpy as np

from .. import _core

_Number = int | float


class _Base(_core.Operation, abc.ABC):
    """Base class for number list operations."""

    def __init__(self, sep: str = ','):
        """Create an operation for number lists.

        :param sep: Numbers separator.
        """
        self._sep = sep

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'sep': self._sep,
        }

    def apply(self, s: str) -> str:
        return str(self._op(map(float, s.split(self._sep))))

    @abc.abstractmethod
    def _op(self, numbers: typ.Iterable[_Number]) -> _Number:
        pass


class Sum(_Base):
    """Compute the sum of a list of numbers."""

    def _op(self, numbers: typ.Iterable[_Number]) -> _Number:
        return sum(numbers)


class Subtract(_Base):
    """Compute the difference of a list of numbers."""

    def _op(self, numbers: typ.Iterable[_Number]) -> _Number:
        return functools.reduce(operator.sub, numbers)


class Multiply(_Base):
    """Compute the product of a list of numbers."""

    def _op(self, numbers: typ.Iterable[_Number]) -> _Number:
        return functools.reduce(operator.mul, numbers)


class Divide(_Base):
    """Compute the quotient of a list of numbers."""

    def _op(self, numbers: typ.Iterable[_Number]) -> _Number:
        return functools.reduce(operator.truediv, numbers)


class Mean(_Base):
    """Compute the mean of a list of numbers."""

    def _op(self, numbers: typ.Iterable[_Number]) -> _Number:
        return float(np.mean(numbers))


class Median(_Base):
    """Compute the median of a list of numbers."""

    def _op(self, numbers: typ.Iterable[_Number]) -> _Number:
        return float(np.median(numbers))


class Stdev(_Base):
    """Compute the standard deviation of a list of numbers."""

    def _op(self, numbers: typ.Iterable[_Number]) -> _Number:
        return float(np.std(numbers))
