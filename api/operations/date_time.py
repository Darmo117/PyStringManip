import time
import typing as typ

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

    def get_params(self) -> typ.Dict[str, typ.Any]:
        return {
            'unit': self._unit,
        }

    def apply(self, s: str) -> str:
        return str(time.time_ns() // self._UNITS[self._unit])
