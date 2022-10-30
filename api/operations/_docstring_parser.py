"""Provides a function to parse docstring in reStructured format.

Adapted from https://github.com/openstack/rally/blob/master/rally/common/plugin/info.py.
"""

import dataclasses
import math
import re

_PARAM_OR_RETURNS_REGEX = re.compile(':(?:param|returns)')
_RETURNS_REGEX = re.compile(':returns: (?P<doc>.*)', re.S)
_PARAM_REGEX = re.compile(r':param (?P<name>[*\w]+): (?P<doc>.*?)(?:(?=:param)|(?=:return)|(?=:raises)|\Z)', re.S)


def _trim(docstring: str) -> str:
    """trim function from PEP-257"""
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = math.inf
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < math.inf:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)

    return '\n'.join(trimmed)


def _reindent(string: str) -> str:
    return '\n'.join(line.strip() for line in string.strip().split('\n'))


@dataclasses.dataclass
class DocString:
    short_description: str = None
    long_description: str = None
    params: dict[str, str] = None
    returns: str = None


def parse_docstring(docstring: str) -> DocString:
    """Parse a docstring into its components."""
    short_description = long_description = returns = ''
    params = {}

    if docstring:
        docstring = _trim(docstring)
        lines = docstring.split('\n', 1)
        short_description = lines[0]

        if len(lines) > 1:
            long_description = lines[1].strip()
            params_returns_desc = None

            if match := _PARAM_OR_RETURNS_REGEX.search(long_description):
                long_desc_end = match.start()
                params_returns_desc = long_description[long_desc_end:].strip()
                long_description = long_description[:long_desc_end].rstrip()

            if params_returns_desc:
                params = {
                    name: _trim(doc)
                    for name, doc in _PARAM_REGEX.findall(params_returns_desc)
                }
                if match := _RETURNS_REGEX.search(params_returns_desc):
                    returns = _reindent(match.group('doc'))

    return DocString(
        short_description=short_description,
        long_description=long_description,
        params=params,
        returns=returns,
    )
