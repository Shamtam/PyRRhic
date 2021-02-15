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

import wx

from pubsub import pub
from wx import aui

from .panelsBase import bTablePanel
from ..common.enums import DataType
from ..common.structures import RamTable, RomTable

class TablePanel(bTablePanel):
    def __init__(self, parent, identifier, table, **kwargs):
        super(TablePanel, self).__init__(parent, **kwargs)
        self._controller = parent.Controller
        self._identifier = identifier
        self._table = table
        self._dtype = table.Definition.Datatype
        self._initialize()
        self.populate()

        self._ramtune_items = [
            self._t_pop_from_ROM,
            self._t_pop_from_RAM,
            self._t_commit,
            self._t_auto_commit
        ]

        # remove RAMtune controls for `RomTable` panels
        if isinstance(self._table, RomTable):
            for item in self._ramtune_items:
                tid = item.GetId()
                self._toolbar.RemoveTool(tid)

        # disable axes editing for `RamTable` panels
        elif isinstance(self._table, RamTable):
            self._x_grid.Enable(False)
            self._y_grid.Enable(False)

        self.Fit()
        self.SetMaxSize(self.GetSize())
        self.SetScrollRate(5, 5)

        pub.subscribe(self.populate, 'livetune.state.pull.complete')

    def _initialize(self):
        self._num_cols = 1
        self._num_rows = 1

        self._x_selection = []
        self._y_selection = []
        self._table_selection = []

        self._selection_map = {
            self._table_grid: (self._table_selection, self._table, (0, 1))
        }

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
            self._selection_map[self._x_grid] = (
                self._x_selection, self._table.Axes[0], (1, None)
            )
            self._num_cols = self._table.Axes[0].Definition.Length
            self._x_grid.AppendCols(self._num_cols)
            self._x_grid.AppendRows()
            self._table_grid.AppendCols(self._num_cols)
            self._table_grid.AppendRows()

        # 3D table
        elif len(self._table.Axes) == 2:
            self._selection_map.update({
                self._x_grid: (self._x_selection, self._table.Axes[0], (1, None)),
                self._y_grid: (self._y_selection, self._table.Axes[1], (0, None)),
            })
            self._num_cols = self._table.Axes[0].Definition.Length
            self._num_rows = self._table.Axes[1].Definition.Length
            self._x_grid.AppendCols(self._num_cols)
            self._x_grid.AppendRows()
            self._y_grid.AppendRows(self._num_rows)
            self._y_grid.AppendCols()
            self._table_grid.AppendCols(self._num_cols)
            self._table_grid.AppendRows(self._num_rows)

    def _set_value(self, table, grid, row, col, swap=False):
        _format_map = { # TODO: dynamic format selection
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
            i, j = (row, col) if not swap else (col, row)
            val = _to_str(vals[i][j], dtype)

        grid.SetCellValue(row, col, val)

        # bold cell font if value has been modified
        font = (
            grid.GetCellFont(row, col).Bold().Italic()
            if table.check_val_modified(row, col)
            else grid.GetCellFont(row, col).GetBaseFont()
        )
        grid.SetCellFont(row, col, font)

    def populate(self):

        # populate table and axes
        for i in range(self._num_rows):
            for j in range(self._num_cols):

                if self._table.Axes:
                    # set y axis values
                    if j == 0 and len(self._table.Axes) == 2:
                        ax = self._table.Axes[1]
                        self._set_value(ax, self._y_grid, i, j, swap=True)

                    # set x axis values
                    if i == 0 and self._table.Axes:
                        ax = self._table.Axes[0]
                        self._set_value(ax, self._x_grid, i, j)

                # set table value
                self._set_value(self._table, self._table_grid, i, j)

        self.Refresh()

        msg = 'rom' if isinstance(self._table, RomTable) else 'ram'
        pub.sendMessage('editor.table.{}.change'.format(msg), obj=self)

    def OnSelect(self, event):
        obj = event.GetEventObject()
        evtID = event.GetEventType()

        for grid, (selection, table, (i, j)) in self._selection_map.items():

            if obj == grid:

                # single cell selected
                if evtID == wx.grid.wxEVT_GRID_SELECT_CELL:
                    idx = (event.Row, event.Col)
                    idx1 = idx[i]
                    idx2 = idx[j] if j is not None else 0
                    if len(list(grid.GetSelectedBlocks())) > 1:
                        selection.append((idx1, idx2))
                    else:
                        selection.clear()
                        selection.append((idx1, idx2))

                elif evtID == wx.grid.wxEVT_GRID_RANGE_SELECTED:
                    selections = list(grid.GetSelectedBlocks())

                    if len(selections) == 1:
                        s = selections[0]
                        rows = range(s.TopRow, s.BottomRow + 1)
                        cols = range(s.LeftCol, s.RightCol + 1)
                        cells = [(x, y) for x in rows for y in cols]

                        if len(rows) > 1 or len(cols) > 1:
                            selection.clear()
                            for idx in cells:
                                idx1 = idx[i]
                                idx2 = idx[j] if j is not None else 0
                                selection.append((idx1, idx2))
            else:
                selection.clear()

    def OnClose(self, event):
        p = self.GetAuiManager().GetPane(self._identifier)
        p.Show(not p.IsShown())

    def OnIncrement(self, grid):
        selection, table, idx = self._selection_map[grid]
        for i, j in selection:
            table.step(i, j)
        self.populate()

    def OnDecrement(self, grid):
        selection, table, idx = self._selection_map[grid]
        for i, j in selection:
            table.step(i, j, decrement=True)
        self.populate()

    def OnIncrementRaw(self, grid):
        selection, table, idx= self._selection_map[grid]
        for i, j in selection:
            table.add_raw(1, i, j)
        self.populate()

    def OnDecrementRaw(self, grid):
        selection, table, idx = self._selection_map[grid]
        for i, j in selection:
            table.add_raw(-1, i, j)
        self.populate()

    def OnSetValue(self, event=None):
        raise NotImplementedError # TODO

    def OnAddToValue(self, event=None):
        raise NotImplementedError # TODO

    def OnMultiplyValue(self, event=None):
        raise NotImplementedError # TODO

    def OnInterpolateH(self, event=None):
        raise NotImplementedError # TODO

    def OnInterpolateV(self, event=None):
        raise NotImplementedError # TODO

    def OnInterpolate2D(self, event=None):
        raise NotImplementedError # TODO

    def OnKeyDown(self, event):
        _func_map = {
            wx.WXK_NUMPAD_SUBTRACT:{
                wx.MOD_NONE: self.OnDecrement,
                wx.MOD_CONTROL: self.OnDecrementRaw,
            },
            wx.WXK_NUMPAD_ADD:{
                wx.MOD_NONE: self.OnIncrement,
                wx.MOD_CONTROL: self.OnIncrementRaw,
            },
            # =/+ key
            61:{
                wx.MOD_NONE: self.OnIncrement,
                wx.MOD_CONTROL: self.OnIncrementRaw,
            },
            # -/_ key
            45:{
                wx.MOD_NONE: self.OnDecrement,
                wx.MOD_CONTROL: self.OnDecrementRaw,
            },
            # e key
            69:{
                wx.MOD_NONE: self.OnSetValue,
            }
        }

        # determine pressed key/modifiers
        kc = event.GetKeyCode()
        mod = event.GetModifiers()

        # call the correct function from the function map
        if kc in _func_map:
            if mod in _func_map[kc]:
                _func_map[kc][mod](event.GetEventObject().Parent)

        # propagate key events for any non-handled keys
        else:
            event.Skip()

    def OnROMPopulate(self, event):
        pass

    def OnRAMPopulate(self, event):
        pass

    def OnCommit(self, event):
        pub.sendMessage('livetune.state.push.init')

    @property
    def Identifier(self):
        return self._identifier
