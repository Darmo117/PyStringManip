import re
import typing as typ

from .. import _core


class Replace(_core.Operation):
    """Find and replace text."""

    _STRING = 's'
    _EXTENDED = 'x'
    _REGEX = 'r'

    def __init__(self, find: str = '', repl: str = '', mode: str = _STRING, flags: str = 'gm'):
        r"""Create a replace operation.

        :param find: The substring to find in modes 's' and 'x' or the regex in mode 'r'.
        :param repl: The replacement string. When in regex mode you can use '\<group #>' to insert captured groups.
        :param mode: The replacement mode: 's' for normal string, 'x' to match '\n', '\r' and '\t',
         'r' for regular expressions.
        :param flags: The list of flags when in regex mode: 's' to make the dot match new lines,
         'i' for case insensitiveness, 'm' to make '^' and '$' match the start and end of lines,
         'x' to ignore whitespace, 'g' to continue after the first match, 'a' to match only ASCII characters.
        """
        if mode not in (self._STRING, self._EXTENDED, self._REGEX):
            raise ValueError(f'invalid replace mode: {mode!r}')
        self._find = find
        self._repl = repl
        self._mode = mode
        self._flags = flags

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'find': self._find,
            'repl': self._repl,
            'mode': self._mode,
            'flags': self._flags,
        }

    def apply(self, s: str) -> str:
        match self._mode:
            case self._STRING:
                return s.replace(self._find, self._repl)
            case self._EXTENDED:
                def extend(string: str) -> str:
                    return string.replace(r'\n', '\n').replace(r'\r', '\r').replace(r'\t', '\t')

                return s.replace(extend(self._find), extend(self._repl))
            case self._REGEX:
                flags = 0
                for f in self._flags:
                    match f:
                        case 's':
                            flags |= re.DOTALL
                        case 'm':
                            flags |= re.MULTILINE
                        case 'a':
                            flags |= re.ASCII
                        case 'i':
                            flags |= re.IGNORECASE
                        case 'x':
                            flags |= re.VERBOSE
                return re.sub(self._find, self._repl, s, flags=flags, count='g' not in self._flags)