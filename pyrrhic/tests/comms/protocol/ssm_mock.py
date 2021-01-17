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

import os

from threading import Thread

from ....comms.protocol.base import ECUProtocol
from ....comms.phy import get_all_interfaces
from ....common.enums import LoggerEndpoint, LoggerProtocol
from ..phy.phy_mock import MockDevice

_ssm_endpoint_map = {
    LoggerEndpoint.ECU : b'\x10',
    LoggerEndpoint.TCU : b'\x18',
}

class MockSSM(ECUProtocol):

    _supported_phy = set([MockDevice])

    def __init__(self, *args, ecu_id='4b12785207', continuous_delay=100):
        """Initialize a mock SSM protocol.

        Keywords [Default]:
        - `ecu_id` [`'4b12785207'`]: `str` representing the 5-byte ECU
            ID that this protocol instance should emulate
        - `continuous_delay` [`100`]: delay between updates when mocking
            a continuous read from this protocol, in milliseconds
        """
        super(MockSSM, self).__init__(*args)
        self._protocol = LoggerProtocol.SSM
        self._ecu_id = ecu_id
        self._thread = None
        self._phy = MockDevice(delay=continuous_delay)

    def identify_endpoint(self, endpoint):
        identifier = self._ecu_id.upper()
        capabilities = bytes.fromhex(
            'f3fac98e0b81feac00000066ce54f9b1e4001f200000000000dc00005d'
            '1f3080f0e6000043fb00f5c18600000001fdf180008180000000000000'
            '0000000000000000000000000000000000000000000000000000000000'
            '000000000000000000'
        )
        raw_ident_str = b'\xa2\x10\x11' + bytes.fromhex(self._ecu_id) + capabilities
        return (
            self._protocol,
            endpoint,
            identifier,
            raw_ident_str
        )

    def read_block(self, dest, addr, num_bytes, continuous=False):
        if continuous:
            self._thread = Thread(
                endpoint=self._phy.enqueue_response, args=(num_bytes,)
            )
            self._thread.start()
            return 1
        else:
            return os.urandom(num_bytes)

    def read_addresses(self, dest, addr_list, continuous=False):
        self._phy.ReadSize = len(addr_list)
        if continuous:
            self._thread = Thread(
                endpoint=self._phy.enqueue_response, args=(len(addr_list),)
            )
            self._thread.start()
            return 1
        else:
            return os.urandom(len(addr_list))

    def write_block(self, dest, addr, data):
        if self._thread:
            self._thread.join()
        return 1

    def write_address(self, dest, addr, data):
        if self._thread:
            self._thread.join()
        return 1
