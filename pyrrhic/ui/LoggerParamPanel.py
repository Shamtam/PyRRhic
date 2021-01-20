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

from .panelsBase import bLoggerParamPanel
from ..common.rom import PyrrhicLoggerViewModel
from ..common.enums import LogParamType

class LoggerParamPanel(bLoggerParamPanel):
    def __init__(self, *args):
        super(LoggerParamPanel, self).__init__(*args)
        self._controller = self.Parent.Controller

    def initialize(self, logger_def):
        self._selected_model = PyrrhicLoggerViewModel(logger_def, selected=True)
        self._selected_dvc.AssociateModel(self._selected_model)
        self._selected_model.DecRef()
        self._selected_dvc.AppendTextColumn('Name', 0)

        self._available_model = PyrrhicLoggerViewModel(logger_def)
        self._available_dvc.AssociateModel(self._available_model)
        self._available_model.DecRef()
        self._available_dvc.AppendTextColumn('Name', 0)

        # get minimal row size for the current font size
        font = self._selected_dvc.GetFont()
        dc = wx.ScreenDC()
        dc.SetFont(font)
        row_height = dc.GetTextExtent('test')[1]
        del dc

        self._selected_dvc.SetRowHeight(row_height)
        self._available_dvc.SetRowHeight(row_height)

    def clear(self):
        self._selected_dvc.ClearColumns()
        self._available_dvc.ClearColumns()

    def update_model(self):
        self._selected_model.Cleared()
        self._available_model.Cleared()

    def OnSelectAvailable(self, event):
        m = self._available_model
        nodes = [m.ItemToObject(x) for x in self._available_dvc.GetSelections()]
        self._but_add.Enable(all([isinstance(x[0], LogParamType) for x in nodes]))

    def OnSelectSelected(self, event):
        m = self._selected_model
        nodes = [m.ItemToObject(x) for x in self._selected_dvc.GetSelections()]
        self._but_rem.Enable(all([isinstance(x[0], LogParamType) for x in nodes]))

    def OnAddParam(self, event):
        m = self._available_model
        nodes = [m.ItemToObject(x) for x in self._available_dvc.GetSelections()]
        nodes = list(filter(lambda x: isinstance(x[0], LogParamType), nodes))
        params = [x[2] for x in nodes]
        self._controller.add_log_params(params)

    def OnRemoveParam(self, event):
        m = self._selected_model
        nodes = [m.ItemToObject(x) for x in self._selected_dvc.GetSelections()]
        nodes = list(filter(lambda x: isinstance(x[0], LogParamType), nodes))
        params = [x[2] for x in nodes]
        self._controller.remove_log_params(params)
