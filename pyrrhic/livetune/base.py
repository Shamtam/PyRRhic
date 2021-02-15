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

    COUNT           = auto()
    HEADERS         = auto()
    TABLES          = auto()
    INITIALIZED     = COUNT | HEADERS | TABLES

    PEND_ALLOCATE   = auto()
    PEND_ACTIVATE   = auto()

class LiveTuneData(object):
    def __init__(self, rom, ram_size):
        self._rom = rom
        self._ram_size = ram_size
        self._allocated_tables = []

    def __repr__(self):
        return '<{} {}/{} {}>'.format(
            type(self).__name__,
            self.AllocatedSize,
            self.TotalSize,
            self.State
        )

    @property
    def ROM(self):
        """`Rom` instance"""
        return self._rom

    @property
    def AllocatedSize(self):
        if any([x is None for x in self._allocated_tables]):
            return None
        return sum([t.NumBytes for t in self._allocated_tables if t is not None])

    @property
    def TotalSize(self):
        return self._ram_size

    @property
    def Tables(self):
        return self._allocated_tables

    @property
    def State(self):
        raise NotImplementedError
