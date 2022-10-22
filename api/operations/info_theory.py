import collections
import math
import re
import typing as typ

from . import _core


class Entropy(_core.Operation):
    """Calculate the Shannon entropy of a text."""

    def apply(self, s: str) -> str:
        # https://en.wikipedia.org/wiki/Entropy_(information_theory)
        frequencies = (i / len(s) for i in collections.Counter(s).values())
        return str(-sum(f * math.log(f, 2) for f in frequencies))


class FrequencyDist(_core.Operation):
    """Compute the frequency of each byte of a string."""

    def __init__(self, encoding: str = 'utf8', show_ascii: bool = False, show_zeros: bool = False):
        """Create a byte frequency counter.

        :param encoding: Which encoding to use do decode the string.
        :param show_ascii: Whether to show the ASCII characters instead of bytes.
        :param show_zeros: Whether to add bytes with a frequency of 0.
        """
        self._encoding = encoding
        self._show_ascii = show_ascii
        self._show_zeros = show_zeros

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'encoding': self._encoding,
            'show_ascii': self._show_ascii,
            'show_zeros': self._show_zeros,
        }

    def apply(self, s: str) -> str:
        counts = collections.Counter(bytes(s, self._encoding))
        if self._show_zeros:
            for i in range(255):
                if i not in counts:
                    counts[i] = 0
        if self._show_ascii:
            counts = {chr(b): c for b, c in counts.items()}
        frequencies = sorted(counts.items(), key=lambda e: e[0])
        return ','.join(f'{b}:{c}' for b, c in frequencies)


class CoincidenceIndex(_core.Operation):
    """Compute the index of coincidence of a string. Only takes into account the 26 letters of the latin alphabet.
    IC for monocase English text is around 1.73.
    """

    def apply(self, s: str) -> str:
        s = re.sub(r'[^a-z]', '', s.lower())
        n = len(s)
        if n <= 1:
            return '0'
        counts = collections.Counter(s)
        c = len(counts)
        # https://en.wikipedia.org/wiki/Index_of_coincidence
        return sum(ni * (ni - 1) for ni in counts.values()) / (n * (n - 1) / c)
