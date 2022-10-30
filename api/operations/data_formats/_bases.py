import abc
import base64
import typing as typ

from .. import _core


class _Base64Operation(_core.Operation, abc.ABC):
    """Base class for all base64 operations."""

    def __init__(self, encoding: str = 'utf8', altchars: str = '+/'):
        self._encoding = encoding
        if (size := len(altchars)) != 2:
            raise ValueError(f'altchars must be of length 2, got {size}')
        self._altchars = bytes(altchars, 'utf8')

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'encoding': self._encoding,
            'altchars': self._altchars.decode('utf8'),
        }


class ToBase64(_Base64Operation):
    """Convert a string’s bytes to base64 from the given encoding."""

    def __init__(self, encoding: str = 'utf8', altchars: str = '+/', remove_pad: bool = False):
        super().__init__(encoding=encoding, altchars=altchars)
        self._remove_pad = remove_pad

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            **super().get_params(),
            'remove_pad': self._remove_pad,
        }

    def apply(self, s: str) -> str:
        data = base64.b64encode(bytes(s, self._encoding), altchars=self._altchars).decode('utf8')
        if self._remove_pad:
            data = data.replace('=', '')
        return data


class FromBase64(_Base64Operation):
    """Convert a string interpreted as base64 to a string in the given encoding."""

    def __init__(self, encoding: str = 'utf8', altchars: str = '+/', add_pad: bool = False):
        super().__init__(encoding=encoding, altchars=altchars)
        self._add_pad = add_pad

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            **super().get_params(),
            'add_pad': self._add_pad,
        }

    def apply(self, s: str) -> str:
        if self._add_pad and (nb := len(s) % 4):
            s += '=' * nb
        return base64.b64decode(bytes(s, 'ascii'), altchars=self._altchars).decode(self._encoding)
