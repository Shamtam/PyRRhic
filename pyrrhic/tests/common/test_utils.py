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

import sys
import unittest

from pyrrhic.common.utils import bound_int
from pyrrhic.common.enums import DataType


class TestBoundInt(unittest.TestCase):

    def setUp(self) -> None:
        self.big_int = 4294967295*8

    def test_uint8(self):
        self.assertEqual(bound_int(DataType.UINT8, 0), 0)
        self.assertEqual(bound_int(DataType.UINT8, 255), 255)
        self.assertEqual(bound_int(DataType.UINT8, -1), 0)
        self.assertEqual(bound_int(DataType.UINT8, 256), 255)
        self.assertEqual(bound_int(DataType.UINT8, -self.big_int), 0)
        self.assertEqual(bound_int(DataType.UINT8, self.big_int), 255)

    def test_uint16(self):
        self.assertEqual(bound_int(DataType.UINT16, 0), 0)
        self.assertEqual(bound_int(DataType.UINT16, 65535), 65535)
        self.assertEqual(bound_int(DataType.UINT16, -1), 0)
        self.assertEqual(bound_int(DataType.UINT16, 65536), 65535)
        self.assertEqual(bound_int(DataType.UINT16, -self.big_int), 0)
        self.assertEqual(bound_int(DataType.UINT16, self.big_int), 65535)

    def test_uint32(self):
        self.assertEqual(bound_int(DataType.UINT32, 0), 0)
        self.assertEqual(bound_int(DataType.UINT32, 4294967295), 4294967295)
        self.assertEqual(bound_int(DataType.UINT32, -1), 0)
        self.assertEqual(bound_int(DataType.UINT32, 4294967296), 4294967295)
        self.assertEqual(bound_int(DataType.UINT32, -self.big_int), 0)
        self.assertEqual(bound_int(DataType.UINT32, self.big_int), 4294967295)

    def test_int8(self):
        self.assertEqual(bound_int(DataType.INT8, -128), -128)
        self.assertEqual(bound_int(DataType.INT8, 127), 127)
        self.assertEqual(bound_int(DataType.INT8, -129), -128)
        self.assertEqual(bound_int(DataType.INT8, 128), 127)
        self.assertEqual(bound_int(DataType.INT8, -self.big_int), -128)
        self.assertEqual(bound_int(DataType.INT8, self.big_int), 127)

    def test_int16(self):
        self.assertEqual(bound_int(DataType.INT16, -32768), -32768)
        self.assertEqual(bound_int(DataType.INT16, 32767), 32767)
        self.assertEqual(bound_int(DataType.INT16, -32769), -32768)
        self.assertEqual(bound_int(DataType.INT16, 32768), 32767)
        self.assertEqual(bound_int(DataType.INT16, -self.big_int), -32768)
        self.assertEqual(bound_int(DataType.INT16, self.big_int), 32767)

    def test_int32(self):
        self.assertEqual(bound_int(DataType.INT32, -2147483648), -2147483648)
        self.assertEqual(bound_int(DataType.INT32, 2147483647), 2147483647)
        self.assertEqual(bound_int(DataType.INT32, -2147483649), -2147483648)
        self.assertEqual(bound_int(DataType.INT32, 2147483648), 2147483647)
        self.assertEqual(bound_int(DataType.INT32, -self.big_int), -2147483648)
        self.assertEqual(bound_int(DataType.INT32, self.big_int), 2147483647)

    def test_non_int(self):
        self.assertEqual(bound_int(DataType.FLOAT, 0), None)
        self.assertEqual(bound_int(DataType.STATIC, 0), None)


if __name__ == "__main__":
    unittest.main()
