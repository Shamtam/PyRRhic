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

from ....common.enums import LoggerEndpoint, LoggerProtocol
from ....comms.protocol.ssm import SSMProtocol, SSMTranslator
from ..phy.phy_mock import MockDevice


_ssm_endpoint_map = {
    LoggerEndpoint.ECU: b"\x10",
    LoggerEndpoint.TCU: b"\x18",
}


class MockSSM(SSMProtocol):

    _supported_phy = set([MockDevice])

    def __init__(
        self,
        *args,
        ecu_id="4b12785207",
        continuous_delay=50,
        ramtune_start=0xFFB648,
        ramtune_end=0xFFBCFF
    ):
        """Initialize a mock SSM protocol.

        Keywords [Default]:
        - `ecu_id` [`'4b12785207'`]: `str` representing the 5-byte ECU
            ID that this protocol instance should emulate
        - `continuous_delay` [`100`]: delay between updates when mocking
            a continuous read from this protocol, in milliseconds
        """
        super().__init__(*args)
        self._protocol = LoggerProtocol.SSM
        self._ecu_id = ecu_id
        self._delay = continuous_delay
        self._phy = MockDevice()

        self._ramtune_start = ramtune_start  # Max Tables address
        self._ramtune_end = ramtune_end  # RAMhole end
        self._ramtune_bytes = bytearray(
            b"\x00" * (self._ramtune_end - self._ramtune_start)
        )

        self._check_ramtune = lambda x: x in range(ramtune_start, ramtune_end)

    def check_receive_buffer(self):
        return self._phy.read()

    def identify_endpoint(self, endpoint):
        identifier = self._ecu_id.upper()
        capabilities = bytes.fromhex(
            "f3fac98e0b81feac00000066ce54f9b1e4001f200000000000dc00005d"
            "1f3080f0e6000043fb00f5c18600000001fdf180008180000000000000"
            "0000000000000000000000000000000000000000000000000000000000"
            "000000000000000000"
        )
        raw_ident_str = (
            b"\xa2\x10\x11" + bytes.fromhex(self._ecu_id) + capabilities
        )
        return (identifier, raw_ident_str)

    def interrupt_endpoint(self, endpoint):
        self._phy.interrupt_continuous_responses()

    def read_block(self, dest, addr, num_bytes, continuous=False):
        if continuous:
            self._phy.begin_continuous_responses(self._delay, num_bytes)
        else:
            if self._check_ramtune(addr):
                start_idx = addr - self._ramtune_start
                end_idx = start_idx + num_bytes
                b = bytes(self._ramtune_bytes[start_idx:end_idx])
                self._phy.queue_response(b)
            else:
                self._phy.queue_response(os.urandom(num_bytes))

    def read_addresses(self, dest, addr_list, continuous=False):

        if continuous:
            self._phy.begin_continuous_responses(self._delay, len(addr_list))

        else:
            out_bytes = bytearray(b"\x00" * len(addr_list))

            for idx, addr in enumerate(addr_list):
                if self._check_ramtune(addr):
                    out_bytes[idx] = self._ramtune_bytes[
                        addr - self._ramtune_start
                    ]
                else:
                    out_bytes[idx : idx + 1] = os.urandom(1)

            self._phy.queue_response(out_bytes)

    def write_block(self, dest, addr, data):
        self._phy.interrupt_continuous_responses()

        if self._check_ramtune(addr):
            start_idx = addr - self._ramtune_start
            end_idx = start_idx + len(data)
            self._ramtune_bytes[start_idx:end_idx] = data
            self._phy.queue_response(data)

    def write_address(self, dest, addr, data):
        self._phy.interrupt_continuous_responses()

        if self._check_ramtune(addr):
            idx = addr - self._ramtune_start
            self._ramtune_bytes[idx] = data
            self._phy.queue_response(data)


_protocols = {
    'Mock SSM': (MockSSM, SSMTranslator)
}
