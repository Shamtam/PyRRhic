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
import sys
import unittest

sys.path.append(".")

from pyrrhic.common.definitions import load_ecuflash_repository  # noqa:E402


class TestECUFlashDefs(unittest.TestCase):
    def setUp(self):
        self.repo_path = os.path.join(os.path.dirname(__file__), "data")

    def test_load_repo(self):
        xml_tree, cal_tree, id_tree = load_ecuflash_repository(self.repo_path)


if __name__ == "__main__":
    unittest.main()
