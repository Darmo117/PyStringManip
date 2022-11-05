import csv
import io
import re
import typing as typ
import unicodedata

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

    _BYTES_REGEX = re.compile(r'(=[\da-fA-F]{2})+')

    def apply(self, s: str) -> str:
        def decode(m: re.Match) -> str:
            return b''.join(int(c, 16).to_bytes(1, 'big') for c in m.group(0)[1:].split('=')).decode('utf8')

        return self._BYTES_REGEX.sub(decode, s.replace('=\n', ''))


class ToHexDump(_core.Operation):
    """Print the hexdump of a text."""

    def __init__(self, encoding: str = 'utf8', bpl: int = 16, uppercase: bool = False, unix: bool = False):
        """Create a to_hex_dump operation

        :param encoding: Input text’s encoding.
        :param bpl: Number of bytes to display per line.
        :param uppercase: Whether to display hex in uppercase.
        :param unix: Whether to display hexdump’s |text| in the same way as UNIX systems.
        """
        self._encoding = encoding
        self._bpl = bpl
        self._uppercase = uppercase
        self._unix = unix

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'encoding': self._encoding,
            'bpl': self._bpl,
            'uppercase': self._uppercase,
            'unix': self._unix,
        }

    def apply(self, s: str) -> str:
        data = bytes(s, self._encoding)
        length = len(data)
        if length > 0xffffffff:
            raise OverflowError('too many bytes')
        x = 'X' if self._uppercase else 'x'
        lines = []
        for i in range(0, length, self._bpl):
            chunk_data = data[i:i + self._bpl]
            chunk_bytes = ' '.join(format(b, '02' + x) for b in chunk_data)
            if len(chunk_data) < self._bpl:
                # Pad last line with spaces on the end
                chunk_bytes += ' ' * ((3 * self._bpl - 1) - (3 * len(chunk_data) - 1))
            chunk_text = ''.join(self._decode(b) for b in chunk_data)
            lines.append(f'{format(i, "08" + x)}  {chunk_bytes}  |{chunk_text}|')
        lines.append(format(length, '08' + x))
        return '\n'.join(lines)

    def _decode(self, b: int) -> str:
        c = chr(b)
        # UNIX mode only prints ASCII characters
        # Don’t print control characters
        if self._unix and b > 127 or unicodedata.category(c)[0] == 'C':
            return '.'
        return c


class FromHexDump(_core.Operation):
    """Convert a hexdump into text."""

    _LINE_REGEX = re.compile(r'^[\da-fA-F]+[ \t]+((?:[\da-fA-F]{2}[ \t]+)+)[ \t]+\|.+\|$')

    def __init__(self, encoding: str = 'utf8'):
        """Create a from_hex_dump operation.

        :param encoding: Enconding of the hexdump’s underlying text.
        """
        self._encoding = encoding

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'encoding': self._encoding,
        }

    def apply(self, s: str) -> str:
        data = b''
        for i, line in enumerate(s.split('\n')):
            raw_bytes = self._LINE_REGEX.fullmatch(line)
            if raw_bytes is not None:
                data += bytes(int(b, 16) for b in filter(None, raw_bytes.group(1).split(' ')))
        return data.decode(self._encoding)


class ToTable(_core.Operation):
    """Convert CSV data into a table."""

    def __init__(self, sep: str = ',', quote: str = '"', has_header: bool = False, as_html: bool = False):
        """Create a to_table operation.

        :param sep: CSV value separator.
        :param quote: CSV quoting character.
        :param has_header: Whether to consider the first row as the table’s header.
        :param as_html: True to convert data into a HTML table, False to convert it into an ASCII table.
        """
        self._value_sep = sep
        self._quote = quote
        self._has_header = has_header
        self._as_html = as_html

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'value_sep': self._value_sep,
            'quote': self._quote,
            'has_header': self._has_header,
            'as_html': self._as_html,
        }

    def apply(self, s: str) -> str:
        with io.StringIO(s) as f:
            csv_data = csv.DictReader(f, delimiter=self._value_sep, quotechar=self._quote)
            lines = [csv_data.fieldnames, *map(self._parse_line, csv_data)]
        if self._as_html:
            return self._html(lines)
        return self._ascii(lines)

    @staticmethod
    def _parse_line(line_dict: dict[str, str | list[str | None] | None]) -> list[str]:
        def parse(line: str | typ.Iterable[str | None] | None) -> list[str]:
            values = []
            for v in line:
                match v:
                    case None:
                        values.append('')
                    case [*l]:  # csv.DictReader puts additional column values into a list
                        values.extend(parse(l))
                    case v:
                        values.append(v)
            return values

        return parse(line_dict.values())

    def _html(self, lines: list[list[str]]) -> str:
        res = '<table>\n<tbody>\n'
        for i, line in enumerate(lines):
            cell_type = 'th' if self._has_header and i == 0 else 'td'
            res += '<tr>\n' + ''.join(f'  <{cell_type}>{v}</{cell_type}>\n' for v in line) + '</tr>\n'
        return res + '</tbody>\n</table>'

    def _ascii(self, lines: list[list[str]]) -> str:
        column_widths = []
        # Compute width of each column
        for line in lines:
            for i, v in enumerate(line):
                if i == len(column_widths):
                    column_widths.append(0)
                if (cell_length := len(v)) > column_widths[i]:
                    column_widths[i] = cell_length

        row_sep = '+' + '+'.join('-' * (2 + w) for w in column_widths) + '+\n'
        res = row_sep
        for i, line in enumerate(lines):
            table_line = '|'
            for j, w in enumerate(column_widths):
                v = line[j] if j < len(line) else ''
                v += ' ' * (w - len(v))
                table_line += f' {v} |'
            res += table_line + '\n'
            if self._has_header and i == 0 or i == len(lines) - 1:
                res += row_sep
        return res[:-1]  # Remove trailing \n
