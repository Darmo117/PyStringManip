import abc
import re
import typing as typ

from .. import _core
from ... import utils


class Uppercase(_core.Operation):
    """Convert all letters to upper case."""

    def apply(self, s: str) -> str:
        return s.upper()


class Lowercase(_core.Operation):
    """Convert all letters to lower case."""

    def apply(self, s: str) -> str:
        return s.lower()


class AddLineNumbers(_core.Operation):
    """Add line number at the start of each line."""

    def apply(self, s: str) -> str:
        res = []
        for i, line in enumerate(s.split('\n')):
            res.append(f'{i} {line}')
        return '\n'.join(res)


class RemoveLineNumbers(_core.Operation):
    """Remove line number from the start of each line."""

    def apply(self, s: str) -> str:
        res = []
        for line in s.split('\n'):
            res.append(re.sub(r'^\d+ ', '', line))
        return '\n'.join(res)


class Reverse(_core.Operation):
    """Reverse the text."""

    def __init__(self, by_line: bool = False):
        """Create a reverse operation.

        :param by_line: If true, line order will be reversed instead of the whole text’s characters.
        """
        self._by_line = by_line

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'by_line': self._by_line,
        }

    def apply(self, s: str) -> str:
        if self._by_line:
            return '\n'.join(s.split('\n')[::-1])
        return s[::-1]


class Sort(_core.Operation):
    """Sort entries after spliting text with the specified delimiter."""

    _ALPHA_CS = 'alpha'
    _ALPHA_CI = 'alpha_i'
    _NUMERIC = 'numeric'
    _NUMERIC_HEX = 'numeric_hex'
    _IP_ADDRESS = 'ip_address'

    def __init__(self, delimiter: str = '\n', mode: str = _ALPHA_CI, reverse: bool = False):
        """Create a sort operation.

        :param delimiter: The character to use to split the text.
        :param mode: The sorting mode: 'alpha' for case-sensitive lexicographical order, 'alpha_i' for case-insensitive,
         'numeric' to sort base-10 numbers, 'numeric_hex' to sort base-16 numbers, 'ip_address' for IPv4 addresses.
        :param reverse: Whether to sort in reverse order.
        """
        self._sort_functions = {
            self._ALPHA_CS: lambda s: s,
            self._ALPHA_CI: str.lower,
            self._NUMERIC: int,
            self._NUMERIC_HEX: lambda s: int(s, 16),
            self._IP_ADDRESS: lambda s: tuple(map(int, s.split('.'))),
        }
        if mode not in self._sort_functions:
            raise ValueError(f'invalid sort mode: {mode}')
        self._delimiter = delimiter
        self._mode = mode
        self._reverse = reverse

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'delimiter': self._delimiter,
            'mode': self._mode,
            'reverse': self._reverse,
        }

    def apply(self, s: str) -> str:
        return self._delimiter.join(
            sorted(s.split(self._delimiter), key=self._sort_functions[self._mode], reverse=self._reverse))


class Unique(_core.Operation):
    """Remove duplicate entries after spliting text with the specified delimiter."""

    def __init__(self, delimiter: str = '\n'):
        """Create a unique filter.

        :param delimiter: The string to split the text with.
        """
        self._delimiter = delimiter

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'delimiter': self._delimiter,
        }

    def apply(self, s: str) -> str:
        res = []
        for chunk in s.split(self._delimiter):
            if chunk not in res:
                res.append(chunk)
        return self._delimiter.join(res)


class Filter(_core.Operation):
    """Split the text then filter out each substring that does not match the given regex."""

    def __init__(self, delimiter: str = '\n', regex: str = '', flags: str = '', invert: bool = False):
        """Create a filter.

        :param delimiter: The string to split the text with.
        :param regex: The regex.
        :param flags: The list of regex flags: 's' to make the dot match new lines,
         'i' for case insensitiveness, 'm' to make '^' and '$' match the start and end of lines,
         'x' to ignore whitespace, 'a' to match only ASCII characters.
        :param invert: If true, filters out strings that do match the regex.
        """
        self._delimiter = delimiter
        self._regex = re.compile(regex, flags=utils.regex_flags_to_int(flags))
        self._flags = flags
        self._invert = invert

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'delimiter': self._delimiter,
            'regex': self._regex.pattern,
            'flags': self._flags,
            'invert': self._invert,
        }

    def apply(self, s: str) -> str:
        res = []
        for chunk in s.split(self._delimiter):
            # ^ <=> XOR
            if (self._regex.search(chunk) is not None) ^ self._invert:
                res.append(chunk)
        return self._delimiter.join(res)


class RemoveBom(_core.Operation):
    """Remove the Byte Order Mark (BOM) from a UTF-8 string."""

    def apply(self, s: str) -> str:
        bytes_ = bytes(s, 'utf8')
        if bytes_[:3] == b'\xEF\xBB\xBF':
            return bytes_[3:].decode('utf8')
        return s


class _TakeChunk(_core.Operation, abc.ABC):
    """Base class for operations that take string slices."""

    def __init__(self, delimiter: str):
        self._delimiter = delimiter

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'delimiter': self._delimiter,
        }

    @abc.abstractmethod
    def _take(self, s: typ.List[str]) -> typ.List[str]:
        pass

    def apply(self, s: str) -> str:
        return self._delimiter.join(self._take(s.split(self._delimiter)))


class Head(_TakeChunk):
    """Keep only the first n substrings."""

    def __init__(self, delimiter: str = '\n', n: int = 10):
        """Create a head operation.

        :param delimiter: The string to split the text with.
        :param n: The number of substrings to keep from the start.
        """
        super().__init__(delimiter=delimiter)
        self._n = n

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            **super().get_params(),
            'n': self._n,
        }

    def _take(self, s: typ.List[str]) -> typ.List[str]:
        return s[:self._n]


class Tail(_TakeChunk):
    """Keep only the last n substrings."""

    def __init__(self, delimiter: str = '\n', n: int = 10):
        """Create a tail operation.

        :param delimiter: The string to split the text with.
        :param n: The number of substrings to keep from the end.
        """
        super().__init__(delimiter=delimiter)
        self._n = n

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            **super().get_params(),
            'n': self._n,
        }

    def _take(self, s: typ.List[str]) -> typ.List[str]:
        return s[-self._n:]


class Slice(_TakeChunk):
    """Keep only the substrings in the specified range."""

    def __init__(self, delimiter: str = '\n', start: int = None, end: int = None, step: int = 1):
        """Create a slice operation.

        :param delimiter: The string to split the text with.
        :param start: Slice’s first index.
        :param end: Slice’s last index (exclusive).
        :param step: Slice’s step.
        """
        super().__init__(delimiter=delimiter)
        self._start = start
        self._end = end
        self._step = step

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            **super().get_params(),
            'start': self._start,
            'end': self._end,
            'step': self._step,
        }

    def _take(self, s: typ.List[str]) -> typ.List[str]:
        return s[self._start:self._end:self._step]


class _TakeBytes(_core.Operation, abc.ABC):
    """Base class for operations that take/drop byte slices."""

    def __init__(self, encoding: str = 'utf8', start: int = 0, n: int = 10):
        """Create bytes slicing operation.

        :param encoding: The text’s encoding.
        :param start: Index of the first byte of the range.
        :param n: The number of bytes.
        """
        self._encoding = encoding
        self._start = start
        self._n = n

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'encoding': self._encoding,
            'start': self._start,
            'n': self._n,
        }


class TakeBytes(_TakeBytes):
    """Keep only the bytes within the specified range."""

    def apply(self, s: str) -> str:
        return bytes(s, self._encoding)[self._start:self._start + self._n].decode(self._encoding)


class DropBytes(_TakeBytes):
    """Drop the bytes within the specified range."""

    def apply(self, s: str) -> str:
        bytes_ = bytes(s, self._encoding)
        return (bytes_[:self._start] + bytes_[self._start + self._n:]).decode(self._encoding)


class Escape(_core.Operation):
    r"""Escape special characters: '\\n', '\\r', '\\t', '\\f', '\\v', '\\b', '\\' and the specified quote (', " or `)"""

    _CHARS = {
        '\\': r'\\',
        '\n': r'\n',
        '\r': r'\r',
        '\t': r'\t',
        '\f': r'\f',
        '\v': r'\v',
        '\b': r'\b',
    }

    _SINGLE_QUOTE = 'single'
    _DOUBLE_QUOTE = 'double'
    _BACK_QUOTE = 'back'

    def __init__(self, escape_quote: str = _SINGLE_QUOTE):
        """Create an escape operation.

        :param escape_quote: The quote to escape: 'single' for ', 'double' for " and 'back' for `.
        """
        self._escape_quote = escape_quote

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'escape_quote': self._escape_quote,
        }

    def apply(self, s: str) -> str:
        for c, repl in self._CHARS.items():
            s = s.replace(c, repl)
        quote = ''
        match self._escape_quote:
            case self._SINGLE_QUOTE:
                quote = "'"
            case self._DOUBLE_QUOTE:
                quote = '"'
            case self._BACK_QUOTE:
                quote = '`'
        return s.replace(quote, '\\' + quote)


class Unescape(_core.Operation):
    r"""Unescape escaped special characters: \\\\n, \\\\r, \\\\t, \\\\f, \\\\v, \\\\b, \\\\, \\', \\" and \\`."""

    _CHARS = {
        r'\n': '\n',
        r'\r': '\r',
        r'\t': '\t',
        r'\f': '\f',
        r'\v': '\v',
        r'\b': '\b',
        r'\\': '\\',
    }

    def apply(self, s: str) -> str:
        for c, repl in self._CHARS.items():
            s = s.replace(c, repl)
        s = s.replace(r"\'", "'").replace(r'\"', '"').replace(r'\`', '`')
        return s
