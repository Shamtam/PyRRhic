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

import struct

from PyJ2534 import IoctlParameter, ProtocolFlags

from ... import _debug
from ...common.enums import (
    DataType, LogParamType, LoggerEndpoint, LoggerProtocol,
    _dtype_size_map, _dtype_struct_map
)
from ..phy.j2534 import J2534PassThru_ISO9141
from .base import EndpointProtocol, LogQuery, LogQueryParseError

_ssm_endpoint_map = {
    LoggerEndpoint.ECU : b'\x10',
    LoggerEndpoint.TCU : b'\x18',
}

class SSMProtocol(EndpointProtocol):

    def __init__(self, *args):
        super(SSMProtocol, self).__init__(*args)
        self._protocol = LoggerProtocol.SSM

    def read_block(self, addr, num_bytes, continuous=False):
        """SSM `A0` block-read request

        If `continuous == False`, this will return a `bytes` containing
        the endpoint response, with the SSM header and checksum bytes
        stripped off. Otherwise, returns `None`.

        Arguments:
        - `addr`: `int` containing the address to start read from
        - `num_bytes`: `int` specifying number of bytes to read

        Keywords:
        - `continuous` [`False`]: instruct the endpoint to respond until
            it is interrupted
        """
        raise NotImplementedError

    def read_addresses(self, addr_list, continuous=False):
        """SSM `A8` read request

        If `continuous == False`, this will return a `bytes` containing
        the endpoint response, with the SSM header and checksum bytes
        stripped off. Otherwise, returns `None`.

        Arguments:
        - `addr_list`: `list` of `int` specifying byte addresses to read

        Keywords:
        - `continuous` [`False`]: instruct the endpoint to respond until
            it is interrupted
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

    _supported_phy = set([J2534PassThru_ISO9141])
    _phy_kwargs = {
        J2534PassThru_ISO9141: {
            'baud': 4800,
            'flags': ProtocolFlags.ISO9141_NO_CHECKSUM,
            'ioctl': {
                IoctlParameter.P1_MAX: 1000,
                IoctlParameter.P3_MIN: 0,
                IoctlParameter.P4_MIN: 0,
            },
        }
    }

    def __init__(self, *args, delay=100, timeout=5000):
        # ensure physical interface and protocol are compatible
        phy_cls = args[1]
        if not phy_cls in self._supported_phy:
            raise ValueError(
                'Unsupported physical interface {} for protocol {}'.format(
                    phy_cls.__name__, self.__class__.__name__
                )
            )

        super(SSM_ISO9141, self).__init__(*args)
        interface_name = args[0]
        self._phy = phy_cls(interface_name, **self._phy_kwargs[phy_cls])
        self._delay = delay
        self._timeout = timeout

        if not self._phy.Initialized:
            self._phy.initialize()

    def _append_checksum(self, message):
        return message + bytes([sum(message) & 0xff])

    def _construct_message(self, dest, command, data=b''):
        """Construct an SSM packet.

        Arguments:
        - `dest`: `LoggerEndpoint` indicating the destination device
        - `command`: `bytes` containing the command byte

        Keywords [Default]:
        - `data` [`b''`]: `bytes` containing message data
        """
        if len(data) > 254:
            raise ValueError('Maximum SSM packet data length is 254 bytes')

        len_byte = bytes([len(data) + 1])
        return self._append_checksum(
            b'\x80'                 # SSM start byte
            + _ssm_endpoint_map[dest] # destination byte
            + b'\xF0'               # source byte
            + len_byte              # payload length byte
            + command               # command byte
            + data                  # payload byte(s)
        )

    def _validate_response(self, cmd, resp):
        """Validate whether the SSM response is valid for the given request

        Returns `True` if the given response is valid, `False` otherwise.
        Pass in the raw message sent/recieved from the ecu (with the header
        and the checksum bytes).

        For SSM protocol, the command byte will be OR'd with `0x40` when
        the target accepts the request and returns a valid response.

        For example, if sending an ECU read block request (`0xA0`), if
        the request is successful, the ECU's response command byte
        will be `0xA0 | 0x40 = 0xE0`.

        Arguments:
        - `cmd`: `bytes` containing the original raw request to the target
        - `resp`: `bytes` containing the target's raw response
        """
        return cmd[4] ^ resp[4] == 0x40

    def check_logger_response(self):
        resp = self._phy.read(num_msgs=2, timeout=self._timeout)
        return self._strip_response(resp)

    def identify_endpoint(self, endpoint):
        # TODO: write interrupt
        msg = self._construct_message(endpoint, b'\xBF')
        resp = self._phy.query(
            msg, num_msgs=2, timeout=self._timeout, delay=self._delay
        )
        if resp:
            resp = self._strip_response(resp)
            identifier = resp[3:8].hex().upper()
            return (identifier, resp)
        else:
            return None

    def read_block(self, dest, addr, num_bytes, continuous=False):
        payload = (
            b'\x01' if continuous else b'\x00'
            + (addr & 0xffffff).to_bytes(3, 'big')
            + bytes([num_bytes - 1])
        )
        msg = self._construct_message(dest, b'\xA0', payload)

        if continuous:
            self._phy.write(msg, timeout=self._timeout)
        else:
            resp = self._phy.query(
                msg, num_msgs=2, timeout=self._timeout, delay=self._delay
            )
            return self._strip_response(resp)

    def read_addresses(self, dest, addr_list, continuous=False):
        payload = (
            (b'\x01' if continuous else b'\x00')
            + b''.join([(x & 0xffffff).to_bytes(3, 'big') for x in addr_list])
        )
        msg = self._construct_message(dest, b'\xA8', payload)

        if continuous:
            self._phy.write(msg, timeout=self._timeout)
        else:
            resp = self._phy.query(
                msg, num_msgs=2, timeout=self._timeout, delay=self._delay
            )
            return self._strip_response(resp)

    def write_block(self, dest, addr, data):
        payload = (addr & 0xffffff).to_bytes(3, 'big') + data
        msg = self._construct_message(dest, b'\xB0', payload)
        self._phy.write(msg, timeout=self._timeout)

    def write_address(self, dest, addr, data):
        payload = (addr & 0xffffff).to_bytes(3, 'big') + data
        msg = self._construct_message(dest, b'\xB8', payload)
        self._phy.write(msg, timeout=self._timeout)

    def _strip_response(self, msg):
        "Strip the SSM header and checksum bytes from a response"
        if msg:
            if len(msg) > 5:
                return msg[5:-1]

class SSMQuery(LogQuery):
    """SSM fast-poll (continuous read) query"""

    _max_request = 0xFF // 3 # need 3 bytes for each address in SSM A8 request

    def __init__(self, params):
        super(SSMQuery, self).__init__(params)
        self._addr_map = {}

    def generate_request(self):
        self._addr_map = {}

        switches = filter(
            lambda x: x.ParamType == LogParamType.SWITCH,
            self._params
        )
        params = filter(
            lambda x: x.ParamType in (
                LogParamType.STD_PARAM, LogParamType.EXT_PARAM
            ),
            self._params
        )

        # add switch addresses
        for s in switches:
            for a in s.Addresses:
                if a not in self._addr_map:
                    self._addr_map[a] = None

        # add parameter addresses
        for p in params:
            for base_addr in p.Addresses:
                psize = _dtype_size_map[p.Datatype]
                for a in range(base_addr, base_addr + psize):
                    if a not in self._addr_map:
                        self._addr_map[a] = None

        func = 'read_addresses'
        args = list(self._addr_map.keys())
        kwargs = {'continuous': True}
        return (func, args, kwargs, True)

    def extract_values(self, resp):
        if not len(resp) == len(self._addr_map):
            raise LogQueryParseError(
                'Unexpected response, mismatch between number of bytes in '
                'response and expected query length'
            )

        # map response string bytes into address map
        for a in self._addr_map:
            self._addr_map[a] = resp[0:1]
            resp = resp[1:]

        # populate values into params
        for p in self._params:

            if p.ParamType == LogParamType.SWITCH:
                addr = p.Addresses[0]
                raw_byte = self._addr_map[addr]
                bit = p.Datatype
                val = int.from_bytes(raw_byte, 'big') >> bit & 0x01 # TODO: implement byteorder in Param
                p.Value = val

            elif p.ParamType in [LogParamType.STD_PARAM, LogParamType.EXT_PARAM]:
                psize = _dtype_size_map[p.Datatype]
                addrs = []
                if len(p.Addresses) == psize:
                    addrs = p.Addresses
                elif len(p.Addresses) == 1:
                    base_addr = p.Addresses[0]
                    addrs = range(base_addr, base_addr + psize)

                if addrs:
                    unpack_key = _dtype_struct_map[p.Datatype]
                    raw_bytes = b''.join([self._addr_map[a] for a in addrs])
                    val = struct.unpack(unpack_key, raw_bytes)[0]
                    p.Value = val

protocols = {
    'SSM (K-line)': (SSM_ISO9141, SSMQuery)
}
