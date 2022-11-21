import abc
import typing as typ

from .. import _core


class _ConvertUnits(_core.Operation, abc.ABC):
    """Base class for unit convertion operations."""

    def __init__(self, source: str, target: str, unit_coefs: dict[str, float]):
        """Create a unit converter.

        :param source: Source unit.
        :param target: Target unit.
        :param unit_coefs: Coefficients to go from a unit to the base unit.
        """
        self._source_unit = source
        self._target_unit = target
        self._unit_coefs = unit_coefs

    def get_params(self) -> dict[str, typ.Any]:
        return {
            'source': self._source_unit,
            'target': self._target_unit,
        }

    def apply(self, s: str) -> str:
        v = float(s)
        return str(v * self._unit_coefs[self._source_unit] / self._unit_coefs[self._target_unit])


class ConvertDistance(_ConvertUnits):
    """Convert a distance."""

    _COEFS = {
        # SI
        'qm': 1e-30,
        'rm': 1e-27,
        'ym': 1e-24,
        'zm': 1e-21,
        'am': 1e-18,
        'fm': 1e-15,
        'pm': 1e-12,
        'nm': 1e-9,
        'µm': 1e-6,
        'mm': 1e-3,
        'cm': 1e-2,
        'dm': 0.1,
        'm': 1,
        'dam': 10,
        'hm': 1e2,
        'km': 1e3,
        'Mm': 1e6,
        'Gm': 1e9,
        'Tm': 1e12,
        'Pm': 1e15,
        'Em': 1e18,
        'Zm': 1e21,
        'Ym': 1e24,
        'Rm': 1e27,
        'Qm': 1e30,
        # Imperial
        'th': 2.54e-5,  # 1/1000 in
        'in': 2.54e-2,
        'ft': 0.3048,  # 12 in
        'yd': 0.9144,  # 3 ft
        'fur': 201.168,  # 220 yd
        'mi': 1609.344,  # 1760 yd
        'lea': 4828.032,  # 3 mi
        # Nautical
        'ftm': 1.8288,
        'cable': 185.2,  # 1/10 nmi
        'nmi': 1852,
        # Physics
        'planck': 1.616_255e-35,
        'Å': 1e-10,
        # Astronomical
        'earth-moon': 384_399,
        'au': 149_597_870_700,
        'ly': 9_460_730_472_580_800,
        'pc': 30_856_775_814_913_673,
    }

    def __init__(self, source: str = 'm', target: str = 'm'):
        """Create a distance conversion operation.

        :param source: Source unit.
        :param target: Target unit.
        """
        super().__init__(source=source, target=target, unit_coefs=self._COEFS)


class ConvertArea(_ConvertUnits):
    """Convert an area."""

    _COEFS = {
        # SI
        'qm²': 1e-60,
        'rm²': 1e-54,
        'ym²': 1e-48,
        'zm²': 1e-42,
        'am²': 1e-36,
        'fm²': 1e-30,
        'pm²': 1e-24,
        'nm²': 1e-18,
        'µm²': 1e-12,
        'mm²': 1e-6,
        'cm²': 1e-4,
        'dm²': 1e-2,
        'm²': 1,
        'dam²': 1e2,
        'hm²': 1e4,
        'km²': 1e6,
        'Mm²': 1e12,
        'Gm²': 1e18,
        'Tm²': 1e24,
        'Pm²': 1e30,
        'Em²': 1e36,
        'Zm²': 1e42,
        'Ym²': 1e48,
        'Rm²': 1e54,
        'Qm²': 1e60,
        # ares
        'ca': 1,
        'da': 10,
        'a': 1e2,
        'daa': 1e3,
        'ha': 1e4,
        # Imperial
        'sq_in': 6.4516e-4,
        'sq_ft': 0.092_903_04,
        'sq_yd': 0.836_127_36,
        'sq_mi': 2_589_988.110_336,
        'ro': 1012,
        'ac': 4046.856_422_4,
        # Physics
        'qb': 1e-58,
        'rb': 1e-55,
        'yb': 1e-52,
        'zb': 1e-49,
        'ab': 1e-46,
        'fb': 1e-43,
        'pb': 1e-40,
        'nb': 1e-37,
        'µb': 1e-34,
        'mb': 1e-31,
        'b': 1e-28,
        'kb': 1e-25,
        'Mb': 1e-22,
        'planck': 2.6121e-70,
    }

    def __init__(self, source: str = 'm²', target: str = 'm²'):
        """Create an area conversion operation.

        :param source: Source unit.
        :param target: Target unit.
        """
        super().__init__(source=source, target=target, unit_coefs=self._COEFS)


class ConvertMass(_ConvertUnits):
    """Convert a mass."""

    _COEFS = {
        # SI
        'qg': 1e-30,
        'rg': 1e-27,
        'yg': 1e-24,
        'zg': 1e-21,
        'ag': 1e-18,
        'fg': 1e-15,
        'pg': 1e-12,
        'ng': 1e-9,
        'µg': 1e-6,
        'mg': 1e-3,
        'cg': 1e-2,
        'dg': 0.1,
        'g': 1,
        'dag': 10,
        'hg': 1e2,
        'kg': 1e3,
        'Mg': 1e6,
        'Gg': 1e9,
        'Tg': 1e12,
        'Pg': 1e15,
        'Eg': 1e18,
        'Zg': 1e21,
        'Yg': 1e24,
        'Rg': 1e27,
        'Qg': 1e30,
        # Usual
        'q': 1e2,  # Quintal
        't': 1e3,  # Tonne
        # Imperial (Avoirdupois)
        'gr': 64.798_91,  # Grain, exact value, same value in Troy system
        'dr': 1.771_845_195_312_5,  # Dram, exact value
        'oz': 28.349_523_125,  # Exact value
        'lb': 453.592_37,  # Exact value
        'st': 6350.293_18,  # Stone, 14 lb, exact value
        'qr': 177_808.209_04,  # Quarter, 28 lb, exact value
        'tod': 177_808.209_04,  # 1 quarter, exact value
        'cwt_us': 453_592.37,  # US hundredweight, 100 lb, exact value
        'cwt_imp': 50_802.345_44,  # Imperial hundredweight, 112 lb, exact value
        'ton_us': 907_184.74,  # 2000 lb, exact value
        'ton_imp': 1_016_046.9088,  # 2240 lb, exact value
        # Imperial (Troy)
        'dr_t': 3.887_934_6,  # Dram, exact value
        'dwt': 1.555_173_84,  # Pennyweight, exact value
        'oz_t': 31.103_476_8,  # Exact value
        'lb_t': 373.241_721_6,  # Exact value
        # Physics
        'planck': 2.176_434e-8,
        # Astronomical
        'earth': 5.9722e-24,
        'M⊕': 5.9722e-24,
        'moon': 5.9722e-24 / 81,
        'sun': 1.988_47e30,
        'M☉': 1.988_47e30,
    }

    def __init__(self, source: str = 'g', target: str = 'g'):
        """Create a mass conversion operation.

        :param source: Source unit.
        :param target: Target unit.
        """
        super().__init__(source=source, target=target, unit_coefs=self._COEFS)


class ConvertSpeed(_ConvertUnits):
    """Convert a speed."""

    _COEFS = {
        # SI
        'm/s': 1,
        'km/h': 1 / 3.6,
        # Imperial
        'mph': 0.447_04,  # Exact value
        'kn': 1.852 / 3.6,  # Knot
        # Scientific
        'sound_atm': 343,
        'sound_water': 1481,
        'c': 299_792_458,  # Speed of light, exact value
    }

    def __init__(self, source: str = 'm/s', target: str = 'm/s'):
        """Create a speed conversion operation.

        :param source: Source unit.
        :param target: Target unit.
        """
        super().__init__(source=source, target=target, unit_coefs=self._COEFS)


class ConvertDataUnit(_ConvertUnits):
    """Convert a data amount."""

    _COEFS = {
        # Base
        'b': 1,
        'B': 8,
        # Binary bits
        'Kib': 2 ** 10,
        'Mib': 2 ** 20,
        'Gib': 2 ** 30,
        'Tib': 2 ** 40,
        'Pib': 2 ** 50,
        'Eib': 2 ** 60,
        'Zib': 2 ** 70,
        'Yib': 2 ** 80,
        # Decimal bits
        'dab': 10,
        'hb': 1e2,
        'kb': 1e3,
        'Mb': 1e6,
        'Gb': 1e9,
        'Tb': 1e12,
        'Pb': 1e15,
        'Eb': 1e18,
        'Zb': 1e21,
        'Yb': 1e24,
        # Binary bytes
        'KiB': 2 ** 13,
        'MiB': 2 ** 23,
        'GiB': 2 ** 33,
        'TiB': 2 ** 43,
        'PiB': 2 ** 53,
        'EiB': 2 ** 63,
        'ZiB': 2 ** 73,
        'YiB': 2 ** 83,
        # Decimal bytes
        'daB': 80,
        'hB': 8e2,
        'kB': 8e3,
        'MB': 8e6,
        'GB': 8e9,
        'TB': 8e12,
        'PB': 8e15,
        'EB': 8e18,
        'ZB': 8e21,
        'YB': 8e24,
    }

    def __init__(self, source: str = 'b', target: str = 'b'):
        """Create a data unit conversion operation.

        :param source: Source unit.
        :param target: Target unit.
        """
        super().__init__(source=source, target=target, unit_coefs=self._COEFS)
