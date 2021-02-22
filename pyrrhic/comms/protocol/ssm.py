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

import logging
import struct

from itertools import groupby
from PyJ2534 import IoctlParameter, ProtocolFlags
from time import sleep

from ... import _debug
from ...common.enums import LoggerEndpoint, LoggerProtocol, _dtype_size_map
from ...livetune import LiveTuneState, MerpModLiveTune
from ..phy.j2534 import J2534PassThru_ISO9141
from .base import (
    EndpointProtocol, EndpointTranslator, TranslatorParseError
)

_logger = logging.getLogger(__name__)

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
                IoctlParameter.P1_MAX: 1,
                IoctlParameter.P3_MIN: 1,
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

        self._phy.initialize()

    def __del__(self):
        self._phy.terminate()

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

    def check_receive_buffer(self):
        resp = self._phy.read(num_msgs=2, timeout=self._timeout)
        return self._strip_response(resp)

    def identify_endpoint(self, endpoint):

        self.interrupt_endpoint(endpoint)

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

    def interrupt_endpoint(self, endpoint):
        self._phy.write(b'\xFF'*8, timeout=self._timeout)
        while self._phy.read():
            sleep(0.01)
        sleep(0.5)

    def read_block(self, dest, addr, num_bytes, continuous=False):
        payload = (
            b'\x01' if continuous else b'\x00'
            + (addr & 0xffffff).to_bytes(3, 'big')
            + bytes([num_bytes - 1])
        )
        msg = self._construct_message(dest, b'\xA0', payload)

        self._phy.write(msg, timeout=self._timeout)

    def read_addresses(self, dest, addr_list, continuous=False):
        payload = (
            (b'\x01' if continuous else b'\x00')
            + b''.join([(x & 0xffffff).to_bytes(3, 'big') for x in addr_list])
        )
        msg = self._construct_message(dest, b'\xA8', payload)

        self._phy.write(msg, timeout=self._timeout)

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

class SSMTranslator(EndpointTranslator):
    """SSM fast-poll (continuous read) translator"""

    # SSM A8 request max payload size
    # tested by trial and error on-car
    _max_read_payload = 0x52

    # SSM B0 request max payload size
    # tested by trial and error on-car
    _max_write_payload = 0xF6

    def __init__(self):
        super(SSMTranslator, self).__init__()
        self._addr_map = {}
        self._livetune = None

        self._livetune_query = None
        self._livetune_current_query = None

        self._livetune_write = None
        self._livetune_current_write = None

    def generate_log_request(self):
        self._check_def()

        self._addr_map = {}

        # add switch addresses
        for s in self.EnabledSwitches:
            for a in s.Addresses:
                if a not in self._addr_map:
                    self._addr_map[a] = None

        # add parameter addresses
        for p in self.EnabledParams:
            psize = _dtype_size_map[p.Datatype]
            addrs = []
            if len(p.Addresses) == psize:
                addrs = p.Addresses
            elif len(p.Addresses) == 1:
                base_addr = p.Addresses[0]
                addrs = range(base_addr, base_addr + psize)

            for a in addrs:
                if a not in self._addr_map:
                    self._addr_map[a] = None

        func = 'read_addresses'
        args = (list(self._addr_map.keys()), )
        kwargs = {'continuous': True}
        return (func, args, kwargs, True)

    def extract_values(self, resp):
        self._check_def()

        if not len(resp) == len(self._addr_map):
            raise TranslatorParseError(
                'Invalid response size. Received {}, expected {}'.format(
                    len(resp), len(self._addr_map)
                )
            )

        self._update_freq_avg()

        # map response string bytes into address map
        for a in self._addr_map:
            self._addr_map[a] = resp[0:1]
            resp = resp[1:]

        # populate switch values
        for s in self.EnabledSwitches:
            addr = s.Addresses[0]
            raw_byte = self._addr_map[addr]
            bit = s.Datatype

            # TODO: implement byteorder
            s.RawValue = (
                True if (int.from_bytes(raw_byte, 'big') >> bit) & 0x01
                else False
            )

        # populate param values
        for p in self.EnabledParams:
            psize = _dtype_size_map[p.Datatype]
            addrs = []
            if len(p.Addresses) == psize:
                addrs = p.Addresses
            elif len(p.Addresses) == 1:
                base_addr = p.Addresses[0]
                addrs = range(base_addr, base_addr + psize)

            if addrs:
                p.RawValue = b''.join([self._addr_map[a] for a in addrs])
            else:
                p.RawValue = None

    def generate_livetune_query(self):
        if not self._livetune:
            return

        # no previous query and pulling from ECU, generate necessary query
        if self._livetune_query is None and self._livetune_write is None:

            # live tuning not initialized, query state from ECU
            if not self._livetune.State & LiveTuneState.INITIALIZED:
                start_addr = 0xFFFFFF & self._livetune.StartAddress
                end_addr = 0xFFFFFF & self._livetune.EndAddress
                self._livetune_current_query = []
                self._livetune_query = {
                    k: None for k in range(start_addr, end_addr)
                }

        # no previous query, and verifying ECU write
        elif self._livetune_query is None and self._livetune_write is not None:
            self._livetune_current_query = []
            self._livetune_query = {k: None for k in self._livetune_write}

        # query is still incomplete
        if self._livetune_current_query is not None:

            # generate list of addresses from current query that have
            # not yet been read from the ECU
            undetermined_bytes = [
                t[0] for t in filter(
                    lambda x: x[1] is None,
                    self._livetune_query.items()
                )
            ]

            if undetermined_bytes:
                # ensure query does not exceed maximum request size
                self._livetune_current_query = \
                    undetermined_bytes[:self._max_read_payload]
            else:
                return

            func = 'read_addresses'
            args = (self._livetune_current_query, )
            kwargs = {}
            return (func, args, kwargs, False)
        else:
            return

    def generate_livetune_write(self):
        if not self._livetune:
            return

        # no previous write, generate necessary write
        if self._livetune_write is None:

            # no writes pending, clear any stored writes
            if not self._livetune.State & LiveTuneState.WRITE_PENDING:
                return

            else:
                final = (
                    True
                    if self._livetune.State & LiveTuneState.FINALIZE_WRITE
                    else False
                )
                self._livetune_write = self._livetune.get_modified_bytes(
                    force_deactivate=not final
                )
                self._livetune_current_write = {}

        if self._livetune_current_write is not None:

            unwritten_addrs = [
                t[0] for t in filter(
                    lambda x: x[1] is not None,
                    self._livetune_write.items()
                )
            ]

            # get first contiguous chunk of unwritten bytes
            if unwritten_addrs:
                key, group = next(
                    groupby(
                        enumerate(unwritten_addrs),
                        lambda x: x[0] - x[1]
                    )
                )
                chunk_addrs = [addr for idx, addr in group]

                # ensure write does not exceed maximum packet size
                chunk_addrs = chunk_addrs[:self._max_write_payload]
                chunk_data = b''.join([
                    self._livetune_write[x] for x in chunk_addrs
                ])

                self._livetune_current_write = {
                    a: d for a, d in zip(chunk_addrs, chunk_data)
                }

            # initial write complete, need to finalize
            elif self._livetune.State & LiveTuneState.FINALIZE_WRITE:
                self._livetune_write = self._livetune.get_modified_bytes(
                    force_deactivate=False
                )

            else:
                self._livetune_write = None
                self._livetune_current_write = None
                return

            write_func = 'write_block'
            write_args = (chunk_addrs[0], chunk_data)
            write_kwargs = {}
            write = (write_func, write_args, write_kwargs)

            verify_func = 'read_block'
            verify_args = (chunk_addrs[0], len(chunk_addrs))
            verify_kwargs = {'continuous': False}
            verify = (verify_func, verify_args, verify_kwargs)

            check = lambda x: x == chunk_data

            return write, verify, check
        else:
            return

    def validate_livetune_write(self):
        if not self._livetune:
            return

        if self._livetune_current_write:
            self._livetune.verify_write(self._livetune_current_write)
            self._livetune_write.update(
                {a: None for a in self._livetune_current_write}
            )

            # clear write if everything has been completed
            if all([x is None for x in self._livetune_write.values()]):
                self._livetune_write = None
                self._livetune_current_write = None

    def extract_livetune_state(self, resp):
        self._check_def()

        if self._livetune_current_query is None:
            raise TranslatorParseError('No current livetune query to parse')

        if not len(resp) == len(self._livetune_current_query):
            raise TranslatorParseError(
                'Invalid response size. Expected {}, received {}'.format(
                    len(resp), len(self._livetune_current_query)
                )
            )

        # update complete query with received bytes
        for idx, addr in enumerate(self._livetune_current_query):
            self._livetune_query[addr] = resp[idx:idx+1]

        complete = all(
            [x is not None for x in self._livetune_query.values()]
        )

        # current query complete, determine new state
        if complete:

            try:
                if not self._livetune.State & LiveTuneState.INITIALIZED:
                    raw_bytes = b''.join(self._livetune_query.values())
                    self._livetune.initialize(raw_bytes)

            except Exception as e:
                raise TranslatorParseError(str(e))

            else:
                self._livetune_query = None
                self._livetune_current_query = None

    def instantiate_livetune(self, rom):
        addrs = MerpModLiveTune.check_livetune_support(self._def)
        if addrs:
            args = (rom, *addrs)
            self._livetune = MerpModLiveTune(*args)
        else:
            self._livetune = None

    @property
    def SupportsLiveTune(self):
        return self._livetune is not None

    @property
    def LiveTuneData(self):
        return self._livetune

protocols = {
    'SSM (K-line)': (SSM_ISO9141, SSMTranslator)
}
