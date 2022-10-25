import abc
import ipaddress
import re
import typing as typ
import urllib.parse

from . import _core
from . import informatics


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
        self._joiner = joiner

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'display_total': self._display_total,
            'sort': self._sort,
            'unique': self._unique,
            'joiner': self._joiner,
        }

    def apply(self, s: str) -> str:
        urls = self._extract(s)
        if self._unique:
            urls = list(set(urls))
        if self._sort:
            urls.sort()
        res = self._joiner.join(urls)
        if self._display_total:
            res = f'Total found: {len(urls)}\n\n' + res
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
