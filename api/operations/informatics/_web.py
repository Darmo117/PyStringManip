import abc
import io
import json
import re
import typing as typ
import urllib.parse

import bs4
import jsonpath
import lxml.etree
import lxml.html

from .. import _core


class EncodeUrl(_core.Operation):
    """Escape some special characters from a URL: []@!$'\"()*+,;% and non-ASCII characters."""

    def apply(self, s: str) -> str:
        return urllib.parse.quote(s, safe=':/?=&#')


class EncodeUrlComponent(_core.Operation):
    """Escape all special characters from a URL: /:?=&#[]@!$'\"()*+,;% and non-ASCII characters."""

    def apply(self, s: str) -> str:
        return urllib.parse.quote_plus(s)


class DecodeUrl(_core.Operation):
    """Replace all %xx values by the corresponding UTF-8 character."""

    def apply(self, s: str) -> str:
        return urllib.parse.unquote(s)


class DecodeUrlComponent(_core.Operation):
    """Replace all %xx values by the corresponding UTF-8 character and replaces the '+' sign by a space."""

    def apply(self, s: str) -> str:
        return urllib.parse.unquote_plus(s)


class ParseUrl(_core.Operation):
    """Parse a URL then print its parts."""

    def apply(self, s: str) -> str:
        parsed_url = urllib.parse.urlparse(s)
        query = urllib.parse.parse_qs(parsed_url.query)
        args = '\n'.join(f'  {k}: {v}' for k, v in query.items())
        if args:
            args = '\n' + args
        return f"""\
Protocole: {parsed_url.scheme}
Host: {parsed_url.netloc}
Path: {parsed_url.path}
Parameters: {parsed_url.params}
Query arguments:{args}
Anchor: {parsed_url.fragment}\
"""


class DefangUrls(_core.Operation):
    """Defang all URLs and domains, i.e. make it invalid to avoid accidental clicks on potential malicious links."""

    _DOT_REGEX = re.compile(r'(?<=\w)\.(?=\w)')
    _SEP_REGEX = re.compile(r'(?<=\w)://(?=\w)')

    def __init__(self, escape_sep: bool = False):
        """Create an operation to disable a URL.

        :param escape_sep: Whether to also escape the '://' characters after the protocole.
        """
        self._escape_sep = escape_sep

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'escape_sep': self._escape_sep,
        }

    def apply(self, s: str) -> str:
        s = self._DOT_REGEX.sub('[.]', s)
        if self._escape_sep:
            s = self._SEP_REGEX.sub('[://]', s)
        return s


class RemoveHtml(_core.Operation):
    """Remove all HTML/XML tags."""

    _WS_REGEX = re.compile(r'\n+')
    _TRAILING_WS_REGEX = re.compile(r'(^[\t ]+|[\t ]+$)', flags=re.MULTILINE)

    def apply(self, s: str) -> str:
        text = bs4.BeautifulSoup(s, 'lxml').text.strip()
        return self._WS_REGEX.sub('\n', self._TRAILING_WS_REGEX.sub('', text))


class _QueryPath(_core.Operation, abc.ABC):
    """Base class for XPath and JPath operations."""

    def __init__(self, query: str = '', joiner: str = '\n'):
        """Create a XPath/JPath extractor.

        :param query: The query.
        :param joiner: The string to use to join results.
        """
        self._query = query
        self._joiner = joiner

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'query': self._query,
            'joiner': self._joiner,
        }


class Xpath(_QueryPath):
    """Extract data from a XML document with an XPath query."""

    def apply(self, s: str) -> str:
        def _str(e) -> str:
            if isinstance(e, str):
                return e
            return lxml.html.tostring(e).decode('utf8').strip()

        r = lxml.etree.parse(io.StringIO(s)).xpath(self._query)
        return self._joiner.join(map(_str, r))


class Jpath(_QueryPath):
    """Extract data from a JSON document with a JPath query."""

    def apply(self, s: str) -> str:
        r = jsonpath.JSONPath(self._query).parse(json.loads(s))
        return self._joiner.join(map(str, r))
