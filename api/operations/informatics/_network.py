import re

from .. import _core


class DefangIpAddresses(_core.Operation):
    """Defang all IPv4 and IPv6 addresses,
    i.e. make them invalid to remove the risk of accidently using them as IP addresses."""

    IPV4_REGEX = re.compile(
        r'((2(5[0-6]|[0-4]\d)|1?\d{2}|\d{1,2})\.){3}(2(5[0-6]|[0-4]\d)|1?\d{2}|\d{1,2})')
    # https://stackoverflow.com/a/17871737/3779986
    IPV6_REGEX = re.compile(r"""(
([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|            # 1:2:3:4:5:6:7:8
([0-9a-fA-F]{1,4}:){1,7}:|                         # 1::                              1:2:3:4:5:6:7::
([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|         # 1::8             1:2:3:4:5:6::8  1:2:3:4:5:6::8
([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|  # 1::7:8           1:2:3:4:5::7:8  1:2:3:4:5::8
([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|  # 1::6:7:8         1:2:3:4::6:7:8  1:2:3:4::8
([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|  # 1::5:6:7:8       1:2:3::5:6:7:8  1:2:3::8
([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|  # 1::4:5:6:7:8     1:2::4:5:6:7:8  1:2::8
[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|       # 1::3:4:5:6:7:8   1::3:4:5:6:7:8  1::8  
:((:[0-9a-fA-F]{1,4}){1,7}|:)|                     # ::2:3:4:5:6:7:8  ::2:3:4:5:6:7:8 ::8       ::     
fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]+| # fe80::7:8%eth0   fe80::7:8%1 (link-local IPv6 addresses with zone index)
::(ffff(:0{1,4})?:)?
((25[0-5]|(2[0-4]|1?[0-9])?[0-9])\.){3}
(25[0-5]|(2[0-4]|1?[0-9])?[0-9])|          # ::255.255.255.255   ::ffff:255.255.255.255  ::ffff:0:255.255.255.255
                                           # (IPv4-mapped IPv6 addresses and IPv4-translated addresses)
([0-9a-fA-F]{1,4}:){1,4}:
((25[0-5]|(2[0-4]|1?[0-9])?[0-9])\.){3}
(25[0-5]|(2[0-4]|1?[0-9])?[0-9])           # 2001:db8:3:4::192.0.2.33  64:ff9b::192.0.2.33 (IPv4-Embedded IPv6 Address)
)""", re.VERBOSE)

    def apply(self, s: str) -> str:
        s = self.IPV4_REGEX.sub(lambda m: m.group().replace('.', '[.]'), s)
        return self.IPV6_REGEX.sub(lambda m: m.group().replace(':', '[:]'), s)
