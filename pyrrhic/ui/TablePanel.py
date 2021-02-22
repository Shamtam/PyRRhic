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

from pubsub import pub

from .EditDialog import EditDialog
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
        pub.subscribe(self.populate, 'livetune.state.push.complete')

    def _initialize(self):
        self._num_cols = 1
        self._num_rows = 1

        self._current_selection = []
        self._table_map = {
            self._table_grid: self._table
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
            self._num_cols = self._table.Axes[0].Definition.Length
            self._x_grid.AppendCols(self._num_cols)
            self._x_grid.AppendRows()
            self._table_grid.AppendCols(self._num_cols)
            self._table_grid.AppendRows()
            self._table_map[self._x_grid] = self._table.Axes[0]

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
            self._table_map[self._x_grid] = self._table.Axes[0]
            self._table_map[self._y_grid] = self._table.Axes[1]

    def _set_value(self, table, grid, idx1, idx2):
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
            # assume STATIC tables are always an x axis (i.e. use idx2)
            val = vals[idx2]
        else:
            dtype = vals.dtype.kind

            if len(vals.shape) == 2:
                idx = (idx1, idx2)
            else:
                idx = idx2 if idx1 is None else idx1

            val = _to_str(vals[idx], dtype)

        idx1 = 0 if idx1 is None else idx1
        idx2 = 0 if idx2 is None else idx2

        grid.SetCellValue(idx1, idx2, val)

        # bold cell font if value has been modified
        font = (
            grid.GetCellFont(idx1, idx2).Bold().Italic()
            if table.check_val_modified(idx1, idx2)
            else grid.GetCellFont(idx1, idx2).GetBaseFont()
        )
        grid.SetCellFont(idx1, idx2, font)

    def populate(self):

        # populate table and axes
        for i in range(self._num_rows):
            for j in range(self._num_cols):

                if self._table.Axes:
                    # set y axis values
                    if j == 0 and len(self._table.Axes) == 2:
                        ax = self._table.Axes[1]
                        self._set_value(ax, self._y_grid, i, None)

                    # set x axis values
                    if i == 0 and self._table.Axes:
                        ax = self._table.Axes[0]
                        self._set_value(ax, self._x_grid, None, j)

                # set table value
                self._set_value(self._table, self._table_grid, i, j)

        self.Refresh()

        msg = 'rom' if isinstance(self._table, RomTable) else 'ram'
        pub.sendMessage('editor.table.{}.change'.format(msg), obj=self)

    def OnSelect(self, event):
        obj = event.GetEventObject()
        evtID = event.GetEventType()

        table = self._table_map.get(obj, None)
        if not table:
            return

        # single cell selected
        if evtID == wx.grid.wxEVT_GRID_SELECT_CELL:

            if obj == self._x_grid:
                idx = (event.Col, 0)
            elif obj == self._y_grid:
                idx = (event.Row, 0)
            else:
                idx = (event.Row, event.Col)

            self._current_selection = (table, [idx])

        elif evtID == wx.grid.wxEVT_GRID_RANGE_SELECTED:
            selections = list(obj.GetSelectedBlocks())

            if len(selections) == 1:
                s = selections[0]
                rows = range(s.TopRow, s.BottomRow + 1)
                cols = range(s.LeftCol, s.RightCol + 1)

                if len(rows) > 1 or len(cols) > 1:
                    if obj == self._x_grid:
                        cells = [(y, 0) for x in rows for y in cols]
                    elif obj == self._y_grid:
                        cells = [(x, 0) for x in rows for y in cols]
                    else:
                        cells = [(x, y) for x in rows for y in cols]

                    self._current_selection = (table, cells)

        else:
            self._current_selection = None

    def OnClose(self, event):
        p = self.GetAuiManager().GetPane(self._identifier)
        p.Show(not p.IsShown())

    def edit_grid(self, func, val=None):

        if self._current_selection:
            table, cells = self._current_selection
            for i, j in cells:

                _func_map = {
                    'inc': (table.step, (i, j), {}),
                    'dec': (table.step, (i, j), {'decrement': True}),
                    'inc_raw': (table.add_raw, (1, i, j), {}),
                    'dec_raw': (table.add_raw, (-1, i, j), {}),
                    'set': (table.set_cell, (val, i, j), {}),
                    'add': (table.add_cell, (val, i, j), {}),
                    'mult': (table.mult_cell, (val, i, j), {}),
                }

                f, args, kwargs = _func_map[func]
                f(*args, **kwargs)

            self.populate()

    def OnIncrement(self, event=None):
        self.edit_grid('inc')

    def OnDecrement(self, event=None):
        self.edit_grid('dec')

    def OnIncrementRaw(self, event=None):
        self.edit_grid('inc_raw')

    def OnDecrementRaw(self, event=None):
        self.edit_grid('dec_raw')

    def OnSetValue(self, event=None):
        dlg = EditDialog(self)
        result = dlg.ShowModal()
        if result == wx.ID_SAVE:
            val = dlg.Value
            self.edit_grid('set', val)

        dlg.Destroy()

    def OnAddToValue(self, event=None):
        dlg = EditDialog(self, op='+')
        result = dlg.ShowModal()
        if result == wx.ID_SAVE:
            val = dlg.Value
            self.edit_grid('add', val)

        dlg.Destroy()

    def OnMultiplyValue(self, event=None):
        dlg = EditDialog(self, op='*')
        result = dlg.ShowModal()
        if result == wx.ID_SAVE:
            val = dlg.Value
            self.edit_grid('mult', val)

        dlg.Destroy()

    def OnInterpolateH(self, event=None):
        if not self._current_selection:
            return

        table, cells = self._current_selection

        if table == self._table.Axes[1]:
            return

        # create temporary array with only selected values
        shape = table.DisplayValues.shape
        if len(shape) == 2:
            array = [[None]*shape[1] for x in range(shape[0])]
        else:
            cells = [(i, None) for i, j in cells]
            array = [[None]*shape[0]]

        for cell in cells:
            idx1, idx2 = cell
            if idx2 is not None:
                array[idx1][idx2] = table.DisplayValues[cell]
            else:
                array[0][idx1] = table.DisplayValues[idx1]

        # interpolate row-wise for each row individualy
        for i, row in enumerate(array):
            vals = []
            col = None

            for j, val in enumerate(row):
                if val is not None:
                    if not vals:
                        col = j
                    vals.append(val)

                else:
                    # encountered last value in this row
                    if all([x is None for x in row[j:]]):
                        break

                    # if a `None` is encountered between values,
                    # skip interpolation for this row
                    if vals and any([x is not None for x in row[j:]]):
                        array[i] = [None]*len(row)
                        break

            if len(vals) <= 1:
                continue

            min, max = vals[0], vals[-1]
            step = (max - min)/(len(vals) - 1)

            for j in range(1, len(vals) - 1):
                interp = min + step*j
                table.set_cell(interp, i, col + j)

        self.populate()

    def OnInterpolateV(self, event=None):
        if not self._current_selection:
            return

        table, cells = self._current_selection

        if table == self._table.Axes[0]:
            return

        # create temporary array with only selected values
        shape = table.DisplayValues.shape
        if len(shape) == 2:
            array = [[None]*shape[0] for x in range(shape[1])]
        else:
            cells = [(i, None) for i, j in cells]
            array = [[None]*shape[0]]

        for cell in cells:
            idx1, idx2 = cell
            if idx2 is not None:
                array[idx2][idx1] = table.DisplayValues[cell]
            else:
                array[0][idx1] = table.DisplayValues[idx1]

        # interpolate row-wise for each row individualy
        for j, col in enumerate(array):
            vals = []
            row = None

            for i, val in enumerate(col):
                if val is not None:
                    if not vals:
                        row = i
                    vals.append(val)

                else:
                    # encountered last value in this row
                    if all([x is None for x in col[i:]]):
                        break

                    # if a `None` is encountered between values,
                    # skip interpolation for this col
                    if vals and any([x is not None for x in col[i:]]):
                        array[j] = [None]*len(col)
                        break

            if len(vals) <= 1:
                continue

            min, max = vals[0], vals[-1]
            step = (max - min)/(len(vals) - 1)

            for i in range(1, len(vals) - 1):
                interp = min + step*i
                table.set_cell(interp, row + i, j)

        self.populate()

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
            wx.WXK_NUMPAD_MULTIPLY:{
                wx.MOD_NONE: self.OnMultiplyValue,
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
            # a key
            65:{
                wx.MOD_NONE: self.OnAddToValue,
            },
            # e key
            69:{
                wx.MOD_NONE: self.OnSetValue,
            },
            # h key
            72:{
                wx.MOD_NONE: self.OnInterpolateH,
            },
            # m key
            77:{
                wx.MOD_NONE: self.OnMultiplyValue,
            },
            # v key
            86:{
                wx.MOD_NONE: self.OnInterpolateV,
            },
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

    def OnRevert(self, event=None):
        self._table.revert()
        self.populate()

    def OnCellChange(self, event):
        obj = event.GetEventObject()

        table = self._table_map.get(obj, None)
        if not table:
            return

        i, j = event.Row, event.Col
        val = obj.GetCellValue(i, j)

        if table.check_valid_value(val):
            table.set_cell(float(val), i, j) # TODO: properly handle converting cell values instead of assuming float
            self.populate()

    def OnPaste(self, event):
        return # TODO
        d = wx.TextDataObject()

        # only paste when
        if not self._current_selection:
            return

        table, cells = self._current_selection

        # pull clipboard text data, return on failure
        if not wx.TheClipboard.GetData(d):
            return

        # return if no text
        text = d.GetText()
        if not text:
            return

        # try parsing clipboard text
        try:
            text_rows = text.splitlines()
            rows = []

            for row in text_rows:
                vals = [float(x) for x in row.split()]

                if rows and len(vals) != rows[-1]:
                    return

                rows.append(vals)

        except Exception as e:
            return

    @property
    def Identifier(self):
        return self._identifier
