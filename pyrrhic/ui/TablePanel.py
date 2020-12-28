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

import numpy as np
import wx

from .panelsBase import bTablePanel
from ..common.enums import DataType

class TablePanel(bTablePanel):
    def __init__(self, parent, identifier, table, **kwargs):
        super(TablePanel, self).__init__(parent, **kwargs)
        self._identifier = identifier
        self._table = table
        self._initialize()
        self.populate()

        self.Fit()
        self.SetMaxSize(self.GetSize())
        self.SetScrollRate(5, 5)

    def _initialize(self):
        self._num_cols = 1
        self._num_rows = 1

        # constant/1D table
        if not self._table.Axes:
            self._x_grid.Hide()
            self._y_grid.Hide()
            self._table_grid.AppendCols()
            self._table_grid.AppendRows()
            self._table_grid.SetDefaultCellAlignment(
                wx.ALIGN_CENTER, wx.ALIGN_CENTER
            )

        # 2D table
        elif len(self._table.Axes) == 1:
            self._num_cols = self._table.Axes[0].Definition.Length
            self._x_grid.AppendCols(self._num_cols)
            self._x_grid.AppendRows()
            self._table_grid.AppendCols(self._num_cols)
            self._table_grid.AppendRows()

        # 3D table
        elif len(self._table.Axes) == 2:
            self._num_cols = self._table.Axes[0].Definition.Length
            self._num_rows = self._table.Axes[1].Definition.Length
            self._x_grid.AppendCols(self._num_cols)
            self._x_grid.AppendRows()
            self._y_grid.AppendRows(self._num_rows)
            self._y_grid.AppendCols()
            self._table_grid.AppendCols(self._num_cols)
            self._table_grid.AppendRows(self._num_rows)

    def _set_value(self, table, grid, row, col, swap=False):
        _format_map = {
            'u': '{:d}',
            'i': '{:d}',
            'f': '{:.6g}',
        }
        _to_str = lambda x, y: _format_map[y].format(x)

        vals = table.DisplayValues
        if table.Definition.Datatype == DataType.BLOB:
            val = vals
        elif table.Definition.Datatype == DataType.STATIC:
            val = vals[col]
        else:
            dtype = vals.dtype.kind
            val = _to_str(vals[row][col], dtype)

        if swap:
            grid.SetCellValue(col, row, val)
        else:
            grid.SetCellValue(row, col, val)

    def populate(self):

        # populate table and axes
        for i in range(self._num_rows):
            for j in range(self._num_cols):

                if self._table.Axes:
                    # set y axis values
                    if j == 0 and len(self._table.Axes) == 2:
                        ax = self._table.Axes[1]
                        self._set_value(ax, self._y_grid, j, i, swap=True)

                    # set x axis values
                    if i == 0 and self._table.Axes:
                        ax = self._table.Axes[0]
                        self._set_value(ax, self._x_grid, i, j)

                # set table value
                self._set_value(self._table, self._table_grid, i, j)

    def OnClose(self, event):
        p = self.GetAuiManager().GetPane(self._identifier)
        p.Show(not p.IsShown())

    @property
    def Identifier(self):
        return self._identifier
