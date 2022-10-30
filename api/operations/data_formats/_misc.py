import re

from .. import _core


class ToQuotedPrintable(_core.Operation):
    """Encode UTF-8 text as Quoted Printable text."""

    _MAX_LENGTH = 76

    def apply(self, s: str) -> str:
        lines = []
        for line in s.split('\n'):
            buffer = ''
            for c in line:
                if c.isascii():
                    char = c
                else:
                    char = ''.join((f'={b:02X}' for b in bytes(c, 'utf8')))
                if len(buffer + char) == self._MAX_LENGTH - 1:
                    lines.append(buffer + char + '=')
                    buffer = ''
                elif len(buffer + char) > self._MAX_LENGTH - 1:
                    lines.append(buffer + '=')
                    buffer = char
                else:
                    buffer += char
            if buffer:
                lines.append(buffer)
        return '\n'.join(lines)


class FromQuotedPrintable(_core.Operation):
    """Decode Quoted Printable text into UTF-8."""

    _BYTES_REGEX = re.compile(r'(=[0-9a-fA-F]{2})+')

    def apply(self, s: str) -> str:
        def decode(m: re.Match) -> str:
            return b''.join(int(c, 16).to_bytes(1, 'big') for c in m.group(0)[1:].split('=')).decode('utf8')

        return self._BYTES_REGEX.sub(decode, s.replace('=\n', ''))
