"""This module defines various utility functions."""

import re


def flip_dict(d: dict) -> dict:
    """Flips all entries of the given dict object.
    If multiple entries in the input dict have the same value, only the last one will be kept.

    :param d: The dict whose entries have to be flipped.
    :return: A new dict object.
    """
    return {v: k for k, v in d.items()}


def unescape(s: str) -> str:
    """Unescape all escaped characters.

    :param s: The string to unescape.
    :return: The unescaped string.
    """
    return s.encode('utf8').decode('unicode_escape')


def regex_flags_to_int(flags: str) -> int:
    """Convert string regex flags into an int that can then be passed to `re` module’s functions

    :param flags: The flags as a string. May be one of [smaix].
    :return: The corresponding int value.
    """
    i = 0
    for f in flags:
        match f:
            case 's':
                i |= re.DOTALL
            case 'm':
                i |= re.MULTILINE
            case 'a':
                i |= re.ASCII
            case 'i':
                i |= re.IGNORECASE
            case 'x':
                i |= re.VERBOSE
    return i
