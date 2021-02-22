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
import struct

from ....common.enums import LoggerEndpoint, LoggerProtocol
from ....comms.protocol.ssm import SSMProtocol
from ..phy.phy_mock import MockDevice

_ssm_endpoint_map = {
    LoggerEndpoint.ECU : b'\x10',
    LoggerEndpoint.TCU : b'\x18',
}

class MockSSM(SSMProtocol):

    _supported_phy = set([MockDevice])

    def __init__(
        self, *args,
        ecu_id='4b12785207',
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
        super(MockSSM, self).__init__(*args)
        self._protocol = LoggerProtocol.SSM
        self._ecu_id = ecu_id
        self._delay = continuous_delay
        self._phy = MockDevice()

        self._ramtune_start = ramtune_start # Max Tables address
        self._ramtune_end = ramtune_end # RAMhole end
        self._ramtune_bytes = bytearray(
            b'\x00'*(self._ramtune_end - self._ramtune_start)
        )

        # # initialized to have one allocated table
        # # DBW Sport requested torque table, scaled down by 0.5
        # self._ramtune_bytes[0:4] = b'\x00\x00\x00\x00'
        # self._ramtune_bytes[4:8] = b'\x00\x00\x00\x01'
        # self._ramtune_bytes[8:12] = (0xdc5e4).to_bytes(4, 'big')
        # self._ramtune_bytes[12:16] = (ramtune_start + 16).to_bytes(4, 'big')
        # self._ramtune_bytes[16:510 + 16] = b'\x00\x00\x00\x00\x00\x00\x00\x01\x00\r\xc5\xa0\x00\xff\xb6X\x00\x00\x05\x00\x07\x80\x08\xc0\n\xe0\x10@\x14\xd3\x18@\x1d\x80\x1f\x80"\x80$@*#*jAK\x00\x00\x04@\x07\x80\x08\xc0\t\x80\r\r\x13@\x17S\x1d\x00!@(\xc0+@0\x180SK\xcc\x00\x00\x03\x80\x05\x00\x05\x07\x07\x00\t\xcd\x0f\x9a\x15M\x1c\x80!\xc0,@0\xc0677\\S\xad\x00\x00\x02\x00\x02\xc0\x03@\x04\xd3\x08\xb3\x0eS\x14S\x1c\x00"\x80-@1\xc0<\x00>\x80V \x00\x00\x01\x00\x02\x00\x03\x00\x04Z\x07\xd3\x0c\xe7\x12\x93\x1b\x80#\x80.\x803@B\xc0D\xc0W\x80\x00\x00\x00\x80\x01\xa0\x02\r\x03\xa0\x06\x87\n\xc0\x11@\x1b\x80$\x00/\x005@K\x80P\x00W\x80\x00\x00\x00@\x01@\x01\xc0\x03\x1a\x05\x9a\t:\x0e\x80\x1a@$@.\xc05@M\x00R\x80W\x80\x00\x00\x00\x10\x00\xc0\x01\x8d\x02\xba\x04\xe7\x08\x13\x0c\xb3\x19\x00#\x00.@3\xc0LMS\x00W\x80\x00\x00\x00\x10\x00\xad\x01`\x02m\x04Z\x07-\x0bG\x16\x80\x1f\xc0-\x002\x00K\xf3S@W\x80\x00\x00\x00\x10\x00\x9a\x01:\x02-\x03\xed\x06s\n\'\x14\x00\x1bZ+\x000\xc0K\xfbS\xc0W\x80\x00\x00\x00\x10\x00\x8d\x01 \x01\xfa\x03\x8d\x05\xe0\t:\x11\x80\x18Z\'\x00.\x80K\xa9S\x00W\x80\x00\x00\x00\x10\x00\x80\x01\x07\x01\xcd\x03G\x05`\x08z\x0e\x80\x15G$\x80+\x00J\xc0R\x80W\x80\x00\x00\x00\x10\x00s\x00\xf3\x01\xad\x03\x07\x04\xfa\x07\xd3\x0c\x80\x12\x80!\xc0\'sHFO\xb4W\x80\x00\x00\x00\x10\x00m\x00\xe0\x01\x8d\x02\xcd\x04\x9a\x07@\n\x80\x0f\xcd\x1f@$\xfaEpK\xfaW\x80\x00\x00\x00\x10\x00g\x00\xd3\x01s\x02\x9a\x04M\x06\xc7\t\x80\x0e3\x1cM!\xa0B\x03G\xc0W\x80\x00\x00\x00\x10\x00`\x00\xc7\x01Z\x02s\x04\x07\x06Z\x07\x80\x0c@\x18\xa0\x1e\xad>ZB\xc0U\xc6\x00\x00\x00\x10\x00`\x00\xc7\x01Z\x02s\x04\x07\x06Z\x07\x80\x0c@\r@\r\x80\r\xc0\x0e\x00\x0e@'

        self._check_ramtune = (lambda x: x in range(ramtune_start, ramtune_end))

    def check_receive_buffer(self):
        return self._phy.read()

    def identify_endpoint(self, endpoint):
        identifier = self._ecu_id.upper()
        capabilities = bytes.fromhex(
            'f3fac98e0b81feac00000066ce54f9b1e4001f200000000000dc00005d'
            '1f3080f0e6000043fb00f5c18600000001fdf180008180000000000000'
            '0000000000000000000000000000000000000000000000000000000000'
            '000000000000000000'
        )
        raw_ident_str = (
            b'\xa2\x10\x11' + bytes.fromhex(self._ecu_id) + capabilities
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
            out_bytes = bytearray(b'\x00'*len(addr_list))

            for idx, addr in enumerate(addr_list):
                if self._check_ramtune(addr):
                    out_bytes[idx] = self._ramtune_bytes[addr - self._ramtune_start]
                else:
                    out_bytes[idx:idx + 1] = os.urandom(1)

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
