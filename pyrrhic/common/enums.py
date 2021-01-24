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

from enum import IntEnum, auto

class UserLevel(IntEnum):
    Beginner        = 1
    Intermediate    = 2
    Advanced        = 3
    Developer       = 4
    Superdev        = 5 # not listed in ECUFlash GUI, but used in XMLs

class DataType(IntEnum):
    BIT0    = 0
    BIT1    = 1
    BIT2    = 2
    BIT3    = 3
    BIT4    = 4
    BIT5    = 5
    BIT6    = 6
    BIT7    = 7
    UINT8   = auto()
    UINT16  = auto()
    UINT32  = auto()
    INT8    = auto()
    INT16   = auto()
    INT32   = auto()
    FLOAT   = auto()
    BLOB    = auto()
    STATIC  = auto()

# `None` valued keys shouldn't ever be used
_dtype_size_map = {
    DataType.BIT0:   None,
    DataType.BIT1:   None,
    DataType.BIT2:   None,
    DataType.BIT3:   None,
    DataType.BIT4:   None,
    DataType.BIT5:   None,
    DataType.BIT6:   None,
    DataType.BIT7:   None,
    DataType.UINT8:  1,
    DataType.UINT16: 2,
    DataType.UINT32: 4,
    DataType.INT8:   1,
    DataType.INT16:  2,
    DataType.INT32:  4,
    DataType.FLOAT:  4,
    DataType.BLOB:   None,
    DataType.STATIC: None,
}

# `None` valued keys shouldn't ever be used
_dtype_struct_map = {
    DataType.BIT0:   None,
    DataType.BIT1:   None,
    DataType.BIT2:   None,
    DataType.BIT3:   None,
    DataType.BIT4:   None,
    DataType.BIT5:   None,
    DataType.BIT6:   None,
    DataType.BIT7:   None,
    DataType.UINT8:  'B',
    DataType.UINT16: 'H',
    DataType.UINT32: 'I',
    DataType.INT8:   'b',
    DataType.INT16:  'h',
    DataType.INT32:  'i',
    DataType.FLOAT:  'f',
    DataType.BLOB:   'B',
    DataType.STATIC: None,
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
_rrlogger_to_dtype_map = {
    'uint8'     : DataType.UINT8,
    'uint16'    : DataType.UINT16,
    'uint32'    : DataType.UINT32,
    'int8'      : DataType.INT8,
    'int16'     : DataType.INT16,
    'int32'     : DataType.INT32,
    'float'     : DataType.FLOAT,
}

# these map to the corresponding jump offsets used in a Subaru ROM
class TableDataType(IntEnum):
    DATA_4B = 0x00
    DATA_2B = 0x04
    DATA_1B = 0x08
    DATA_U1 = 0x0C # not sure what/if these are ever used
    DATA_U2 = 0x10 # not sure what/if these are ever used

class ByteOrder(IntEnum):
    BIG_ENDIAN = auto()
    LITTLE_ENDIAN = auto()

_byte_order_struct_map = {
    ByteOrder.BIG_ENDIAN : '>',
    ByteOrder.LITTLE_ENDIAN : '<',
}

class LoggerProtocol(IntEnum):
    SSM = auto()
    #TODO: OBD = auto()
    #TODO: DS2 = auto()
    #TODO: NCS = auto()

class LoggerEndpoint(IntEnum):
    ECU     = 1
    TCU     = 2
    ECU_TCU = 3
