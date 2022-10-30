import json
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
        :param strict: Whether to allow lines with varying numbers of values.
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
        }

    def apply(self, s: str) -> str:
        objects = None
        lines = s.split('\n')
        match self._mode:
            case self._ARRAYS:
                objects = self._to_arrays(lines)
            case self._DICTS:
                objects = self._to_dicts(lines)
            case self._DICT_OF_ARRAYS:
                objects = self._to_dict_of_arrays(lines)
        return json.dumps(objects)

    def _to_arrays(self, lines: list[str]) -> list[list[str]]:
        data = []
        for i, line in enumerate(lines):
            values = self._parse_line(line)
            if self._strict and i > 0 and (len1 := len(data[-1])) != (len2 := len(values)):
                self._error(len1, len2, i)
            data.append(values)
        return data

    def _to_dicts(self, lines: list[str]) -> list[dict[str, str]]:
        data = []
        header = []
        for i, line in enumerate(lines):
            values = self._parse_line(line, no_parsing=i == 0)
            if i == 0:
                header = values
            else:
                header_size = len(header)
                row_size = len(values)
                if self._strict and header_size != row_size:
                    self._error(header_size, row_size, i)
                data.append({header[j]: v for j, v in enumerate(values[:header_size])})
        return data

    def _to_dict_of_arrays(self, lines: list[str]) -> dict[str, list[str]]:
        data = {}
        header = []
        for i, line in enumerate(lines):
            values = self._parse_line(line, no_parsing=i > 0)
            if i == 0:
                header = values
                data = {k: [] for k in values}
            else:
                header_size = len(header)
                row_size = len(values)
                if self._strict and header_size != row_size:
                    self._error(header_size, row_size, i)
                for j, v in enumerate(values[:header_size]):
                    data[header[j]].append(v)
        return data

    def _parse_line(self, line: str, no_parsing: bool = False) -> list[str]:
        # TODO allow double quotes and parse values
        return line.split(self._value_sep)

    def _error(self, expected_len: int, actual_len: int, index: int):
        raise ValueError(f'row #{index} has length {actual_len}, expected {expected_len}')
