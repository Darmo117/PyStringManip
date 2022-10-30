import abc
import typing as typ

from .. import _core
from ... import utils


class _BytewiseOperation(_core.Operation, abc.ABC):
    """Base class for all bytewise numeric transformations."""

    def __init__(self, encoding: str, sep: str):
        """Create a bytewise operation.

        :param encoding: Encoding of the output string.
        :param sep: String to split the input string on.
        """
        self._encoding = encoding
        self._sep = utils.unescape(sep)

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'encoding': self._encoding,
            'sep': self._sep,
        }


class _BytesToBase(_BytewiseOperation):
    """Base class for all operations that convert a string’s bytes to a list of base-n numbers."""

    def __init__(self, encoding: str = 'utf8', uppercase: bool = False, joiner: str = ' ', bpl: int = 0,
                 pad: bool = False, base: int = 10, expose_base: bool = False):
        """Create a to_base operation.

        :param encoding: Encoding of the input string.
        :param uppercase: Whether to put non-numeric digits in the resulting string to uppercase or not.
        :param joiner: String to use to join each byte representation.
        :param bpl: Number of bytes to display per line.
         A value of 0 or less means that all bytes will be on the same line.
        :param pad: Whether to pad each byte with 0s.
        :param base: The base to represent each byte in.
        :param expose_base: Whether the `base` parameter should be visible from the get_params() method.
        """
        super().__init__(encoding=encoding, sep=joiner)
        if not (2 <= base <= 36):
            raise ValueError('base must be in [2, 36]')
        self._uppercase = uppercase
        self._bytes_per_line = bpl
        self._pad = pad
        self._base = base
        self._expose_base = expose_base

    def get_params(self) -> typ.Dict[str, typ.Any]:
        params = {
            **super().get_params(),
            'pad': self._pad,
            'uppercase': self._uppercase,
            'bpl': self._bytes_per_line,
        }
        if self._expose_base:
            params['base'] = self._base
        return params

    def apply(self, s: str) -> str:
        buffer = [[]]
        for b in bytearray(s, self._encoding):
            # noinspection PyChainedComparisons
            if self._bytes_per_line > 0 and len(buffer[-1]) == self._bytes_per_line:
                buffer.append([])
            buffer[-1].append(utils.format_int(b, self._base, uppercase=self._uppercase, pad=-self._pad))
        return '\n'.join(self._sep.join(line) for line in buffer)


class BytesToBaseN(_BytesToBase):
    """Convert a string’s bytes to their base-n representation using the specified delimiter."""

    def __init__(self, encoding: str = 'utf8', base: int = 10, pad: bool = True, uppercase: bool = False,
                 joiner: str = ' ', bpl: int = 0):
        """Create a to_base_n operation.

        :param encoding: Encoding of the input string.
        :param base: The base to represent each byte in.
        :param pad: Whether to pad each byte with 0s.
        :param uppercase: Whether to put non-numeric digits in the resulting string to uppercase or not.
        :param joiner: String to use to join each byte representation.
        :param bpl: Number of bytes to display per line.
         A value of 0 or less means that all bytes will be on the same line.
        """
        super().__init__(encoding=encoding, pad=pad, uppercase=uppercase, joiner=joiner, bpl=bpl, base=base,
                         expose_base=True)


class BytesToHex(_BytesToBase):
    """Convert a string’s bytes to their hexadecimal representation using the specified delimiter."""

    def __init__(self, encoding: str = 'utf8', pad: bool = True, uppercase: bool = False, joiner: str = ' ',
                 bpl: int = 0):
        """Create a to_hex operation.

        :param encoding: Encoding of the input string.
        :param pad: Whether to pad each byte with 0s.
        :param uppercase: Whether to put non-numeric digits in the resulting string to uppercase or not.
        :param joiner: String to use to join each byte representation.
        :param bpl: Number of bytes to display per line.
         A value of 0 or less means that all bytes will be on the same line.
        """
        super().__init__(encoding=encoding, pad=pad, uppercase=uppercase, joiner=joiner, bpl=bpl, base=16)


class BytesToOctal(_BytesToBase):
    """Convert a string’s bytes to their octal representation using the specified delimiter."""

    def __init__(self, encoding: str = 'utf8', pad: bool = True, uppercase: bool = False, joiner: str = ' ',
                 bpl: int = 0):
        """Create a to_octal operation.

        :param encoding: Encoding of the input string.
        :param pad: Whether to pad each byte with 0s.
        :param uppercase: Whether to put non-numeric digits in the resulting string to uppercase or not.
        :param joiner: String to use to join each byte representation.
        :param bpl: Number of bytes to display per line.
         A value of 0 or less means that all bytes will be on the same line.
        """
        super().__init__(encoding=encoding, pad=pad, uppercase=uppercase, joiner=joiner, bpl=bpl, base=8)


class BytesToBinary(_BytesToBase):
    """Convert a string’s bytes to their octal representation using the specified delimiter."""

    def __init__(self, encoding: str = 'utf8', pad: bool = True, uppercase: bool = False, joiner: str = ' ',
                 bpl: int = 0):
        """Create a to_binary operation.

        :param encoding: Encoding of the input string.
        :param pad: Whether to pad each byte with 0s.
        :param uppercase: Whether to put non-numeric digits in the resulting string to uppercase or not.
        :param joiner: String to use to join each byte representation.
        :param bpl: Number of bytes to display per line.
         A value of 0 or less means that all bytes will be on the same line.
        """
        super().__init__(encoding=encoding, pad=pad, uppercase=uppercase, joiner=joiner, bpl=bpl, base=2)


class _FromBytes(_BytewiseOperation):
    """Base class for all operations that convert a list of base-n bytes into a string."""

    def __init__(self, encoding: str = 'utf8', sep: str = ' ', base: int = 10, expose_base: bool = False):
        """Create a from_base operation.

        :param encoding: Encoding of the output string.
        :param sep: String to use to split each byte representation.
        :param base: The base to convert each bytes from.
        :param expose_base: Whether the `base` parameter should be visible from the get_params() method.
        """
        super().__init__(encoding=encoding, sep=sep)
        self._base = base
        self._expose_base = expose_base

    def get_params(self) -> typ.Dict[str, typ.Any]:
        params = super().get_params()
        if self._expose_base:
            params['base'] = self._base
        return params

    def apply(self, s: str) -> str:
        if self._sep != '\n':
            s = s.replace('\n', self._sep)
        return bytes(int(h, self._base) for h in filter(None, s.split(self._sep))).decode(self._encoding)


class FromBaseNBytes(_FromBytes):
    """Convert a string interpreted as a list of base-n bytes to a string with the given encoding."""

    def __init__(self, encoding: str = 'utf8', sep: str = ' ', base: int = 10):
        """Create a from_base_n operation.

        :param encoding: Encoding of the output string.
        :param sep: String to use to split each byte representation.
        :param base: The base to convert each bytes from.
        """
        super().__init__(encoding=encoding, sep=sep, base=base, expose_base=True)


class FromHexBytes(_FromBytes):
    """Convert a string interpreted as a list of hexadecimal bytes to a string with the given encoding."""

    def __init__(self, encoding: str = 'utf8', sep: str = ' '):
        """Create a from_hex operation.

        :param encoding: Encoding of the output string.
        :param sep: String to use to split each byte representation.
        """
        super().__init__(encoding=encoding, sep=sep, base=16)


class FromOctalBytes(_FromBytes):
    """Convert a string interpreted as a list of octal bytes to a string with the given encoding."""

    def __init__(self, encoding: str = 'utf8', sep: str = ' '):
        """Create a from_octal operation.

        :param encoding: Encoding of the output string.
        :param sep: String to use to split each byte representation.
        """
        super().__init__(encoding=encoding, sep=sep, base=8)


class FromBinaryBytes(_FromBytes):
    """Convert a string interpreted as a list of binary bytes to a string with the given encoding."""

    def __init__(self, encoding: str = 'utf8', sep: str = ' '):
        """Create a from_binary operation.

        :param encoding: Encoding of the output string.
        :param sep: String to use to split each byte representation.
        """
        super().__init__(encoding=encoding, sep=sep, base=2)
