from .. import _core


class ToNato(_core.Operation):
    """Convert characters to their NATO phonetic alphabet equivalent."""

    _NATO = {
        'a': 'Alfa',
        'b': 'Bravo',
        'c': 'Charlie',
        'd': 'Delta',
        'e': 'Echo',
        'f': 'Foxtrot',
        'g': 'Golf',
        'h': 'Hotel',
        'i': 'India',
        'j': 'Juliett',
        'k': 'Kilo',
        'l': 'Lima',
        'm': 'Mike',
        'n': 'November',
        'o': 'Oscar',
        'p': 'Papa',
        'q': 'Quebec',
        'r': 'Romeo',
        's': 'Sierra',
        't': 'Tango',
        'u': 'Uniform',
        'v': 'Victor',
        'w': 'Whiskey',
        'x': 'X-ray',
        'y': 'Yankee',
        'z': 'Zulu',
        '0': 'Zero',
        '1': 'One',
        '2': 'Two',
        '3': 'Tree',
        '4': 'Fower',
        '5': 'Fife',
        '6': 'Six',
        '7': 'Seven',
        '8': 'Eight',
        '9': 'Niner',
        '.': 'Stop',
    }

    def apply(self, s: str) -> str:
        def aux(i: int, c: str) -> str:
            c_ = self._NATO.get(c.lower(), c)
            if i < len(s) - 1 and c_ != c:
                c_ += ' '
            return c_

        return ''.join(aux(i, c) for i, c in enumerate(s))
