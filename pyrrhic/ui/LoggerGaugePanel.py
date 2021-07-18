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

from pubsub import pub

from .panelsBase import bLoggerGaugePanel
from .GaugePanel import GaugePanel


class LoggerGaugePanel(bLoggerGaugePanel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._gauge_map = {}

        pub.subscribe(self.update_gauges, 'comms.logquery.updated')
        pub.subscribe(self.refresh_gauges, 'comms.logparams.updated')

    def update_gauges(self, params):

        sz = self.GetSizer()
        sz.Clear()

        # determine params to remove, if needed
        new_params = {x.Identifier for x in params}
        cur_params = set(self._gauge_map.keys())
        rem_params = cur_params - new_params

        # add any new panels
        for p in params:
            if p.Identifier not in self._gauge_map:
                g = GaugePanel(self, p)
                self._gauge_map[p.Identifier] = g

        # remove panels
        for p in rem_params:
            g = self._gauge_map[p]
            del self._gauge_map[p]
            sz.Detach(g)
            g.Destroy()

        # update layout
        panels = list(self._gauge_map.values())

        if panels:
            canvas_size = self.GetClientSize()
            min_size = panels[0].GetBestSize()
            num_cols = canvas_size[0] // min_size[0]
            num_rows = canvas_size[1] // min_size[1]

            sz.SetCols(num_cols)
            sz.SetRows(num_rows)
            sz.AddMany([(x, 0, wx.EXPAND | wx.ALL, 2) for x in panels])
            self.Layout()

    def refresh_gauges(self):
        for g in self._gauge_map.values():
            g.refresh()

    def OnResize(self, event):
        panels = list(self._gauge_map.values())
        if panels:
            sz = self.GetSizer()
            canvas_size = self.GetClientSize()
            min_size = panels[0].GetBestSize()
            num_cols = canvas_size[0] // min_size[0]
            num_rows = canvas_size[1] // min_size[1]
            sz.SetCols(num_cols)
            sz.SetRows(num_rows)
        self.Layout()
