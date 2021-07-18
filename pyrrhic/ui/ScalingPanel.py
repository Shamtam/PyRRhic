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

from .panelsBase import bScalingPanel


class ScalingPanel(bScalingPanel):
    def __init__(self, parent):
        super().__init__(parent)

    def populate(self, scaling):
        self.Freeze()

        self._id_box.SetValue(scaling.name)
        self._units_box.SetValue(scaling.units)

        expr = scaling.expression
        if isinstance(expr, str):
            self._expr_box.SetValue(expr)
        elif isinstance(expr, dict):
            

        self.Thaw()
