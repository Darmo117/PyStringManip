import re

from .. import _core


class ParseUnixFilePerms(_core.Operation):
    """Parse a UNIX file permission string. Supports both literal and octal notations."""

    _LITERAL_REGEX = re.compile(
        '(?P<ftype>[-dlpscbD])'
        '(?P<ur>[-r])(?P<uw>[-w])(?P<ux>[-xsS])'
        '(?P<gr>[-r])(?P<gw>[-w])(?P<gx>[-xsS])'
        '(?P<or>[-r])(?P<ow>[-w])(?P<ox>[-xtT])'
    )
    _NUMERIC_REGEX = re.compile('(?P<b>[0-7])(?P<u>[0-7])(?P<g>[0-7])(?P<o>[0-7])')

    _FILE_TYPES = {
        '-': 'File',
        'd': 'Directory',
        'l': 'Symbolic Link',
        'p': 'Named Pipe',
        's': 'Socket',
        'c': 'Character Device',
        'b': 'Block Device',
        'D': 'Door',
    }

    def apply(self, s: str) -> str:
        def r(r_: bool) -> str:
            return 'r' if r_ else '-'

        def w(w_: bool) -> str:
            return 'w' if w_ else '-'

        def xs(x_: bool, s_: bool) -> str:
            match x_, s_:
                case True, True:
                    return 's'
                case False, True:
                    return 'S'
                case True, False:
                    return 'x'
                case False, False:
                    return '-'

        def xt(x_: bool, t_: bool) -> str:
            match x_, t_:
                case True, True:
                    return 't'
                case False, True:
                    return 'T'
                case True, False:
                    return 'x'
                case False, False:
                    return '-'

        def octal(r_: bool, w_: bool, x_: bool) -> int:
            return (r_ << 2) | (w_ << 1) | x_

        def x(b: bool) -> str:
            return 'X' if b else ' '

        if match := self._LITERAL_REGEX.match(s):
            ftype = match.group('ftype')
            ur = match.group('ur') == 'r'
            uw = match.group('uw') == 'w'
            ux = match.group('ux') in 'xs'
            gr = match.group('gr') == 'r'
            gw = match.group('gw') == 'w'
            gx = match.group('gx') in 'xs'
            or_ = match.group('or') == 'r'
            ow = match.group('ow') == 'w'
            ox = match.group('ox') in 'xt'
            us = match.group('ux') in 'sS'
            gs = match.group('gx') in 'sS'
            ot = match.group('ox') in 'tT'
        elif match := self._NUMERIC_REGEX.match(s):
            ftype = None
            bo = int(match.group('b'))
            uo = int(match.group('u'))
            go = int(match.group('g'))
            oo = int(match.group('o'))
            ur, uw, ux = bool(uo & 4), bool(uo & 2), bool(uo & 1)
            gr, gw, gx = bool(go & 4), bool(go & 2), bool(go & 1)
            or_, ow, ox = bool(oo & 4), bool(oo & 2), bool(oo & 1)
            us, gs, ot = bool(bo & 4), bool(bo & 2), bool(bo & 1)
        else:
            raise ValueError('could not find a valid file permission string')
        return f"""\
Textual representation: {ftype or '-'}{r(ur)}{w(uw)}{xs(ux, us)}{r(gr)}{w(gw)}{xs(gx, gs)}{r(or_)}{w(ow)}{xt(ox, ot)}
Octal representation:   {octal(us, gs, ot)}{octal(ur, uw, ux)}{octal(gr, gw, gx)}{octal(or_, ow, ox)}
File type: {self._FILE_TYPES[ftype] if ftype else 'Unknown'}
setuid bit: {int(us)}
setgid bit: {int(gs)}
sticky bit: {int(ot)}
          +-------+-------+-------+
          | User  | Group | Other |
+---------+-------+-------+-------+
|    Read |   {x(ur)}   |   {x(gr)}   |   {x(or_)}   |
+---------+-------+-------+-------+
|   Write |   {x(uw)}   |   {x(gw)}   |   {x(ow)}   |
+---------+-------+-------+-------+
| Execute |   {x(ux)}   |   {x(gx)}   |   {x(ox)}   |
+---------+-------+-------+-------+
"""
