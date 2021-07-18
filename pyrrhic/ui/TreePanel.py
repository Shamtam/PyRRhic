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
from wx import dataview as dv

from ..common.rom import Rom, InfoContainer, TableContainer
from ..common.structures import RomTable
from .panelsBase import bTreePanel
from .ViewModels import RomViewModel


class TreePanel(bTreePanel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        pub.subscribe(self.initialize, 'controller.init')
        pub.subscribe(self.update_model, 'editor.table.rom.change')

    def initialize(self, controller):
        self._model = RomViewModel(controller)
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

    def update_model(self, obj=None):
        if obj is None:
            self._model.Cleared()

        elif isinstance(obj, Rom):
            item = self._model.ObjectToItem(obj)
            self._model.ItemChanged(item)

        elif isinstance(obj, RomTable):
            rom = obj.Parent
            category = rom.Tables[obj.Definition.Category]

            items = [
                self._model.ObjectToItem(obj),
                self._model.ObjectToItem(category),
                self._model.ObjectToItem(rom)
            ]
            dva = dv.DataViewItemArray()
            for x in items: dva.append(x)
            self._model.ItemsChanged(dva)

    def OnToggle(self, event):
        item = event.GetItem()
        node = self._model.ItemToObject(item)

        if isinstance(node, (Rom, InfoContainer, TableContainer)):
            dvc = self._dvc
            dvc.Collapse(item) if dvc.IsExpanded(item) else dvc.Expand(item)

        elif isinstance(node, RomTable):
            pub.sendMessage('editor.table.toggle', table=node)

    @property
    def Model(self):
        return self._model
