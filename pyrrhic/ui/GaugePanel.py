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

import wx

from .panelsBase import bGaugePanel

class GaugePanel(bGaugePanel):
    def __init__(self, parent, param):
        super().__init__(parent)
        self._param = param
        self._param_label.SetLabelText(param.Name)
        self._value_text.SetLabelText('-')
        self._min = None
        self._max = None

    def refresh(self):
        val = self._param.ValueStr

        if val:
            if not self._min:
                self._min = val
            if not self._max:
                self._max = val

            if val < self._min:
                self._min = val
            if val > self._max:
                self._max = val

            self._value_text.SetLabelText(val)
            self._min_value.SetLabelText(self._min)
            self._max_value.SetLabelText(self._max)
        else:
            self._value_text.SetLabelText('')

        self._value_text.Refresh()
        self._min_value.Refresh()
        self._max_value.Refresh()
        self.Update()
