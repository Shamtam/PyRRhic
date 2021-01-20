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

from ....common.helpers import PyrrhicWorker
from ....comms.phy.base import CommunicationDevice
from queue import Queue, Empty
from time import sleep

class MockResponseWorker(PyrrhicWorker):
    def __init__(self, device, delay, length):
        super(MockResponseWorker, self).__init__()
        self._device = device
        self._delay = delay
        self._length = length

    def run(self):
        while not self._stoprequest.is_set():
            self._device.ReadQueue.put_nowait(os.urandom(self._length))
            sleep(self._delay*1e-3)

class MockDevice(CommunicationDevice):
    """ECU physical-layer communication encapsulation/interface"""

    def __init__(self, delay=100):
        self._delay = delay
        self._read_q = Queue()
        self._worker = None

    def initialize(self, *args, **kwargs):
        pass

    def terminate(self):
        pass

    def read(self, num_msgs=1):
        out = b''
        while len(out) < num_msgs:
            try:
                b = self._read_q.get_nowait()
                out += b
            except Empty:
                break

        return out if len(out) else None

    def write(self):
        pass

    def query(self, num_msgs=1):
        return self.read(num_msgs=num_msgs)

    def clear_rx_buffer(self):
        with self._read_q.mutex:
            self._read_q.queue.clear()

    def clear_tx_buffer(self):
        pass

    def begin_continuous_responses(self, delay, length):
        """Spawn a thread to continuously generate mock responses

        Arguments:
        `delay`: delay in ms between generated responses
        `length`: length of each generated response
        """
        self.interrupt_continuous_responses()
        self._worker = MockResponseWorker(self, delay, length)
        self._worker.start()

    def interrupt_continuous_responses(self):
        if self._worker is not None:
            self._worker.join()
            self.clear_rx_buffer()
            self._worker = None

    @property
    def Initialized(self):
        return True

    @property
    def ReadQueue(self):
        return self._read_q
