import math
import typing as typ

from .. import _core


class HaversineDist(_core.Operation):
    """Compute the Haversine distance in meters between two GPS coordinates."""

    def __init__(self, coords_sep: str = '\n', latlon_sep: str = ','):
        """Create a haversine_dist operation.

        :param coords_sep: Coordinates separator.
        :param latlon_sep: Latitude/longitude separator.
        """
        self._coords_sep = coords_sep
        self._latlon_sep = latlon_sep

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'coords_sep': self._coords_sep,
            'latlon_sep': self._latlon_sep,
        }

    def apply(self, s: str) -> str:
        coord1, coord2 = s.split(self._coords_sep, maxsplit=1)
        lat1, lon1 = self._latlon(coord1)
        lat2, lon2 = self._latlon(coord2)
        lats = self._sin_sq(lat1, lat2)
        lons = self._sin_sq(lon1, lon2)
        earth_diameter = 12_742_000
        dist = earth_diameter * math.asin(math.sqrt(lats + math.cos(lat1) * math.cos(lat2) * lons))
        return str(dist)

    def _latlon(self, coord: str) -> tuple[float, float]:
        # noinspection PyTypeChecker
        return tuple(math.radians(float(s)) for s in coord.split(self._latlon_sep, maxsplit=1))

    @staticmethod
    def _sin_sq(comp1, comp2):
        return math.sin((comp2 - comp1) / 2) ** 2
