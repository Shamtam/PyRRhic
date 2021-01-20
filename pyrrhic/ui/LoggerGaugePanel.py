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

from .panelsBase import bLoggerGaugePanel
from .GaugePanel import GaugePanel

class LoggerGaugePanel(bLoggerGaugePanel):
    def __init__(self, *args):
        super(LoggerGaugePanel, self).__init__(*args)
        self._panels = []
        self._gauge_map = {}

    def _update_gauge_layout(self):
        if self._panels:
            sz = self.GetSizer()
            sz.Clear()

            canvas_size = self.GetClientSize()
            min_size = self._panels[0].GetBestSize()

            num_cols = canvas_size[0] // min_size[0]
            num_rows = canvas_size[1] // min_size[1]
            sz.SetCols(num_cols)
            sz.SetRows(num_rows)
            sz.AddMany([(x, 0, wx.EXPAND | wx.ALL, 2) for x in self._panels])
            self.Layout()

    def add_gauge(self, param):
        if param.Identifier not in self._gauge_map:
            g = GaugePanel(self, param)
            self._gauge_map[param.Identifier] = g
            self._panels.append(g)
            self._update_gauge_layout()

    def remove_gauge(self, param):
        if param.Identifier in self._gauge_map:
            g = self._gauge_map[param.Identifier]
            self._panels.remove(g)
            del self._gauge_map[param.Identifier]
            self.Sizer.Detach(g)
            g.Destroy()
            self._update_gauge_layout()

    def update_gauges(self):
        for g in self._panels:
            g.update()

    def OnResize(self, event):
        if self._panels:
            sz = self.GetSizer()
            canvas_size = self.GetClientSize()
            min_size = self._panels[0].GetBestSize()
            num_cols = canvas_size[0] // min_size[0]
            num_rows = canvas_size[1] // min_size[1]
            sz.SetCols(num_cols)
            sz.SetRows(num_rows)
        self.Layout()
