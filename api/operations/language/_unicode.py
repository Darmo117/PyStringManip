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
