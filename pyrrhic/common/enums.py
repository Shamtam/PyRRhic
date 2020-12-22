#   Copyright (C) 2020  Shamit Som <shamitsom@gmail.com>
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

from enum import Enum, Flag, auto

class UserLevel(Enum):
    BEGINNER        = 1
    INTERMEDIATE    = 2
    ADVANCED        = 3
    DEVELOPER       = 4
    SUPERDEV        = 5 # not listed in ECUFlash GUI, but used in XMLs

class DataType(Enum):
    UINT8   = auto()
    UINT16  = auto()
    UINT32  = auto()
    INT8    = auto()
    INT16   = auto()
    INT32   = auto()
    FLOAT   = auto()
    BLOB    = auto()

_dtype_size_map = {
    DataType.UINT8:  1,
    DataType.UINT16: 2,
    DataType.UINT32: 4,
    DataType.INT8:   1,
    DataType.INT16:  2,
    DataType.INT32:  4,
    DataType.FLOAT:  4,
    DataType.BLOB:   None    # shouldn't ever be used
}

_ecuflash_to_dtype_map = {
    'uint8'     : DataType.UINT8,
    'uint16'    : DataType.UINT16,
    'uint32'    : DataType.UINT32,
    'int8'      : DataType.INT8,
    'int16'     : DataType.INT16,
    'int32'     : DataType.INT32,
    'float'     : DataType.FLOAT,
    'bloblist'  : DataType.BLOB,
}

# these map to the corresponding jump offsets used in a Subaru ROM
class TableDataType(Enum):
    DATA_4B = 0x00
    DATA_2B = 0x04
    DATA_1B = 0x08
    DATA_U1 = 0x0C # not sure what/if these are ever used
    DATA_U2 = 0x10 # not sure what/if these are ever used

class ByteOrder(Enum):
    BIG_ENDIAN = auto()
    LITTLE_ENDIAN = auto()
