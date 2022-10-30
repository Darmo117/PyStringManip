import abc
import itertools
import typing as typ

from .. import _core


class _SetOperation(_core.Operation, abc.ABC):
    """Base class for sets operations."""

    def __init__(self, sets_sep: str = '\n', values_sep: str = ','):
        """Create a set operation.

        :param sets_sep: String to use to separate the two sets.
        :param values_sep: Set values separator.
        """
        self._sets_sep = sets_sep
        self._values_sep = values_sep

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'sets_sep': self._sets_sep,
            'values_sep': self._values_sep,
        }

    def apply(self, s: str) -> str:
        sets = s.split(self._sets_sep)
        if (nb := len(sets)) != 2:
            ValueError(f'expected 2 sets, got {nb}')
        set1 = self._to_set(sets[0])
        set2 = self._to_set(sets[1])
        return self._values_sep.join(sorted(self._op(set1, set2)))

    def _to_set(self, s: str) -> set:
        return set(filter(None, s.split(self._values_sep)))

    @abc.abstractmethod
    def _op(self, s1: set, s2: set) -> typ.Iterable[typ.Any]:
        pass


class SetUnion(_SetOperation):
    """Get the union of two sets."""

    def _op(self, s1: set, s2: set) -> typ.Iterable[typ.Any]:
        return s1 | s2


class SetIntersection(_SetOperation):
    """Get the intersection of two sets."""

    def _op(self, s1: set, s2: set) -> typ.Iterable[typ.Any]:
        return s1 & s2


class SetDifference(_SetOperation):
    """Get the difference of two sets."""

    def _op(self, s1: set, s2: set) -> typ.Iterable[typ.Any]:
        return s1 - s2


class SetSymmetricDifference(_SetOperation):
    """Get the symmetric difference of two sets."""

    def _op(self, s1: set, s2: set) -> typ.Iterable[typ.Any]:
        return s1 ^ s2


class CartesianProduct(_SetOperation):
    """Get the cartesian product of two sets."""

    def _op(self, s1: set, s2: set) -> typ.Iterable[typ.Any]:
        return [f'({e1},{e2})' for e1, e2 in itertools.product(s1, s2)]
