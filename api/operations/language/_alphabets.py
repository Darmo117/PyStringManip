import abc
import re
import typing as typ

from .. import _core
from ... import utils


class ToNato(_core.Operation):
    """Convert characters to their NATO phonetic alphabet equivalent."""

    _NATO = {
        'a': 'Alfa',
        'b': 'Bravo',
        'c': 'Charlie',
        'd': 'Delta',
        'e': 'Echo',
        'f': 'Foxtrot',
        'g': 'Golf',
        'h': 'Hotel',
        'i': 'India',
        'j': 'Juliett',
        'k': 'Kilo',
        'l': 'Lima',
        'm': 'Mike',
        'n': 'November',
        'o': 'Oscar',
        'p': 'Papa',
        'q': 'Quebec',
        'r': 'Romeo',
        's': 'Sierra',
        't': 'Tango',
        'u': 'Uniform',
        'v': 'Victor',
        'w': 'Whiskey',
        'x': 'X-ray',
        'y': 'Yankee',
        'z': 'Zulu',
        '0': 'Zero',
        '1': 'One',
        '2': 'Two',
        '3': 'Tree',
        '4': 'Fower',
        '5': 'Fife',
        '6': 'Six',
        '7': 'Seven',
        '8': 'Eight',
        '9': 'Niner',
        '.': 'Stop',
    }

    def apply(self, s: str) -> str:
        def aux(i: int, c: str) -> str:
            c_ = self._NATO.get(c.lower(), c)
            if i < len(s) - 1 and c_ != c:
                c_ += ' '
            return c_

        return ''.join(aux(i, c) for i, c in enumerate(s))


class _MorseCode(_core.Operation, abc.ABC):
    """Base class for Morse-related operations."""

    _UNICODE_TO_MORSE = {
        'a': '.-',
        'b': '-...',
        'c': '-.-.',
        'd': '-..',
        'e': '.',
        'f': '..-.',
        'g': '--.',
        'h': '....',
        'i': '..',
        'j': '.---',
        'k': '-.-',
        'l': '.-..',
        'm': '--',
        'n': '-.',
        'o': '---',
        'p': '.--.',
        'q': '--.-',
        'r': '.-.',
        's': '...',
        't': '-',
        'u': '..-',
        'v': '...-',
        'w': '.--',
        'x': '-..-',
        'y': '-.--',
        'z': '--..',
        '0': '-----',
        '1': '.----',
        '2': '..---',
        '3': '...--',
        '4': '....-',
        '5': '.....',
        '6': '-....',
        '7': '--...',
        '8': '---..',
        '9': '----.',
        '.': '.-.-.-',
        ',': '--..--',
        '?': '..--..',
        "'": '.----.',
        '’': '.----.',
        '!': '-.-.--',
        '/': '-..-.',
        '(': '-.--.',
        ')': '-.--.-',
        '&': '.-...',
        ':': '---...',
        ';': '-.-.-.',
        '=': '-...-',
        '+': '.-.-.',
        '-': '-....-',
        '_': '..--.-',
        '"': '.-..-.',
        '$': '...-..-',
        '@': '.--.-.',
        '[End of work]': '...-.-',
        '[Error]': '........',
        '[Invitation to transmit]': '-.-',
        '[Starting Signal]': '-.-.-',
        '[New Page Signal]': '.-.-.',
        '[Understood]': '...-.',
        '[Wait]': '.-...',
        '[SOS]': '...---...',
        'à': '.--.-',
        'ä': '.-.-',
        'å': '.--.-',
        'ą': '.-.-',
        'æ': '.-.-',
        'ć': '-.-..',
        'ĉ': '-.-..',
        'ç': '-.-..',
        'đ': '..-..',
        'ð': '..--.',
        'é': '..-..',
        'è': '.-..-',
        'ę': '..-..',
        'ĝ': '--.-.',
        'ĥ': '----',
        'ĵ': '.---.',
        'ł': '.-..-',
        'ń': '--.--',
        'ñ': '--.--',
        'ó': '---.',
        'ö': '---.',
        'ø': '---.',
        'ś': '...-...',
        'ŝ': '...-.',
        'š': '----',
        'þ': '.--..',
        'ü': '..--',
        'ŭ': '..--',
        'ź': '--.-.',
        'ż': '--.-',
    }
    _MORSE_TO_UNICODE = utils.flip_dict(_UNICODE_TO_MORSE)
    _ERROR = '[?]'
    _EXTENDED_REGEX = re.compile(r"""[^a-z0-9?,.;"'’\n\r\t]""")

    def __init__(self, dot: str = '.', dash='-', letter_sep=' ', word_sep: str = '/', extended: bool = False):
        """Create a Morse encoder/decoder.

        :param dot: Character to use as the dot.
        :param dash: Character to use as the dash.
        :param letter_sep: Character to use as the letter separator.
        :param word_sep: Character to use as the word separator.
        :param extended: Whether to allow characters other than A/a through Z/z and 0 through 9.
        """
        self._dot = dot
        self._dash = dash
        self._letter_sep = utils.unescape(letter_sep)
        self._word_sep = utils.unescape(word_sep)
        self._extended = extended

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'dot': self._dot,
            'dash': self._dash,
            'letter_sep': self._letter_sep,
            'word_sep': self._word_sep,
            'extended': self._extended,
        }


class ToMorseCode(_MorseCode):
    """Encode text to Morse code."""

    def apply(self, s: str) -> str:
        words = []
        for word in re.split(r'\s', s):
            m_word = []
            for c in word:
                c = c.lower()
                if self._extended or not self._EXTENDED_REGEX.fullmatch(c):
                    m_word.append(self._UNICODE_TO_MORSE.get(c, '').replace('.', self._dot).replace('-', self._dash))
            words.append(self._letter_sep.join(m_word))
        return self._word_sep.join(words)


class FromMorseCode(_MorseCode):
    """Decode Morse code into text."""

    def __init__(self, dot: str = '.', dash='-', letter_sep=' ', word_sep: str = '/', extended: bool = False,
                 caps: bool = True):
        """Create a Morse decoder.

        :param dot: Character to use as the dot.
        :param dash: Character to use as the dash.
        :param letter_sep: Character to use as the letter separator.
        :param word_sep: Character to use as the word separator.
        :param extended: Whether to allow characters other than A/a through Z/z and 0 through 9.
        :param caps: Whether the translated text should be in all-caps.
        """
        super().__init__(dot=dot, dash=dash, letter_sep=letter_sep, word_sep=word_sep, extended=extended)
        self._caps = caps

    def apply(self, s: str) -> str:
        words = []
        for m_word in s.split(self._word_sep):
            word = ''
            for m_c in m_word.split(self._letter_sep):
                c = self._MORSE_TO_UNICODE.get(m_c.replace(self._dot, '.').replace(self._dash, '-'), self._ERROR)
                if c[0] == '[' or self._extended or not self._EXTENDED_REGEX.fullmatch(c):
                    if self._caps and c[0] != '[':
                        c = c.upper()
                    word += c
                else:
                    word += self._ERROR
            words.append(word)
        return ' '.join(words)
