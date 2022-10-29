import typing as typ

from .. import _core


class Vigenere(_core.Operation):
    """Encode/decode a text using Vigenère cypher."""

    _ENCODE = 'encode'

    def __init__(self, key: str = '', mode: str = _ENCODE):
        """Create a Vigenère cypher operation.

        :param key: The encryption/decrytion key.
        :param mode: Either 'encode' or 'decode'.
        """
        if mode not in (self._ENCODE, 'decode'):
            raise ValueError(f'invalid mode {mode!r}')
        self._key = key
        self._mode = mode

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'key': self._key,
            'mode': self._mode,
        }

    def apply(self, s: str) -> str:
        key_length = len(self._key)
        res = ''
        i = 0
        for c in s:
            if 'A' <= (char := c.upper()) <= 'Z':
                key_char = self._key[i]
                cc = self._table(char, key_char.upper())
                res += cc if c.isupper() else cc.lower()
                i = (i + 1) % key_length
            else:
                res += c
        return res

    def _table(self, c: str, key_char: str) -> str:
        # 65 = ord('A')
        if self._mode == self._ENCODE:
            return chr(((ord(c) + ord(key_char)) - 2 * 65) % 26 + 65)
        else:
            return chr((ord(c) - ord(key_char)) % 26 + 65)
