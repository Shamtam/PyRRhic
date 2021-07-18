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

sys.path.append(".")

from pyrrhic.common.enums import UserLevel, DataType  # noqa:E402
from pyrrhic.common.structures import Scaling, TableDef  # noqa:E402
from pyrrhic.common.helpers import Container, ECUFlashContainer  # noqa:E402


class TestScaling(unittest.TestCase):
    def setUp(self):
        self.scalings = Container(self, name="Scalings")
        scalings = [
            Scaling(
                self.scalings,
                "AFRtest",
                precision=6,
                expression="14.7/(1+x*.0078125)",
            ),
            Scaling(self.scalings, "float_m5to5", min=-5, max=5),
            Scaling(
                self.scalings,
                "basicint",
                format="d",
                padding=3,
                expression="x*4 + 3",
            ),
            Scaling(
                self.scalings,
                "basichex",
                format="x",
                padding=3,
                expression="x*4 + 3",
            ),
        ]

        self.scalings.data = {x.identifier: x for x in scalings}

    def test_float_inversion(self):
        s = self.scalings["AFRtest"]

        for raw_val in range(256):
            disp_val = s.to_disp_val(raw_val)
            calc_raw = s.to_raw(disp_val)
            self.assertAlmostEqual(raw_val, calc_raw, places=s.precision)

    def test_float_min_bound(self):
        s = self.scalings["float_m5to5"]

        self.assertEqual(s.to_disp_val(-10), -5)
        self.assertEqual(s.to_disp_val(-5), -5)
        self.assertEqual(s.to_disp_val(0), 0)

    def test_float_max_bound(self):
        s = self.scalings["float_m5to5"]

        self.assertEqual(s.to_disp_val(10), 5)
        self.assertEqual(s.to_disp_val(5), 5)
        self.assertEqual(s.to_disp_val(0), 0)

    def test_float_format(self):
        s = self.scalings["AFRtest"]

        self.assertEqual(s.to_disp_str(0), "14.700000")
        self.assertEqual(s.to_disp_str(1), "14.586047")
        self.assertEqual(s.to_disp_str(10), "13.634783")
        self.assertEqual(s.to_disp_str(100), "8.252632")

    def test_int_inversion(self):
        s = self.scalings["basicint"]

        for raw_val in range(256):
            disp_val = s.to_disp_val(raw_val)
            calc_raw = int(s.to_raw(disp_val))
            self.assertEqual(raw_val, calc_raw)

    def test_hex_inversion(self):
        s = self.scalings["basichex"]

        for raw_val in range(256):
            disp_val = int(s.to_disp_val(raw_val))
            disp_str = "0x{:x}".format(disp_val)
            calc_raw = int(s.to_raw(disp_str))
            self.assertEqual(raw_val, calc_raw)


class TestTableDef(unittest.TestCase):

    def setUp(self):
        self.stub_tables = ECUFlashContainer(self, name="Table Stubs")
        self.defined_tables = ECUFlashContainer(self, name="Defined Tables")
        self.derived_tables = ECUFlashContainer(self, name="Derived Tables")

        stubs = [
            TableDef(
                self.stub_tables,
                "BaseTable1D",
                "Stub Tables",
                description="A 1D base table stub",
                level=UserLevel.Beginner,
                datatype=DataType.UINT8,
                length=5,
            ),
            TableDef(
                self.stub_tables,
                "BaseTable2D",
                "Stub Tables",
                description="A 2D base table stub",
                level=UserLevel.Beginner,
                datatype=DataType.UINT16,
                axes=[{"datatype": DataType.FLOAT, "length": 10}],
            ),
            TableDef(
                self.stub_tables,
                "BaseTable3D",
                "Stub Tables",
                description="A 3D base table stub",
                level=UserLevel.Beginner,
                datatype=DataType.UINT8,
                axes=[
                    {"datatype": DataType.FLOAT, "length": 10},
                    {"datatype": DataType.FLOAT, "length": 20},
                ],
            ),
            TableDef(
                self.stub_tables,
                "BaseStatic2DTable",
                "Stub Tables",
                description="A 2D base table stub with a static axis",
                level=UserLevel.Beginner,
                datatype=DataType.UINT8,
                axes=[
                    {
                        "datatype": DataType.STATIC,
                        "values": ["Indep 01", "Indep 02", "Indep 03"],
                    },
                ],
            ),
            TableDef(
                self.stub_tables,
                "BaseBlob2DTable",
                "Stub Tables",
                description="A 2D base table stub with a bloblist axis",
                level=UserLevel.Beginner,
                datatype=DataType.UINT8,
                axes=[
                    {
                        "datatype": DataType.BLOB,
                        "scaling": Scaling(
                            self,
                            "TableAxis",
                            "X-Axis",
                            format="s",
                            expression={
                                bytes.fromhex("01"): "Value 01",
                                bytes.fromhex("02"): "Value 02",
                                bytes.fromhex("03"): "Value 03",
                            },
                        ),
                    },
                ],
            ),
        ]

        defined = [
            TableDef(
                self.defined_tables,
                "Defined2DTable",
                "Stub Tables",
                description="A fully-defined 2D table",
                level=UserLevel.Beginner,
                datatype=DataType.UINT8,
                axes=[
                    {
                        'datatype': DataType.FLOAT,
                        'length': 5,
                        'address': 0x1000,
                    }
                ],
                address=(0x1000 + 20)
            )
        ]

        derived = [
            TableDef(
                self.derived_tables,
                "BaseTable1D",
                "Stub Tables",
                address=0x0000
            ),
            TableDef(
                self.derived_tables,
                "BaseTable2D",
                "Stub Tables",
                address=0x1000,
                axes=[
                    {"address": 0x1100}
                ]
            ),
            TableDef(
                self.derived_tables,
                "BaseTable3D",
                "Stub Tables",
                address=0x2000,
                axes=[
                    {"address": 0x2100},
                    {"address": 0x2200}
                ]
            ),
            TableDef(
                self.derived_tables,
                "BaseStatic2DTable",
                "Stub Tables",
                address=0x3000,
                axes=[
                    {},
                ]
            ),
            TableDef(
                self.derived_tables,
                "BaseBlob2DTable",
                "Stub Tables",
                address=0x4000,
                axes=[
                    {"address": 0x3100},
                ]
            ),
        ]

        self.stub_tables.data = {x.name: x for x in stubs}
        self.defined_tables.data = {x.name: x for x in defined}
        self.derived_tables.data = {x.name: x for x in derived}


if __name__ == "__main__":
    unittest.main()
