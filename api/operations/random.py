import os
import typing as typ
import uuid

from lorem_text import lorem

from . import _core


class Rng(_core.Operation):
    """Generate a cryptographically secure pseudo-random integer of the given byte size."""

    # noinspection PyShadowingBuiltins
    def __init__(self, bytes: int = 32):
        """Create a RNG operation.

        :param bytes: The number of bytes.
        """
        if not (1 <= bytes <= 1e5):
            raise ValueError('number of bytes must be in [1, 1e5]')
        self._bytes = bytes

    def get_params(self) -> dict[str, typ.Any]:
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
    """Generate lorem ipsum text."""

    def __init__(self, size: int = 5, unit: str = 'p'):
        """Create a lorem ipsum generator.

        :param size: The number of worlds, sentences or paragraphs, depending on the `unit` parameter.
        :param unit: The type of lorem to generate, either 'w' (words), 's' (sentences) or 'p' (paragraphs).
        """
        self._size = size
        self._functions = {
            'w': lorem.words,
            's': lambda nb: ' '.join(lorem.sentence() for _ in range(nb)),
            'p': lorem.paragraphs,
        }
        if unit not in self._functions:
            raise ValueError(f'invalid unit: {unit}')
        self._unit = unit

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'size': self._size,
            'unit': self._unit,
        }

    def apply(self, s: str) -> str:
        return self._functions[self._unit](self._size)
