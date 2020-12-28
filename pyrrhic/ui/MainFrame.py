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

import logging
import wx

from .base import bMainFrame
from .TablePanel import TablePanel
from ..controller import PyrrhicController
from .PrefsDialog import PrefsDialog
from .wxutils import modal_dialog_ok

_logger = logging.getLogger(__name__)

class MainFrame(bMainFrame):
    def __init__(self, parent):
        super(MainFrame, self).__init__(parent)
        self._controller = PyrrhicController(self)
        self._tree_panel.initialize(self._controller.LoadedROMs)

    def __del__(self):
    # need to override this function (auto-generated by wxFormBuilder)
    # to avoid exception being thrown on close due to AUI manager deletion
        pass

    def edit_table(self, data):
        rom, cat_name = data[0][1]
        tab_name = data[-1]
        table = rom.Tables[cat_name][tab_name]

        if table.Panel is not None:
            self.toggle_table(table.Panel)

        else:
            pane_name = table.PanelTitle
            p = TablePanel(self, pane_name, table)
            table.Panel = p
            start_pos = self.GetScreenPosition()

            # calculate pane (not panel) total size
            scr_x = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
            scr_y = wx.SystemSettings.GetMetric(wx.SYS_HSCROLL_Y)
            max_size = (p.GetSize()[0], p.GetSize()[1])

            self.m_mgr.AddPane(
                p,
                wx.aui.AuiPaneInfo()
                    .Name(pane_name)
                    .Caption(pane_name)
                    .CloseButton()
                    .PaneBorder()
                    .Float()
                    .Resizable()
                    .FloatingPosition(start_pos)
                    .Show()
            )
            self.m_mgr.Update()

            # need to set the AUIFloatingPane max size here, since the
            # aui.AuiPaneInfo.MaxSize() approach doesn't seem to work
            p.Parent.SetClientSize(max_size)
            p.Parent.SetMaxClientSize(max_size)

    def toggle_table(self, pane_id):
        pane = self.m_mgr.GetPane(pane_id)
        pane.Show(not pane.IsShown())
        self.m_mgr.Update()

    def refresh_tree(self):
        self._tree_panel.update_model()

    def info_box(self, title, message):
        modal_dialog_ok(self, title, message, wx.ICON_INFORMATION)

    def warning_box(self, title, message):
        modal_dialog_ok(self, title, message, wx.ICON_WARNING)

    def error_box(self, title, message):
        modal_dialog_ok(self, title, message, wx.ICON_ERROR)

    def OnClose(self, event):
        self._controller.save_prefs()
        self.m_mgr.UnInit()
        event.Skip()

    def OnOpenRom(self, event):
        if not self._controller.DefsValid:
            self.warning_box(
                'No Definitions Loaded',
                'No definitions loaded! Please ensure definition paths are correct',
            )
            return

        dlg = wx.FileDialog(self,
            'Open ROM File',
            wildcard='Binary ROM Image (*.hex; *.bin)|*.hex;*.bin|All Files|*.*',
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE
        )
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            fpaths = dlg.GetPaths()

            for fpath in fpaths:
                # TODO: sanity check files here?
                self._controller.open_rom(fpath)

            self.refresh_tree()

    def OnPreferences(self, event):
        dlg = PrefsDialog(self, self._controller.Preferences)
        dlg.ShowModal()
        dlg.Destroy()

    @property
    def Controller(self):
        return self._controller

    @property
    def LogPane(self):
        return self._log_panel

    @property
    def ROMTreePane(self):
        return self._tree_panel
