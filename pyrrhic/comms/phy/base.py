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

class CommunicationDevice(object):
    """ECU physical-layer communication encapsulation/interface"""

    def __init__(self, interface_name, **kwargs):
        """Open and configure the physical device layer

        Arguments:
        - `interface_name`: `str` containing the interface name, as it
            appears in the global interface dictionary key
        """
        self._initialized = False
        self._delay = kwargs.pop('delay', 100)
        self._timeout = kwargs.pop('timeout', 5000)

    def initialize(self, *args, **kwargs):
        "Initialize the physical layer connection"
        raise NotImplementedError

    def terminate(self):
        "Terminate the physical layer connection"
        raise NotImplementedError

    def read(self, num_msgs=1, timeout=None):
        "Read `num_msgs` messages"
        raise NotImplementedError

    def write(self, msg_bytes, timeout=None):
        "Write the given bytes"
        raise NotImplementedError

    def query(self, msg_bytes, num_msgs=1000, timeout=None, delay=500):
        """Convenience command to write then read from the channel.

        Writes `msg_bytes` to the channel, then waits `delay` ms, then
        reads `num_msgs` from the channel. `timeout` is passed to `read`
        and `write` and indicates the timeout in ms that is used.
        """
        raise NotImplementedError

    def clear_rx_buffer(self):
        "Clear the receive buffer"
        raise NotImplementedError

    def clear_tx_buffer(self):
        "Clear the transmit buffer"
        raise NotImplementedError

    def clear_buffers(self):
        "Convenience method to clear both Tx and Rx buffers"
        self.clear_rx_buffer()
        self.clear_tx_buffer()

    @property
    def Initialized(self):
        return self._initialized
