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

from wx import dataview as dv

from .panelsBase import bLoggerParamPanel
from .ViewModels import TranslatorViewModel, OptionalToggleRenderer

class LoggerParamPanel(bLoggerParamPanel):
    def __init__(self, *args):
        super(LoggerParamPanel, self).__init__(*args)
        self._controller = self.Parent.Controller

    def initialize(self, translator):
        self._model = TranslatorViewModel(translator)
        self._dvc.AssociateModel(self._model)
        self._model.DecRef()

        _toggle_rend = OptionalToggleRenderer(
            mode=dv.DATAVIEW_CELL_ACTIVATABLE,
        )

        # determine row/col widths
        font = self._dvc.GetFont()
        dc = wx.ScreenDC()
        dc.SetFont(font)

        # get minimal row size for the current font size
        row_height = dc.GetTextExtent('test')[1]
        box_width = _toggle_rend.Size
        id_width = dc.GetTextExtent('X1234')[0]
        del dc

        self._dvc.SetRowHeight(max(box_width, row_height))

        _toggle_col = dv.DataViewColumn(
            '', _toggle_rend, 0, width=box_width*3,
            align=wx.ALIGN_RIGHT, flags=0
        )
        self._dvc.AppendColumn(_toggle_col)

        self._dvc.AppendTextColumn(
            'ID',
            1,
            width=id_width,
            align=wx.ALIGN_LEFT,
            flags=dv.DATAVIEW_COL_SORTABLE,
        )

        self._dvc.AppendTextColumn(
            'Name',
            2,
            align=wx.ALIGN_LEFT,
            flags=dv.DATAVIEW_COL_SORTABLE | dv.DATAVIEW_COL_RESIZABLE,
        )

        self._dvc.GetColumn(2).SetSortOrder(True)

    def clear(self):
        self._dvc.ClearColumns()

    def update_model(self):
        self._model.Cleared()

    def OnSelectParam(self, event):
        pass

    def OnUpdateParams(self, event):
        # TODO: veto enabling of parameters if beyond query capacity
        self._controller.update_log_params()

    def OnEditItem(self, event):
        event.Skip()

    # def OnSelectAvailable(self, event):
    #     m = self._model
    #     nodes = [m.ItemToObject(x) for x in self._dvc.GetSelections()]
    #     self._but_add.Enable(all([isinstance(x[0], LogParamType) for x in nodes]))

    # def OnSelectSelected(self, event):
    #     #nodes = [m.ItemToObject(x) for x in self._selected_dvc.GetSelections()]
    #     self._but_rem.Enable(all([isinstance(x[0], LogParamType) for x in nodes]))

    # def OnAddParam(self, event):
    #     m = self._model
    #     nodes = [m.ItemToObject(x) for x in self._dvc.GetSelections()]
    #     nodes = list(filter(lambda x: isinstance(x[0], LogParamType), nodes))
    #     params = [x[2] for x in nodes]
    #     self._controller.add_log_params(params)

    # def OnRemoveParam(self, event):
    #     #nodes = [m.ItemToObject(x) for x in self._selected_dvc.GetSelections()]
    #     nodes = list(filter(lambda x: isinstance(x[0], LogParamType), nodes))
    #     params = [x[2] for x in nodes]
    #     self._controller.remove_log_params(params)
