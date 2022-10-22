import typing as typ

import unidecode

from .. import _core


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


class EscapeUnicodeChars(_core.Operation):
    """Escape all or some Unicode characters."""

    def __init__(self, mode: str = r'utf16be', encode_all_chars: bool = False, uppercase_hex: bool = False):
        """Create a Unicode escape operation.

        :param mode: The prefix to prepend to the codepoints.
        :param encode_all_chars: Whether to escape all characters instead of only those with a codepoint > 127.
        :param uppercase_hex: Whether to print hex codepoints as upper case.
        """
        self._functions = {
            'utf16be': self._escape_to_utf16be,
            'python': self._escape_to_python,
        }
        if mode not in self._functions:
            raise ValueError(f'invalid mode: {mode}')
        self._mode = mode
        self._encode_all_chars = encode_all_chars
        self._uppercase_hex = uppercase_hex

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'mode': self._mode,
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
