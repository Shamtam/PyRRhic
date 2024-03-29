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

from .enums import DataType

def bound_int(dtype, i):
    """Bound `i` to be within the valid range for the given `dtype`.

    Returns the bounded `int`, or `None` if `dtype` is not one of the
    integer data types specified in `DataType`.

    Arguments:
    - `dtype`: `DataType`
    - `i`: `int` to be bounded
    """

    ranges = {
        DataType.UINT8: (0, 255),
        DataType.UINT16: (0, 65535),
        DataType.UINT32: (0, 4294967295),
        DataType.INT8: (-128, 127),
        DataType.INT16: (-32768, 32767),
        DataType.INT32: (-2147483648, 2147483647),
    }
    if dtype not in ranges:
        return None
    else:
        min_val, max_val = ranges[dtype]
        return min(max(i, min_val), max_val)
