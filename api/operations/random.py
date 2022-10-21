import os
import typing as typ
import uuid

from . import _core


class Rng(_core.Operation):
    """Generate a cryptographically secure pseudo-random integer of the given byte size."""

    # noinspection PyShadowingBuiltins
    def __init__(self, bytes: int = 32):
        """Create a RNG operation.

        :param bytes: The number of bytes.
        """
        if not (1 <= bytes <= 100_000):
            raise ValueError('number of bytes must be in [1, 1e5]')
        self._bytes = bytes

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'bytes': self._bytes,
        }

    def apply(self, s: str) -> str:
        return str(int.from_bytes(os.urandom(self._bytes), "big"))


class XkcdRng(_core.Operation):
    """Generate a pseudo-random integer based on XKCD’s rule."""

    def apply(self, s: str) -> str:
        return '4'


class RandomUuid(_core.Operation):
    """Generate a random version 4 UUID."""

    def apply(self, s: str) -> str:
        return str(uuid.uuid4())


class Lipsum(_core.Operation):
    def __init__(self, size: int = 5, unit: str = '§'):
        self._size = size
        self._unit = unit

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'size': self._size,
            'unit': self._unit,
        }

    def apply(self, s: str) -> str:
        pass  # TODO
