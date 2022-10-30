import abc
import base64
import typing as typ

from .. import _core


class _BaseOperation(_core.Operation, abc.ABC):
    """Base class for all baseXX operations."""

    def __init__(self, encoding: str = 'utf8'):
        """Create a baseXX operation.

        :param encoding: Text encoding.
        """
        self._encoding = encoding

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'encoding': self._encoding,
        }


class ToBase32(_BaseOperation):
    """Convert a string’s bytes to base32 from the given encoding."""

    def __init__(self, encoding: str = 'utf8'):
        """Create a to_base32 operation.

        :param encoding: Input text’s encoding.
        """
        super().__init__(encoding=encoding)

    def apply(self, s: str) -> str:
        return base64.b32encode(bytes(s, self._encoding)).decode('ascii')


class FromBase32(_BaseOperation):
    """Convert a string interpreted as base32 into a string in the given encoding."""

    def __init__(self, encoding: str = 'utf8'):
        """Create a from_base32 operation.

        :param encoding: Output text’s encoding.
        """
        super().__init__(encoding=encoding)

    def apply(self, s: str) -> str:
        return base64.b32decode(bytes(s, 'ascii')).decode(self._encoding)


class _Base64Operation(_BaseOperation, abc.ABC):
    """Base class for all base64 operations."""

    def __init__(self, encoding: str = 'utf8', altchars: str = '+/'):
        """Create a base64 operation.

        :param encoding: Input/output text’s encoding.
        :param altchars: Characters to use instead of '+' and '/'.
        """
        super().__init__(encoding=encoding)
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
        """Create a to_base64 operation.

        :param encoding: Input text’s encoding.
        :param altchars: Characters to use instead of '+' and '/'.
        :param remove_pad: Whether to remove the padding character '=' from the output.
        """
        super().__init__(encoding=encoding, altchars=altchars)
        self._remove_pad = remove_pad

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            **super().get_params(),
            'remove_pad': self._remove_pad,
        }

    def apply(self, s: str) -> str:
        data = base64.b64encode(bytes(s, self._encoding), altchars=self._altchars).decode('ascii')
        if self._remove_pad:
            data = data.replace('=', '')
        return data


class FromBase64(_Base64Operation):
    """Convert a string interpreted as base64 into a string in the given encoding."""

    def __init__(self, encoding: str = 'utf8', altchars: str = '+/', add_pad: bool = False):
        """Create a from_base64 operation.

        :param encoding: Output text’s encoding.
        :param altchars: Characters to use instead of '+' and '/'.
        :param add_pad: Whether to add missing padding characters '='.
        """
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


class ToBase85(_BaseOperation):
    """Convert a string’s bytes to base85 from the given encoding."""

    def __init__(self, encoding: str = 'utf8', pad: bool = False):
        """Create a to_base85 operation.

        :param encoding: Input text’s encoding.
        :param pad: Whether to pad the input string with null bytes before encoding.
        """
        super().__init__(encoding=encoding)
        self._pad = pad

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            **super().get_params(),
            'pad': self._pad,
        }

    def apply(self, s: str) -> str:
        return base64.b85encode(bytes(s, self._encoding), pad=self._pad).decode('ascii')


class FromBase85(_BaseOperation):
    """Convert a string interpreted as base85 into a string in the given encoding."""

    def __init__(self, encoding: str = 'utf8'):
        """Create a from_base85 operation.

        :param encoding: Output text’s encoding.
        """
        super().__init__(encoding=encoding)

    def apply(self, s: str) -> str:
        return base64.b85decode(bytes(s, 'ascii')).decode(self._encoding)
