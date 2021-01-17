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

from queue import Queue, Empty
from time import sleep

class MockDevice(object):
    """ECU physical-layer communication encapsulation/interface"""

    def __init__(self, delay=100):
        self._delay = delay
        self._read_q = Queue()

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

    def enqueue_response(self, length):
        self._read_q.put_nowait(os.urandom(length))

    @property
    def Initialized(self):
        return True
