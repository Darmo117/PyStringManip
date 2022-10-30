"""This module defines various utility functions."""
import math
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


_DIGITS = '0123456789abcdefghijklmnopqrstuvwxyz'


def format_int(n: int, base: int, uppercase: bool = False, pad: int = -1) -> str:
    """Format an integer into the given base.

    :param n: The integer.
    :param base: The target base.
    :param uppercase: Whether to put non-numeric digits in the resulting string to uppercase or not.
    :param pad: The padding amount. -1 will adapt padding to output base.
    :return: The formatted integer.
    :raises ValueError: If the base is not in [2, 36].
    """
    if not (2 <= base <= 36):
        raise ValueError(f'invalid base {base}')
    flag = {2: 'bb', 8: 'oo', 16: 'xX'}.get(base)
    padding_length = math.ceil(math.log(256) / math.log(base)) if pad < 0 else pad
    if flag:
        return format(n, f'0{padding_length}{flag[uppercase]}')
    else:
        res = ''
        while n >= base:
            res = _DIGITS[n % base] + res
            n //= base
        res = (_DIGITS[n % base] + res).rjust(padding_length, '0')
        return res.upper() if base > 10 and uppercase else res
