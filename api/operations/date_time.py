import abc
import datetime as dt
import math
import time
import typing as typ

import pytz

from . import _core


class GetTime(_core.Operation):
    """Get the current timestamp since UNIX epoch."""

    _UNITS = {
        's': 1_000_000_000,
        'ms': 1_000_000,
        'µs': 1000,
        'ns': 1,
    }

    def __init__(self, unit: str = 's'):
        """Create an operation that returns the current time.

        :param unit: The timestamp’s unit: 's' for seconds, 'ms' for milliseconds, 'µs' for microseconds,
         'ns' for nanoseconds.
        """
        if unit not in self._UNITS:
            raise ValueError(f'invalid granularity: {unit}')
        self._unit = unit

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'unit': self._unit,
        }

    def apply(self, s: str) -> str:
        return str(time.time_ns() // self._UNITS[self._unit])


class FromUnixTs(_core.Operation):
    """Convert a UNIX timestamp to a date-time string in the format 'YYYY-MM-DD HH:mm:ss±ZZ:ZZ'."""

    UNITS = {
        's': 1,
        'ms': 1e3,
        'µs': 1e6,
        'ns': 1e9,
    }

    def __init__(self, tz: str = 'UTC', unit: str = 's'):
        """Create a from_unix_ts operation.

        :param tz: Name of the timezone.
        :param unit: Timestamp’s unit, either 's', 'ms', 'µs' or 'ns'.
        """
        if unit not in self.UNITS:
            raise ValueError(f'invalid unit: {unit!r}')
        self._tz = tz or 'UTC'
        self._unit = unit

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'tz': self._tz,
            'unit': self._unit,
        }

    def apply(self, s: str) -> str:
        return str(dt.datetime.fromtimestamp(float(s) / self.UNITS[self._unit],
                                             tz=_tz(self._tz) if self._tz else None))


class _ParseDatetime(_core.Operation, abc.ABC):
    """Base class for operations that parse dates."""

    # noinspection PyShadowingBuiltins
    def __init__(self, format: str = '%Y-%m-%d', tz: str = 'UTC'):
        """Create a date-parsing operation.

        :param format: Date’s format.
        :param tz: Date’s timezone name.
        """
        self._format = format or 'UTC'
        self._tz = tz

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'format': self._format,
            'tz': self._tz,
        }

    def _parse(self, s: str) -> dt.datetime:
        return dt.datetime.strptime(s, self._format).replace(tzinfo=_tz(self._tz))


class ToUnixTs(_ParseDatetime):
    """Convert a date-time string as a UNIX timestamp."""

    # noinspection PyShadowingBuiltins
    def __init__(self, format: str = '%Y-%m-%d', tz: str = 'UTC', unit: str = 's'):
        """Create a to_unix_ts operation.

        :param format: Date’s format.
        :param tz: Date’s timezone name.
        :param unit: Timestamp’s unit, either 's', 'ms', 'µs' or 'ns'.
        """
        if unit not in FromUnixTs.UNITS:
            raise ValueError(f'invalid unit: {unit!r}')
        super().__init__(format=format, tz=tz)
        self._unit = unit

    def get_params(self) -> dict[str, typ.Any]:
        return {
            **super().get_params(),
            'unit': self._unit,
        }

    def apply(self, s: str) -> str:
        date = self._parse(s)
        return str(int(date.timestamp() * FromUnixTs.UNITS[self._unit]))


class ParseDatetime(_ParseDatetime):
    """Parse a date-time string."""

    def apply(self, s: str) -> str:
        date = self._parse(s)
        leap_year = date.year % 4 == 0 and date.year % 100 != 0 or date.year % 400 == 0
        return f"""\
Date: {date.strftime('%A %d %B %Y')}
Time: {date.strftime('%H:%M:%S')}
Period: {date.strftime('%p')}
Timezone: {date.tzname() or 'N/A'}
UTC offset: {date.strftime('%z')}

Leap year: {str(leap_year).lower()}
Days in month: {self._days_in_month(date.month, leap_year)}

Day of year: {date.timetuple().tm_yday}
Week number: {date.strftime('%U')}
Trimester: {math.ceil(date.month / 3)}
"""

    @staticmethod
    def _days_in_month(month: int, leap_year: bool):
        match month:
            case 1 | 3 | 5 | 7 | 8 | 10 | 12:
                return 31
            case 2 | 4 | 6 | 9 | 11:
                return 30
            case _ if leap_year:
                return 29
            case _:
                return 28


class ConvertDatetime(_ParseDatetime):
    """Convert a date-time representation into another."""

    # noinspection PyShadowingBuiltins
    def __init__(self, in_format: str = '%Y-%m-%d', in_tz: str = 'UTC',
                 out_format: str = '%Y-%m-%d', out_tz: str = 'UTC'):
        """Create a convert_datetime operation.

        :param in_format: Input date’s format.
        :param in_tz: Input date’s timezone name.
        :param out_format: Output date’s format.
        :param out_tz: Output date’s timezone name.
        """
        super().__init__(format=in_format, tz=in_tz)
        self._out_format = out_format
        self._out_tz = out_tz

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'in_format': self._format,
            'in_tz': self._tz,
            'out_format': self._out_format,
            'out_tz': self._out_tz,
        }

    def apply(self, s: str) -> str:
        date = self._parse(s).astimezone(tz=_tz(self._out_tz))
        return date.strftime(self._out_format)


def _tz(tzname: str) -> dt.tzinfo:
    """Create a tzinfo object for the given timezone name.

    :param tzname: Timezone’s name.
    :return: A tzinfo object.
    :raise ValueError: If the timezone name is not recognized.
    """
    try:
        return pytz.timezone(tzname) if tzname else pytz.timezone('UTC')
    except pytz.exceptions.UnknownTimeZoneError:
        raise ValueError(f'unknown timezone: {tzname!r}')
