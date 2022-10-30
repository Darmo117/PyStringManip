import csv
import io
import json
import re
import typing as typ

from .. import _core


class CsvToJson(_core.Operation):
    """Convert a CSV file into JSON."""

    _ARRAYS = 'arrays'
    _DICTS = 'dicts'
    _DICT_OF_ARRAYS = 'dict_of_arrays'

    def __init__(self, value_sep: str = ',', mode: str = _DICT_OF_ARRAYS,
                 parse_values: bool = False, strict: bool = False):
        """Create a csv_to_json operation.

        :param value_sep: String to use to split values in a row.
        :param mode: Either 'arrays', 'dicts' or 'dict_of_arrays'.
        :param parse_values: Whether to try to parse values, i.e. numbers and empty values.
        :param strict: Whether to allow lines to have more values than the header.
        """
        if mode not in (self._ARRAYS, self._DICTS, self._DICT_OF_ARRAYS):
            raise ValueError(f'invalid mode: {mode!r}')
        self._value_sep = value_sep
        self._mode = mode
        self._parse_values = parse_values
        self._strict = strict

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'value_sep': self._value_sep,
            'mode': self._mode,
            'parse_values': self._parse_values,
            'strict': self._strict,
        }

    def apply(self, s: str) -> str:
        parsed_csv = csv.DictReader(io.StringIO(s), delimiter=self._value_sep, quotechar='"')
        objects = None
        match self._mode:
            case self._ARRAYS:
                objects = self._to_arrays(parsed_csv)
            case self._DICTS:
                objects = self._to_dicts(parsed_csv)
            case self._DICT_OF_ARRAYS:
                objects = self._to_dict_of_arrays(parsed_csv)
        return json.dumps(objects)

    def _to_arrays(self, lines: csv.DictReader) -> list[list[str]]:
        if not lines.fieldnames:
            return []
        data = [[self._parse_value(v) for v in lines.fieldnames]] if self._parse_values else [lines.fieldnames]
        for i, line in enumerate(lines):
            data.append([])
            for v in line.values():
                if isinstance(v, list):
                    data[-1].extend(map(self._parse_value, v))
                else:
                    data[-1].append(self._parse_value(v))
            if self._strict and (len1 := len(lines.fieldnames)) != (len2 := len(data[-1])):
                self._error(len1, len2, i)
        return data

    def _to_dicts(self, lines: csv.DictReader) -> list[dict[str, str]]:
        if not lines.fieldnames:
            return []
        header = lines.fieldnames
        if '' in header:
            raise ValueError('empty column name')
        if len(set(header)) != len(header):
            raise ValueError('duplicate column name')

        data = []
        for i, line in enumerate(lines):
            header_size = len(header)
            row_size = len(line)
            if self._strict and None in line:
                self._error(header_size, row_size + len(line[None]), i)
            data.append({k: self._parse_value(v) for k, v in line.items() if k is not None})

        return data

    def _to_dict_of_arrays(self, lines: csv.DictReader) -> dict[str, list[str]]:
        if not lines.fieldnames:
            return {}
        header = lines.fieldnames
        if '' in header:
            raise ValueError('empty column name')
        if len(set(header)) != len(header):
            raise ValueError('duplicate column name')

        data = {k: [] for k in lines.fieldnames}
        for i, line in enumerate(lines):
            header_size = len(header)
            row_size = len(line)
            if self._strict and None in line:
                self._error(header_size, row_size + len(line[None]), i)
            for k, v in line.items():
                if k is not None:
                    data[k].append(self._parse_value(v))

        return data

    _FLOAT_REGEX = re.compile(r'\d*\.\d+|\d+\.\d*')

    def _parse_value(self, value: str | None) -> str | int | float | bool | None:
        if not self._parse_values:
            return value or ''  # Replace None by ''
        match value:
            case None | '':
                return None
            case 'true':
                return True
            case 'false':
                return False
            case v if v.isascii() and v.isnumeric():
                return int(v)
            case v if self._FLOAT_REGEX.fullmatch(v):
                return float(v)
            case v:
                return v

    def _error(self, expected_len: int, actual_len: int, index: int):
        raise ValueError(f'row #{index + 2} has length {actual_len}, expected {expected_len}')
