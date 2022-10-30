import abc
import re
import typing as typ
import unicodedata

import unidecode

from .. import _core
from ... import utils


class _CharCode(_core.Operation, abc.ABC):
    """Base class for charcode operations."""

    def __init__(self, base: int = 16, delim: str = ' '):
        self._delim = delim
        self._base = base

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'base': self._base,
        }


class ToCharcode(_CharCode):
    """Convert each character to their Unicode codepoint."""

    def __init__(self, base: int = 16, joiner: str = ' ', uppercase: bool = False, pad: int = 4):
        """Create a to_charcode operation.

        :param base: The base to represent codepoints in.
        :param joiner: The string to use to join codepoints with.
        :param uppercase: Whether to put non-numeric digits in the resulting string to uppercase or not.
        :param pad: The number of 0s to pad codepoints with.
        """
        super().__init__(base=base, delim=joiner)
        self._pad = pad
        self._uppercase = uppercase

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            **super().get_params(),
            'joiner': self._delim,
            'uppercase': self._uppercase,
            'pad': self._pad,
        }

    def apply(self, s: str) -> str:
        return self._delim.join(
            utils.format_int(ord(c), self._base, uppercase=self._uppercase, pad=self._pad) for c in s)


class FromCharcode(_CharCode):
    """Convert a list of Unicode codepoints into a text."""

    def __init__(self, base: int = 16, sep: str = ' '):
        """Create a from_charcode operation.

        :param base: The base codepoints are represented in.
        :param sep: The string to use to split codepoints.
        """
        super().__init__(base=base, delim=sep)

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            **super().get_params(),
            'sep': self._delim,
        }

    def apply(self, s: str) -> str:
        return ''.join(chr(int(c, self._base)) for c in s.split(self._delim))


class UnicodeFormat(_core.Operation):
    """Adds some formatting to a string."""

    def __init__(self, u: bool = False, s: bool = False):
        """Formats a string.

        :param u: Whether to underline the text.
        :param s: Whether to strikethrough the text.
        """
        self._under = u
        self._strike = s

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'u': self._under,
            's': self._strike,
        }

    def apply(self, s: str) -> str:
        return ''.join(c + ('\u0336' if self._strike else '') + ('\u0332' if self._under else '') for c in s)


class RemoveDiacritics(_core.Operation):
    """Removes all diacritics from a string."""

    def apply(self, s: str) -> str:
        return unidecode.unidecode(s)


class _UnicodeChars(_core.Operation, abc.ABC):
    """Base class for Unicode escaping operations."""
    _UTF16BE = 'utf16be'
    _PYTHON = 'python'

    def __init__(self, mode: str = _UTF16BE):
        """Create a Unicode escape operation.

        :param mode: The prefix to prepend to the codepoints.
        """
        if mode not in (self._UTF16BE, self._PYTHON):
            raise ValueError(f'invalid mode: {mode}')
        self._mode = mode

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'mode': self._mode,
        }


class EscapeUnicodeChars(_UnicodeChars):
    """Escape all or some Unicode characters."""

    def __init__(self, mode: str = _UnicodeChars._UTF16BE, encode_all_chars: bool = False, uppercase_hex: bool = False):
        """Create a Unicode escape operation.

        :param mode: The prefix to prepend to the codepoints.
        :param encode_all_chars: Whether to escape all characters instead of only those with a codepoint > 127.
        :param uppercase_hex: Whether to print hex codepoints as upper case.
        """
        super().__init__(mode)
        self._functions = {
            self._UTF16BE: self._escape_to_utf16be,
            self._PYTHON: self._escape_to_python,
        }
        self._encode_all_chars = encode_all_chars
        self._uppercase_hex = uppercase_hex

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            **super().get_params(),
            'encode_all_chars': self._encode_all_chars,
            'uppercase_hex': self._uppercase_hex,
        }

    def apply(self, s: str) -> str:
        return ''.join(self._functions[self._mode](c)
                       if ord(c) > 127 or self._encode_all_chars else c
                       for c in s)

    def _escape_to_python(self, c: str) -> str:
        flag = 'X' if self._uppercase_hex else 'x'
        codepoint = ord(c)
        if codepoint > 0xffff:
            return r'\U' + format(codepoint, '08' + flag)
        else:
            return r'\u' + format(codepoint, '04' + flag)

    def _escape_to_utf16be(self, c: str) -> str:
        b = bytes(c, 'utf-16be')
        return ''.join(
            r'\u' + format(int.from_bytes(b[i:i + 2], 'big'), '04' + ('X' if self._uppercase_hex else 'x'))
            for i in range(0, len(b), 2)
        )


class UnescapeUnicodeChars(_UnicodeChars):
    """Unescape all escaped Unicode characters."""

    _UTF16BE_REGEX = re.compile(r'((?:\\u[0-9a-fA-F]{4})+)')
    _PYTHON_REGEX = re.compile(r'\\(?:u([0-9a-fA-F]{4})|U([0-9a-fA-F]{8}))')

    def apply(self, s: str) -> str:
        match self._mode:
            case self._PYTHON:
                return self._unescape_as_python(s)
            case self._UTF16BE:
                return self._unescape_from_utf16be(s)

    def _unescape_as_python(self, s: str) -> str:
        def aux(m: typ.Match[str]) -> str:
            match = m.group(1) or m.group(2)
            c = chr(int(match, 16))
            try:
                # Check if code is valid UTF-8: will raise a UnicodeEncodeError if not
                bytes(c, 'utf8')
            except UnicodeEncodeError:
                # Escape code is not valid UTF-8, return the initial sequence
                return m.group()[:2] + match
            else:
                return c

        return self._PYTHON_REGEX.sub(aux, s)

    def _unescape_from_utf16be(self, s: str) -> str:
        def aux(m: typ.Match[str]) -> str:
            bytes_ = b''
            for code in m.group(1).split(r'\u')[1:]:
                bytes_ += int(code, 16).to_bytes(2, 'big')
            try:
                return bytes_.decode(encoding='utf-16be')
            except UnicodeDecodeError:
                return m.group()

        return self._UTF16BE_REGEX.sub(aux, s)


class NormalizeUnicode(_core.Operation):
    """Normalize a Unicode string."""

    def __init__(self, norm: str = 'NFC'):
        """Create a Unicode normalizer.

        :param norm: The norm of the resulting string, either NFC, NFKC, NFD or NFKD.
        """
        if norm not in ('NFC', 'NFKC', 'NFD', 'NFKD'):
            raise ValueError(f'invalid Unicode norm: {norm}')
        self._norm = norm

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'norm': self._norm,
        }

    def apply(self, s: str) -> str:
        return unicodedata.normalize(self._norm, s)
