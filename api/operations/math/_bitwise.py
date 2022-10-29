import abc
import typing as typ

from .. import _core


class _BitwiseOperation(_core.Operation):
    """Base class for 2-operand bitwise operations."""

    def __init__(self, n: int = 0):
        """Create a 2-operand bitwise operation.

        :param n: Integer to perform the opertion with.
        """
        self._n = n

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'n': self._n,
        }

    def apply(self, s: str) -> str:
        return str(self._op(int(s)))

    @abc.abstractmethod
    def _op(self, i: int) -> int:
        pass


class Xor(_BitwiseOperation):
    """Perform a bitwise XOR operation."""

    def _op(self, i: int) -> int:
        return i ^ self._n


class Or(_BitwiseOperation):
    """Perform a bitwise OR operation."""

    def _op(self, i: int) -> int:
        return i | self._n


class And(_BitwiseOperation):
    """Perform a bitwise AND operation."""

    def _op(self, i: int) -> int:
        return i & self._n


class Not(_core.Operation):
    """Perform a bitwise NOT operation."""

    def apply(self, s: str) -> str:
        return str(~int(s))


class LeftBitShift(_BitwiseOperation):
    """Shift an integer’s bits by the specified amount to the left."""

    def _op(self, i: int) -> int:
        return i << self._n


class RightBitShift(_BitwiseOperation):
    """Shift an integer’s bits by the specified amount to the right, sign is preserved."""

    def _op(self, i: int) -> int:
        return i >> self._n
