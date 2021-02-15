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

from ..common.rom import Rom, TableContainer
from ..common.structures import RamTable
from .panelsBase import bRAMTreePanel
from .ViewModels import RamViewModel, OptionalToggleRenderer

class RAMTreePanel(bRAMTreePanel):
    def __init__(self, *args, **kwargs):
        super(RAMTreePanel, self).__init__(*args, **kwargs)
        self._livetune = None
        self._initialized = False

        self._base_ram_label = self._RAM_label.GetLabelText()
        self._base_table_label = self._tables_label.GetLabelText()



    def initialize(self, livetune=None):
        self._livetune = livetune
        self._model = RamViewModel(self.Parent.Controller, livetune)
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
        del dc

        self._dvc.SetRowHeight(max(box_width, row_height))

        _allocate_col = dv.DataViewColumn(
            '', _toggle_rend, 0, width=box_width*3,
            align=wx.ALIGN_RIGHT, flags=0
        )
        _active_col = dv.DataViewColumn(
            '', _toggle_rend, 1, width=box_width*3,
            align=wx.ALIGN_RIGHT, flags=0
        )
        self._dvc.AppendColumn(_allocate_col)
        self._dvc.AppendColumn(_active_col)

        self._dvc.AppendTextColumn(
            'Name',
            2,
            align=wx.ALIGN_LEFT,
            flags=dv.DATAVIEW_COL_RESIZABLE,
        )

        self._dvc.GetColumn(2).SetSortOrder(True)
        self._model.Cleared()

        self._dvc.Enable(False)

        pub.subscribe(self.OnPending, 'livetune.state.pending')
        pub.subscribe(self.OnPullFailed, 'livetune.state.pull.failed')
        pub.subscribe(self.OnPullComplete, 'livetune.state.pull.complete')
        pub.subscribe(self.OnPushComplete, 'livetune.state.push.complete')
        pub.subscribe(self.refresh_tree, 'editor.table.ram.change')

    def refresh_tree(self, obj=None):
        # get expanded items
        items = []
        self._model.GetChildren(None, items)
        exp_items = [x for x in items if self._dvc.IsExpanded(x)]

        # refresh entire tree
        self._model.Cleared()

        # re-expand items
        for item in exp_items:
            self._dvc.Expand(item)

        # while items:
        #     item = items.pop()
        #     self._model.ItemChanged(item)
        #     if self._dvc.IsExpanded(item):
        #         self._model.GetChildren(item, items)

    def OnToggle(self, event):
        item = event.GetItem()
        node = self._model.ItemToObject(item)

        if isinstance(node, TableContainer):
            dvc = self._dvc
            dvc.Collapse(item) if dvc.IsExpanded(item) else dvc.Expand(item)

        elif isinstance(node, RamTable):
            if node.RamAddress is not None:
                pub.sendMessage('editor.table.toggle', table=node)

    def OnValueChange(self, event=None):
        if self._livetune:
            used_bytes = self._livetune.AllocatedSize
            total_bytes = self._livetune.TotalSize
            num_tables = len(self._livetune.Tables)

            pending_bytes = self._livetune.PendingSize
            pending_allocations = self._livetune.PendingAllocations
            pending_activations = self._livetune.PendingActivations

            if pending_allocations:
                self._RAM_label.SetLabelText('{} {}/{} ({}/{})'.format(
                    self._base_ram_label,
                    used_bytes, total_bytes,
                    pending_bytes, total_bytes
                ))
                table_delta = sum(
                    [-1 if x.RamAddress else 1 for x in pending_allocations.values()]
                )
                self._tables_label.SetLabelText('{} {} ({})'.format(
                    self._base_table_label,
                    num_tables, num_tables + table_delta
                ))

            else:
                self._RAM_label.SetLabelText('{} {}/{}'.format(
                    self._base_ram_label,
                    used_bytes,
                    total_bytes
                ))

                self._tables_label.SetLabelText('{} {}'.format(
                    self._base_table_label,
                    num_tables
                ))

            self._gauge.SetRange(total_bytes)
            self._gauge.SetValue(used_bytes)

            self._push_but.Enable(
                bool(pending_allocations) or bool(pending_activations)
            )

    def OnPullState(self, event=None):
        if self._livetune:
            self._livetune.initialize()
            pub.sendMessage('livetune.state.pull.init')
            self._initialized = False

    def OnPushState(self, event=None):
        if self._initialized:
            pub.sendMessage('livetune.state.push.init')

    def OnPending(self):
        self._pull_but.Disable()
        self._push_but.Disable()
        self._dvc.Disable()
        self._gauge.Pulse()

    def OnPullFailed(self):
        self._model.Cleared()
        self._pull_but.Enable()
        self._push_but.Disable()
        self._dvc.Disable()
        self._gauge.SetValue(0)

    def OnPullComplete(self):
        self._model.Cleared()

        self.OnValueChange()
        self._dvc.Enable(True)

        self._initialized = True
        self._pull_but.Enable()

    def OnPushComplete(self):
        self.OnPullState()

    @property
    def Model(self):
        return self._model
