import abc
import math
import typing as typ

from .. import _core


class _BytewiseOperation(_core.Operation, abc.ABC):
    """Base class for all bytewise numeric transformations."""

    def __init__(self, encoding: str, delimiter: str):
        """Create a bytewise operation.

        :param encoding: Encoding of the output string.
        :param delimiter: String to split the input string on.
        """
        self._encoding = encoding
        self._delimiter = delimiter

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'encoding': self._encoding,
            'delimiter': self._delimiter,
        }


class _BytesToBase(_BytewiseOperation):
    """Base class for all operations that convert a string’s bytes to a list of base-n numbers."""

    _DIGITS = '0123456789abcdefghijklmnopqrstuvwxyz'

    def __init__(self, encoding: str = 'utf8', uppercase: bool = False, joiner: str = ' ', bpl: int = 0,
                 pad: bool = False, base: int = 10, expose_base: bool = False):
        """Create a to_base operation.

        :param encoding: Encoding of the input string.
        :param joiner: String to use to join each byte representation.
        :param bpl: Number of bytes to display per line.
         A value of 0 or less means that all bytes will be on the same line.
        :param pad: Whether to pad each byte with 0s.
        :param base: The base to represent each byte in.
        :param expose_base: Whether the `base` parameter should be visible from the get_params() method.
        """
        super().__init__(encoding=encoding, delimiter=joiner)
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
            buffer[-1].append(self._format(b))
        return '\n'.join(self._delimiter.join(line) for line in buffer)

    def _format(self, n: int) -> str:
        flag = {2: 'bb', 8: 'oo', 16: 'xX'}.get(self._base)
        padding_length = math.ceil(math.log(256) / math.log(self._base)) if self._pad else 0
        if flag:
            return format(n, f'0{padding_length}{flag[self._uppercase]}')
        else:
            res = ''
            while n >= self._base:
                res = self._DIGITS[n % self._base] + res
                n //= self._base
            res = (self._DIGITS[n % self._base] + res).rjust(padding_length, '0')
            return res.upper() if self._base > 10 and self._uppercase else res


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

    def __init__(self, encoding: str = 'utf8', delimiter: str = ' ', base: int = 10, expose_base: bool = False):
        """Create a from_base operation.

        :param encoding: Encoding of the output string.
        :param delimiter: String to use to split each byte representation.
        :param base: The base to convert each bytes from.
        :param expose_base: Whether the `base` parameter should be visible from the get_params() method.
        """
        super().__init__(encoding=encoding, delimiter=delimiter)
        self._base = base
        self._expose_base = expose_base

    def get_params(self) -> typ.Dict[str, typ.Any]:
        params = super().get_params()
        if self._expose_base:
            params['base'] = self._base
        return params

    def apply(self, s: str) -> str:
        if self._delimiter != '\n':
            s = s.replace('\n', self._delimiter)
        return bytes(int(h, self._base) for h in filter(None, s.split(self._delimiter))).decode(self._encoding)


class FromBaseNBytes(_FromBytes):
    """Convert a string interpreted as a list of base-n bytes to a string with the given encoding."""

    def __init__(self, encoding: str = 'utf8', delimiter: str = ' ', base: int = 10):
        """Create a from_base_n operation.

        :param encoding: Encoding of the output string.
        :param delimiter: String to use to split each byte representation.
        :param base: The base to convert each bytes from.
        """
        super().__init__(encoding=encoding, delimiter=delimiter, base=base, expose_base=True)


class FromHexBytes(_FromBytes):
    """Convert a string interpreted as a list of hexadecimal bytes to a string with the given encoding."""

    def __init__(self, encoding: str = 'utf8', delimiter: str = ' '):
        """Create a from_hex operation.

        :param encoding: Encoding of the output string.
        :param delimiter: String to use to split each byte representation.
        """
        super().__init__(encoding=encoding, delimiter=delimiter, base=16)


class FromOctalBytes(_FromBytes):
    """Convert a string interpreted as a list of octal bytes to a string with the given encoding."""

    def __init__(self, encoding: str = 'utf8', delimiter: str = ' '):
        """Create a from_octal operation.

        :param encoding: Encoding of the output string.
        :param delimiter: String to use to split each byte representation.
        """
        super().__init__(encoding=encoding, delimiter=delimiter, base=8)


class FromBinaryBytes(_FromBytes):
    """Convert a string interpreted as a list of binary bytes to a string with the given encoding."""

    def __init__(self, encoding: str = 'utf8', delimiter: str = ' '):
        """Create a from_binary operation.

        :param encoding: Encoding of the output string.
        :param delimiter: String to use to split each byte representation.
        """
        super().__init__(encoding=encoding, delimiter=delimiter, base=2)
