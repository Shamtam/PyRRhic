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

from enum import IntEnum
from PyJ2534 import IoctlParameter

from .base import ECUProtocol
from ...common.structures import LogParam
from ...common.enums import LoggerTarget
from ..phy.j2534 import J2534PassThru_ISO9141

class SSMTarget(IntEnum):
    LoggerTarget.ECU        = 0x10
    LoggerTarget.TCU        = 0x18
    LoggerTarget.ECU_TCU    = 0xf0

class SSMProtocol(ECUProtocol):

    def read_block(self, addr, num_bytes, continuous=False):
        """SSM `A0` block-read request

        Arguments:
        - `addr`: `int` containing the address to start read from
        - `num_bytes`: `int` specifying number of bytes to read

        Keywords:
        - `continuous` [`False`]: instruct ECU/TCU to respond until interrupted
        """
        raise NotImplementedError

    def read_addresses(self, addr_list, continuous=False):
        """SSM `A8` read request

        Arguments:
        - `addr_list`: `list` of `int` specifying byte addresses to read from

        Keywords:
        - `continuous` [`False`]: instruct the ECU/TCU to respond until interrupted
        """
        raise NotImplementedError

    def write_block(self, addr, data):
        """SSM `B0` block-write request

        Arguments:
        - `addr`: `int` containing the address to start write to
        - `data`: `bytes` containing data to write
        """
        raise NotImplementedError

    def write_address(self, addr, data):
        """SSM `B8` write request

        Arguments:
        - `addr`: `int` containing the address to write to
        - `data`: `bytes` containing the byte to write
        """
        raise NotImplementedError

class SSM_ISO9141(SSMProtocol):

    _supported_phy = (
        J2534PassThru_ISO9141
    )

    def __init__(self, phy, delay=100, timeout=5000):
        if not isinstance(phy, self._supported_phy):
            raise ValueError(
                'Unsupported physical interface {} for protocol {}'.format(
                    phy.__class__.__name__, self.__class__.__name__
                )
            )
        self._phy = phy
        self._delay = delay
        self._timeout = timeout

        if not self._phy.Initialized:
            self._phy.initialize(
                config={
                    IoctlParameter.P1_MAX: 1000,
                    IoctlParameter.P3_MIN: 0,
                    IoctlParameter.P4_MIN: 0,
                }
            )

    def _append_checksum(self, message):
        return message + bytes([sum(message) & 0xff])

    def _construct_message(self, dest, command, data=b''):
        """Construct an SSM packet.

        Arguments:
        - `dest`: `SSMTarget` indicating the destination device
        - `command`: `bytes` containing the command byte

        Keywords [Default]:
        - `data` [`b''`]: `bytes` containing message data
        """
        if len(data) > 254:
            raise ValueError('Maximum SSM packet data length is 254 bytes')

        len_byte = bytes([len(data) + 1])
        return self._append_checksum(
            b'\x80'                             # SSM start byte
            + bytes([dest, SSMTarget.DIAG])     # destination and source bytes
            + len_byte                          # payload length byte
            + command                           # command byte
            + data                              # payload byte(s)
        )

    def ecu_init(self):
        msg = self._construct_message(SSMTarget.ECU, b'\xBF')
        return self._phy.query(
            msg, num_msgs=2, timeout=self._timeout, delay=self._delay
        )

    def tcu_init(self):
        msg = self._construct_message(SSMTarget.TCU, b'\xBF')
        return self._phy.query(
            msg, num_msgs=2, timeout=self._timeout, delay=self._delay
        )

    def read_block(self, dest, addr, num_bytes, continuous=False):
        payload = (
            b'\x01' if continuous else b'\x00'
            + addr.to_bytes(3, 'big')
            + bytes([num_bytes - 1])
        )
        msg = self._construct_message(dest, b'\xA0', payload)
        return self._phy.query(
            msg, num_msgs=2, timeout=self._timeout, delay=self._delay
        )

    def read_addresses(self, dest, addr_list, continuous=False):
        payload = (
            (b'\x01' if continuous else b'\x00')
            + b''.join([x.to_bytes(3, 'big') for x in addr_list])
        )
        msg = self._construct_message(dest, b'\xA8', payload)
        return self._phy.query(
            msg, num_msgs=2, timeout=self._timeout, delay=self._delay
        )

    def write_block(self, dest, addr, data):
        payload = addr.to_bytes(3, 'big') + data
        msg = self._construct_message(dest, b'\xB0', payload)
        return self._phy.write(msg, timeout=self._timeout)

    def write_address(self, dest, addr, data):
        payload = addr.to_bytes(3, 'big') + data
        msg = self._construct_message(dest, b'\xB8', payload)
        return self._phy.write(msg, timeout=self._timeout)
