import abc
import csv
import io
import json
import re
import typing as typ

from .. import _core


class _CsvJson(_core.Operation, abc.ABC):
    """Base class for CSV/JSON operations."""

    def __init__(self, sep: str = ',', quote: str = '"'):
        """Create a CSV/JSON operation.

        :param sep: CSV values separator.
        :param quote: CSV quoting character.
        """
        self._value_sep = sep
        self._quote = quote

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'value_sep': self._value_sep,
            'quote': self._quote,
        }


class CsvToJson(_CsvJson):
    """Convert a CSV file into JSON."""

    ARRAYS = 'arrays'
    DICTS = 'dicts'
    DICT_OF_ARRAYS = 'dict_of_arrays'

    def __init__(self, sep: str = ',', quote: str = '"', mode: str = DICT_OF_ARRAYS,
                 parse_values: bool = False, strict: bool = False):
        """Create a csv_to_json operation.

        :param sep: CSV values separator.
        :param quote: CSV quoting character.
        :param mode: Either 'arrays', 'dicts' or 'dict_of_arrays'.
        :param parse_values: Whether to try to parse values, i.e. numbers and empty values.
        :param strict: Whether to allow lines to have more values than the header.
        """
        if mode not in (self.ARRAYS, self.DICTS, self.DICT_OF_ARRAYS):
            raise ValueError(f'invalid mode: {mode!r}')
        super().__init__(sep=sep, quote=quote)
        self._mode = mode
        self._parse_values = parse_values
        self._strict = strict

    def get_params(self) -> dict[str, typ.Any]:
        return {
            **super().get_params(),
            'mode': self._mode,
            'parse_values': self._parse_values,
            'strict': self._strict,
        }

    def apply(self, s: str) -> str:
        with io.StringIO(s) as f:
            parsed_csv = csv.DictReader(f, delimiter=self._value_sep, quotechar=self._quote)
            objects = None
            match self._mode:
                case self.ARRAYS:
                    objects = self._to_arrays(parsed_csv)
                case self.DICTS:
                    objects = self._to_dicts(parsed_csv)
                case self.DICT_OF_ARRAYS:
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


class JsonToCsv(_CsvJson):
    """Convert a JSON object to CSV format. If a row features more columns than declared in the header,
    additional values will be discarded from the resulting CSV data."""

    def apply(self, s: str) -> str:
        json_object = json.loads(s)
        if not json_object:
            return ''
        # Reformat JSON data
        match self._detect_json_format(json_object):
            case CsvToJson.ARRAYS:
                header, data = self._from_arrays(json_object)
            case CsvToJson.DICTS:
                header, data = self._from_dicts(json_object)
            case CsvToJson.DICT_OF_ARRAYS:
                header, data = self._from_dict_of_dicts(json_object)
            case _:
                raise ValueError('invalid JSON format')
        # Convert to CSV
        with io.StringIO() as file:
            writer = csv.DictWriter(file, fieldnames=header, delimiter=self._value_sep, quotechar=self._quote)
            writer.writeheader()
            writer.writerows(data)
            return file.getvalue().strip()

    @staticmethod
    def _detect_json_format(o: dict | list) -> str | None:
        if isinstance(o, list):
            if all(isinstance(e, list) for e in o):
                return CsvToJson.ARRAYS
            if all(isinstance(e, dict) for e in o):
                return CsvToJson.DICTS
        if isinstance(o, dict) and all(isinstance(k, str) and isinstance(v, list) for k, v in o.items()):
            return CsvToJson.DICT_OF_ARRAYS
        return None

    @staticmethod
    def _bool_to_str(v):
        return str(v).lower() if isinstance(v, bool) else v

    def _from_arrays(self, json_object: list[list[str]]) -> tuple[list[str], list[dict[str, str]]]:
        header = json_object[0]
        data = []
        for row in json_object[1:]:
            if len(row) < len(header):
                # Pad lines with not enough values
                row.extend([''] * (len(header) - len(row)))
            data.append(dict(zip(header, map(self._bool_to_str, row))))
        return header, data

    def _from_dicts(self, json_object: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]]]:
        header = []
        data = []
        for entry in json_object:
            data.append({})
            for k, v in entry.items():
                if k not in header:
                    header.append(k)
                data[-1][k] = self._bool_to_str(v)
        return header, data

    def _from_dict_of_dicts(self, json_object: dict[str, list[str]]) -> tuple[list[str], list[dict[str, str]]]:
        header = list(json_object.keys())
        data = []
        for k, values in json_object.items():
            for i, v in enumerate(values):
                if i == len(data):
                    data.append({})
                data[i][k] = self._bool_to_str(v)
        return header, data
