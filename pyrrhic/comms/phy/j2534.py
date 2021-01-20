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

from time import sleep
from typing import Protocol

from PyJ2534 import *
from PyJ2534.error import J2534Error, J2534Errors

from .base import CommunicationDevice

class J2534PassThru(CommunicationDevice):
    "Encapsulation of a J2534 Pass-Thru device"

    def __init__(self, interface_name, protocol, baud, flags=0, ioctl={}, init=False):
        """Encapsulation initializer

        Arguments:
        - `interface_name`: `str` containing the name of the interface
            to open, as stored in the keys of the `dict` returned from
            the call to `PyJ2534.get_interfaces`
        - `protocol`: `ProtocolID` indicating the type of channel to open
        - `baud`: `int` indicating the channel baud rate

        Keywords [Default]:
        - `flags` [`0`] : `ProtocolFlags` specifying the flags to use
            when initializng the channel
        - `ioctl` [`{}`]: `dict` containing {`IoctlParameter`: Value} pairs to
            configure the channel upon initialization
        - `init` [`False`]: Initialize the interface immediately
        """
        self._iface_name = interface_name
        self._iface = load_interface(get_interfaces()[self._iface_name])
        self._devID = None
        self._chanID = None
        self._filterID = None
        self._protocol = protocol
        self._baud = baud
        self._flags = flags
        self._ioctl = ioctl
        self._initialized = False

        if init:
            self.initialize()

    def initialize(self):
        """Open the device and initialize a communication channel

        """
        if not self._initialized:

            # open the device
            self._devID = self._iface.PassThruOpen()

            # open channel
            args = (self._devID, self._protocol, self._flags, self._baud)
            self._chanID = self._iface.PassThruConnect(*args)

            # configure channel, disable loopback by default
            if IoctlParameter.LOOPBACK not in self._ioctl:
                self._ioctl[IoctlParameter.LOOPBACK] = 0
            self._iface.PassThruIoctlSetConfig(self._chanID, self._ioctl)

            # create a pass-all filter
            filter_msg = PASSTHRU_MSG(ProtocolID.ISO9141, data=b'\x00')
            self._filterID = self._iface.PassThruStartMsgFilter(
                self._chanID,
                FilterType.PASS_FILTER,
                mask_msg=filter_msg,
                pattern_msg=filter_msg
            )

            # clear buffers
            self._iface.PassThruIoctlClearRxBuffer(self._chanID)
            self._iface.PassThruIoctlClearTxBuffer(self._chanID)

            self._initialized = True

    def terminate(self):
        "Close the channel and the device"
        if self._initialized:
            if self._chanID is not None:
                self._iface.PassThruDisconnect(self._chanID)
                self._chanID = None

            self._iface.PassThruClose(self._devID)
            self._devID = None
            self._initialized = False

    @property
    def PassThruInterface(self):
        "Pass-Thru interface DLL wrapper"
        return self._iface

    @property
    def DeviceID(self):
        return self._devID

    @property
    def ChannelID(self):
        return self._chanID

class J2534PassThru_ISO9141(J2534PassThru):
    "J2534 Pass-Thru device configured for a ISO9141 channel"

    def __init__(self, interface_name, **kwargs):
        """Initializer

        See `J2534PassThru` base class for description `args` and `kwargs`.
        """
        baud = kwargs.pop('baud', 4800)
        super(J2534PassThru_ISO9141, self).__init__(
            interface_name, ProtocolID.ISO9141, baud, **kwargs
        )

    def read(self, num_msgs=2, timeout=None):

        if not self._initialized:
            raise RuntimeError('Interface is not initialized!')

        msgs = []
        try:
            msgs = self._iface.PassThruReadMsgs(
                self._chanID, num_msgs=num_msgs, timeout=timeout
            )
        except J2534Error as e:
            if e.error == J2534Errors.ERR_TIMEOUT:
                pass
        ret = None
        for msg in msgs:
            if msg.RxStatus == RxStatus.Normal:
                if ret is None:
                    ret = b''
                ret += msg.Data

        return ret

    def write(self, msg_bytes, timeout=None):

        if not self._initialized:
            raise RuntimeError('Interface is not initialized!')

        ptMsg = PASSTHRU_MSG(ProtocolID.ISO9141, data=msg_bytes)
        return self._iface.PassThruWriteMsgs(
            self._chanID, [ptMsg], timeout=timeout
        )

    def query(self, msg_bytes, num_msgs=2, timeout=None, delay=500):

        if not self._initialized:
            raise RuntimeError('Interface is not initialized!')

        # clear buffers
        self._iface.PassThruIoctlClearTxBuffer(self._chanID)
        self._iface.PassThruIoctlClearRxBuffer(self._chanID)

        # send request
        self.write(msg_bytes, timeout=timeout)

        # wait
        if delay is not None:
            sleep(delay*1e-3)

        # return response
        return self.read(num_msgs=num_msgs, timeout=timeout)

phys = {x: set([J2534PassThru, J2534PassThru_ISO9141]) for x in get_interfaces()}
