import abc
import base64
import typing as typ

from .. import _core


class _Base64Operation(_core.Operation, abc.ABC):
    """Base class for all base64 operations."""

    def __init__(self, encoding: str = 'utf8'):
        self._encoding = encoding

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'encoding': self._encoding,
        }


class ToBase64(_Base64Operation):
    """Convert a string’s bytes to base64 from the given encoding."""

    def apply(self, s: str) -> str:
        return base64.b64encode(bytes(s, self._encoding)).decode('utf8')


class FromBase64(_Base64Operation):
    """Convert a string interpreted as base64 to a string in the given encoding."""

    def apply(self, s: str) -> str:
        return base64.b64decode(bytes(s, 'ascii')).decode(self._encoding)
