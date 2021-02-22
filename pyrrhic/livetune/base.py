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

from enum import IntFlag, auto

class LiveTuneState(IntFlag):
    UNINITIALIZED   = 0
    INITIALIZED     = auto()
    WRITE_PENDING   = auto()
    FINALIZE_WRITE  = auto()

class LiveTuneData(object):
    def __init__(self, rom, ram_size):
        self._rom = rom
        self._ram_size = ram_size
        self._ram_bytes = None
        self._bytes = None

    def __repr__(self):
        return '<{} {}/{} {}>'.format(
            type(self).__name__,
            self.AllocatedSize,
            self.TotalSize,
            self.State
        )

    def initialize(self, raw_bytes=None):
        """Initialize the instance with the raw bytes read from RAM.

        Keywords [Default]:
        `raw_bytes` [`None`]: `bytes` containing raw bytes of the
            complete section of RAM used for live tuning, or `None` to
            uninitialize the instance
        """
        if isinstance(raw_bytes, bytes):
            self._ram_bytes = bytearray(raw_bytes)
            self._bytes = self._ram_bytes[:]
        else:
            self._ram_bytes = None
            self._bytes = None

    def check_allocatable(self, table):
        raise NotImplementedError

    @property
    def ROM(self):
        """`Rom` instance"""
        return self._rom

    @property
    def TotalSize(self):
        return self._ram_size

    @property
    def AllocatedTables(self):
        """`dict` of `RamTable` currently allocated on the ECU, keyed
            by their ROM address."""
        raise NotImplementedError

    @property
    def AllocatedSize(self):
        raise NotImplementedError

    @property
    def State(self):
        raise NotImplementedError
