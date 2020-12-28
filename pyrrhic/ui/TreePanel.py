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

from .panelsBase import bTreePanel
from ..common.rom import Rom, PyrrhicRomViewModel

class TreePanel(bTreePanel):
    def __init__(self, *args, **kwargs):
        super(TreePanel, self).__init__(*args, **kwargs)

    def initialize(self, rom_container):
        self._model = PyrrhicRomViewModel(self.Parent.Controller)
        self._dvc.AssociateModel(self._model)
        self._model.DecRef()

        self._dvc.AppendTextColumn('Name', 0)

        # get minimal row size for the current font size
        font = self._dvc.GetFont()
        dc = wx.ScreenDC()
        dc.SetFont(font)
        row_height = dc.GetTextExtent('test')[1]
        del dc

        self._dvc.SetRowHeight(row_height)

    def update_model(self):
        self._model.Cleared()

    def OnToggle(self, event):
        item = event.GetItem()
        node = self._model.ItemToObject(item)

        if (
            isinstance(node, Rom) or
            (
                isinstance(node, tuple) and
                node[0] in ['infocontainer', 'category']
            )
        ):
            dvc = self._dvc
            dvc.Collapse(item) if dvc.IsExpanded(item) else dvc.Expand(item)

        elif (isinstance(node, tuple) and node[0] == 'table'):
            data = node[1]
            self.Parent.edit_table(data)
