import abc
import datetime
import ipaddress
import re
import typing as typ
import urllib.parse

from . import _core
from . import informatics
from .. import utils


class _Extractor(_core.Operation, abc.ABC):
    """Base class for all extractors."""

    def __init__(self, display_total: bool = False, sort: bool = False, unique: bool = False, joiner: str = '\n'):
        """Create an extractor.

        :param display_total: Whether to display the total number of results.
        :param sort: Whether to sort the results.
        :param unique: Whether to remove duplicate results.
        :param joiner: The string to join the extracted results with.
        """
        self._display_total = display_total
        self._sort = sort
        self._unique = unique
        self._joiner = utils.unescape(joiner)

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'display_total': self._display_total,
            'sort': self._sort,
            'unique': self._unique,
            'joiner': self._joiner,
        }

    def apply(self, s: str) -> str:
        values = self._extract(s)
        if self._unique:
            values = list(set(values))
        if self._sort:
            values.sort()
        res = self._joiner.join(values)
        if self._display_total:
            res = f'Total found: {len(values)}\n\n' + res
        return res

    @abc.abstractmethod
    def _extract(self, s: str) -> typ.List[str]:
        pass


class ExtractIps(_Extractor):
    """Extract all IP addresses."""

    def __init__(self, display_total: bool = False, sort: bool = False, unique: bool = False,
                 ipv4: bool = True, ipv6: bool = True, hide_private: bool = False, joiner: str = '\n'):
        """Create an IP address extractor.

        :param display_total: Whether to display the total number of results.
        :param sort: Whether to sort the results.
        :param unique: Whether to remove duplicate results.
        :param ipv4: Whether to extract IPv4s.
        :param ipv6: Whether to extract IPv6s.
        :param hide_private: Whether to hide local addresses.
        :param joiner: The string to join the extracted results with.
        """
        super().__init__(display_total=display_total, sort=sort, unique=unique, joiner=joiner)
        self._ipv4 = ipv4
        self._ipv6 = ipv6
        self._hide_private = hide_private

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            **super().get_params(),
            'hide_private': self._hide_private,
        }

    def _extract(self, s: str) -> typ.List[str]:
        def _map(it: typ.Iterator[re.Match[str]], cast: typ.Type[ipaddress.IPv4Address | ipaddress.IPv6Address]) \
                -> typ.List[str]:
            return [m.group() for m in it if not self._hide_private or not cast(m.group()).is_private]

        ips = []
        if self._ipv4:
            ips.extend(_map(informatics.DefangIpAddresses.IPV4_REGEX.finditer(s), ipaddress.IPv4Address))
        if self._ipv6:
            ips.extend(_map(informatics.DefangIpAddresses.IPV6_REGEX.finditer(s), ipaddress.IPv6Address))
        return ips


class ExtractMacAddresses(_Extractor):
    """Extract all MAC addresses."""

    _MAC_ADDRESS_REGEX = re.compile(r'(?:[a-fA-F\d]{1,2}:){5}[a-fA-F\d]{1,2}')

    def _extract(self, s: str) -> typ.List[str]:
        return self._MAC_ADDRESS_REGEX.findall(s)


class ExtractUrls(_Extractor):
    """Extract all URLs."""

    _URL_REGEX = re.compile(r"""\w*://[\w.-]+(?:\.[\w.-]+)+[-\w._~:/?#\[\]@!$&'()*+,;=]+""")

    def _extract(self, s: str) -> typ.List[str]:
        return self._URL_REGEX.findall(s)


class ExtractDomains(ExtractUrls):
    """Extract all URL domains."""

    def _extract(self, s: str) -> typ.List[str]:
        return [urllib.parse.urlparse(url).netloc for url in self._URL_REGEX.findall(s)]


class ExtractEmails(_Extractor):
    """Extract all email addresses."""

    # https://www.emailregex.com/
    _EMAIL_REGEX = re.compile(r"""
(?:
     [a-z\d!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z\d!#$%&'*+/=?^_`{|}~-]+)*
    |"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*"
)
@
(?:
     (?:[a-z0-9](?:[a-z\d-]*[a-z\d])?\.)+[a-z\d](?:[a-z\d-]*[a-z\d])?
    |\[(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}
     (?:
         25[0-5]
        |2[0-4]\d
        |[01]?\d\d?
        |[a-z\d-]*[a-z\d]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+
     )]
)
""", re.VERBOSE)

    def _extract(self, s: str) -> typ.List[str]:
        return self._EMAIL_REGEX.findall(s)


class ExtractFilePaths(_Extractor):
    """Extract all file paths."""

    # Illegal characters: https://stackoverflow.com/a/31976060/3779986
    _UNIX_FP_REGEX = re.compile(r'/(?:[^/\0\n\r]+/?)+|(?:[^/\0\n\r]+/)+[^/\0\n\r]*')
    _UNIX_FP_REGEX_NO_WS = re.compile(_UNIX_FP_REGEX.pattern.replace(r'\n\r', r'\s'))
    _WINDOWS_FP_REGEX = re.compile(
        r'[a-zA-Z]:\\(?:[^\\<>:"/|?*\x00-\x1f\n\r]+\\?)+|(?:[^\\<>:"/|?*\x00-\x1f\n\r]+\\)+[^\\<>:"/|?*\x00-\x1f\n\r]*')
    _WINDOWS_FP_REGEX_NO_WS = re.compile(_WINDOWS_FP_REGEX.pattern.replace(r'\n\r', r'\s'))

    def __init__(self, display_total: bool = False, sort: bool = False, unique: bool = False,
                 unix: bool = True, windows: bool = True, exclude_ws: bool = True, joiner: str = '\n'):
        """Create a file path extractor.

        :param display_total: Whether to display the total number of results.
        :param sort: Whether to sort the results.
        :param unique: Whether to remove duplicate results.
        :param unix: Whether to extract UNIX paths.
        :param windows: Whether to extract Windows paths.
        :param exclude_ws: Whether to exclude all whitespace characters.
        :param joiner: The string to join the extracted results with.
        """
        super().__init__(display_total=display_total, sort=sort, unique=unique, joiner=joiner)
        self._unix = unix
        self._windows = windows
        self._exclude_ws = exclude_ws

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            **super().get_params(),
            'unix': self._unix,
            'windows': self._windows,
            'exclude_ws': self._exclude_ws,
        }

    def _extract(self, s: str) -> typ.List[str]:
        paths = []
        if self._unix:
            paths.extend((self._UNIX_FP_REGEX_NO_WS if self._exclude_ws else self._UNIX_FP_REGEX).findall(s))
        if self._windows:
            paths.extend((self._WINDOWS_FP_REGEX_NO_WS if self._exclude_ws else self._WINDOWS_FP_REGEX).findall(s))
        return paths


class ExtractDates(_Extractor):
    """Extract dates in the format "yyyy-mm-dd", "dd/mm/yyyy" or "mm/dd/yyyy".
    Separators may be any of "/-." or space.
    """

    @staticmethod
    def __generate(s: str):
        for sep in '-/. ':
            yield s.replace('§', sep)

    _DATE_REGEX = re.compile(r'\d{4}(?:[-/. ]\d{2}){2}|(?:\d{2}[-/. ]){2}\d{4}')
    _FORMATS = (*__generate('%Y§%m§%d'), *__generate('%d§%m§%Y'), *__generate('%m§%d§%Y'))

    def _extract(self, s: str) -> typ.List[str]:
        def f(m: str) -> bool:
            for df in self._FORMATS:
                try:
                    datetime.datetime.strptime(m, df)
                    return True
                except ValueError:
                    pass
            return False

        matches = self._DATE_REGEX.finditer(s)
        return list(filter(f, (m.group(0) for m in matches)))


class Regex(_core.Operation):
    """Extract strings that match a regular expression."""

    _MATCHES = 'matches'
    _GROUPS = 'groups'
    _MATCHES_GROUPS = 'matches_and_groups'

    def __init__(self, regex: str = '', flags: str = 'm', display_total: bool = False, output_format: str = _MATCHES,
                 joiner: str = '\n', match_groups_joiner: str = '\n\t', groups_joiner: str = ','):
        f"""Create a regex extractor.

        :param regex: The substring to find in modes 's' and 'x' or the regex in mode 'r'.
        :param flags: The list of regex flags: 's' to make the dot match new lines,
         'i' for case insensitiveness, 'm' to make '^' and '$' match the start and end of lines,
         'x' to ignore whitespace, 'a' to match only ASCII characters.
        :param joiner: The string to use to join the matches.
        :param match_groups_joiner: The string to use to join matches with their capture groups in
         {self._MATCHES_GROUPS!r} mode.
        :param groups_joiner: The string to use to join capture groups.
        """
        if output_format not in (self._MATCHES, self._GROUPS, self._MATCHES_GROUPS):
            raise ValueError(f'invalid output format: {output_format!r}')
        self._regex = re.compile(regex, flags=utils.regex_flags_to_int(flags))
        self._flags = flags
        self._display_total = display_total
        self._output_format = output_format
        self._joiner = utils.unescape(joiner)
        self._match_groups_joiner = utils.unescape(match_groups_joiner)
        self._groups_joiner = utils.unescape(groups_joiner)

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'regex': self._regex.pattern,
            'flags': self._flags,
            'display_total': self._display_total,
            'output_format': self._output_format,
            'joiner': self._joiner,
            'match_groups_joiner': self._match_groups_joiner,
            'groups_joiner': self._groups_joiner,
        }

    def apply(self, s: str) -> str:
        def _map(m: re.Match) -> str:
            match self._output_format:
                case self._MATCHES:
                    return m.group(0)
                case self._GROUPS:
                    return self._groups_joiner.join(m.groups())
                case self._MATCHES_GROUPS:
                    return f'{m.group(0)}{self._match_groups_joiner}{self._groups_joiner.join(m.groups())}'

        matches = list(self._regex.finditer(s))
        res = f'Total: {len(matches)}\n\n' if self._display_total else ''
        return res + self._joiner.join(map(_map, matches))
