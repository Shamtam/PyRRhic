#   Copyright (C) 2021  Shamit Som <shamitsom@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

from ... import _debug
from .j2534 import phys as j2534_phys

def get_all_interfaces():
    """Get all interfaces available on the system.

    Returns a `dict` with {`str`: `set`} key-val pairs, where the keys
    are the name of each interface on the machine, and the values are
    a `set` of the valid `CommunicationDevice` subclasses supported by
    the given interface.
    """
    ifaces = {}

    ifaces.update(j2534_phys)

    if _debug:
        from ...tests.comms.phy.phy_mock import MockDevice
        ifaces.update({'Mock Interface': set([MockDevice])})

    return ifaces
