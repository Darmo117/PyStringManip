import re
import typing as typ

from .. import _core
from ... import utils


class RemoveWhitespace(_core.Operation):
    """Remove whitespace."""

    def __init__(self, exclude: str = ''):
        """Create an operation that removes whitespace.

        :param exclude: The list of whitespace characters to keep.
        """
        if match := re.search(r'(\S)', utils.unescape_whitespace(exclude)):
            raise ValueError(
                f'found non-whitespace character in exclusion list at index {match.start(1) + 1}: {match.group(1)!r}')
        self._exclude = exclude

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'exclude': self._exclude,
        }

    def apply(self, s: str) -> str:
        return re.sub(fr'[^\S{self._exclude}]', '', s)


class RemoveNullBytes(_core.Operation):
    """Remove all null bytes."""

    def apply(self, s: str) -> str:
        return s.replace('\0', '')


class Replace(_core.Operation):
    """Find and replace text."""

    def __init__(self, regex: str = '', repl: str = '', flags: str = 'gm'):
        r"""Create a replace operation.

        :param regex: The substring to find in modes 's' and 'x' or the regex in mode 'r'.
        :param repl: The replacement string. When in regex mode you can use '\<group #>' to insert captured groups.
        :param flags: The list of regex flags: 's' to make the dot match new lines,
         'i' for case insensitiveness, 'm' to make '^' and '$' match the start and end of lines,
         'x' to ignore whitespace, 'g' to continue after the first match, 'a' to match only ASCII characters.
        """
        self._regex = re.compile(regex, flags=utils.regex_flags_to_int(flags))
        self._repl = repl
        self._flags = flags

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'regex': self._regex.pattern,
            'repl': self._repl,
            'flags': self._flags,
        }

    def apply(self, s: str) -> str:
        return self._regex.sub(self._repl, s, count='g' not in self._flags)


class Occurrences(_core.Operation):
    """Count occurrences of substrings that match the given regex."""

    def __init__(self, regex: str = '', flags: str = '', invert: bool = False):
        """Create an occurrences counter.

        :param regex: The regex.
        :param flags: The list of regex flags: 's' to make the dot match new lines,
         'i' for case insensitiveness, 'm' to make '^' and '$' match the start and end of lines,
         'x' to ignore whitespace, 'a' to match only ASCII characters.
        :param invert: If true, filters out strings that do match the regex.
        """
        self._regex = re.compile(regex, flags=utils.regex_flags_to_int(flags))
        self._flags = flags
        self._invert = invert

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'regex': self._regex.pattern,
            'flags': self._flags,
            'invert': self._invert,
        }

    def apply(self, s: str) -> str:
        return str(len(self._regex.findall(s)))


class CheckSimilarities(_core.Operation):
    """Check which characters are at the same place in all substrings."""

    def __init__(self, delimiter: str = '\n'):
        """Create a similarities checking operation.

        :param delimiter: The string to use to split inputs.
        """
        self._delimiter = delimiter

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'delimiter': self._delimiter,
        }

    def apply(self, s: str) -> str:
        lines = s.split(self._delimiter)
        if len(lines) < 2:
            raise ValueError('not enough values to compare')
        length = min(map(len, lines))
        flags = ''
        for i in range(length):
            if all(lines[0][i] == lines[j][i] for j in range(1, len(lines))):
                flags += '^'
            else:
                flags += ' '
        return '\n'.join(lines + [flags])
