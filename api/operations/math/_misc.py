import typing as typ

from .. import _core
from ... import utils


class ToBase(_core.Operation):
    """Convert a decimal integer into the given base."""

    def __init__(self, base: int = 10, uppercase: bool = False):
        """Create a to_base operation.

        :param base: Target base.
        :param uppercase: Whether to put non-numeric digits in the resulting string to uppercase or not.
        """
        self._base = base
        self._uppercase = uppercase

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'base': self._base,
            'uppercase': self._uppercase,
        }

    def apply(self, s: str) -> str:
        return utils.format_int(int(s), self._base, uppercase=self._uppercase, pad=0)


class FromBase(_core.Operation):
    """Convert an integer into decimal from the given base."""

    def __init__(self, base: int = 10):
        """Create a from_base operation.

        :param base: Source base.
        """
        self._base = base

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'base': self._base,
        }

    def apply(self, s: str) -> str:
        return str(int(s, self._base))
