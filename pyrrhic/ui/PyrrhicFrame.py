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
import os
from pyrrhic.ui.DefPanel import DefPanel
import wx

from pubsub import pub
from wx.lib.agw import aui

from ..common.enums import UserLevel
from .TreePanel import TreePanel
from .LoggerParamPanel import LoggerParamPanel
from .LoggerGaugePanel import LoggerGaugePanel
from .RAMTreePanel import RAMTreePanel
from .ConsolePanel import ConsolePanel
from .TablePanel import TablePanel
from .PrefsDialog import PrefsDialog
from .wxutils import modal_dialog_ok

_logger = logging.getLogger(__name__)

# string constants... can be easily refactored away from here for translation
_rom_wildcard = "Binary ROM Image (*.hex; *.bin)|*.hex;*.bin|All Files|*.*"
_connect_text = "Connect"
_connecting_text = "Connecting..."
_disconnect_text = "Disconnect"
_disconnecting_text = "Disconnecting..."
_connect_success_text = "Connection Successful!"
_iface_text = "Interface Selection"
_protocol_text = "Protocol Selection"


class PyrrhicFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(
            parent,
            title="PyRRhic",
            size=wx.Size(1000, 600),
            style=(
                wx.DEFAULT_FRAME_STYLE | wx.RESIZE_BORDER | wx.TAB_TRAVERSAL
            ),
        )

        self._temp_status_delay = 3000  # ms
        self._left_status_timer = wx.Timer(self)
        self._center_status_timer = wx.Timer(self)
        self._right_status_timer = wx.Timer(self)

        self._init_ui()
        self._init_menubar()
        self._init_bindings()

        self._save_items = [
            self._mi_save,
            self._mi_save_as,
            self._tb_save,
            self._tb_save_as,
        ]

    def _init_ui(self):

        self._statusbar = self.CreateStatusBar(3)

        self._mgr = aui.AuiManager(
            self,
            aui.AUI_MGR_DEFAULT
            | aui.AUI_MGR_ALLOW_ACTIVE_PANE
            | aui.AUI_MGR_LIVE_RESIZE
            | aui.AUI_MGR_AUTONB_NO_CAPTION,
        )

        self._mgr.SetAutoNotebookStyle(
            aui.AUI_NB_TOP
            | aui.AUI_NB_MIDDLE_CLICK_CLOSE
            | aui.AUI_NB_TAB_EXTERNAL_MOVE
        )
        self._mgr.SetAutoNotebookTabArt(aui.AuiSimpleTabArt())

        self._console_panel = ConsolePanel(self, name="ConsolePanel")

        _panels = [
            TreePanel(self, name="ROMPanel"),
            LoggerParamPanel(self, name="LogParamPanel"),
            LoggerGaugePanel(self, name="LogGaugePanel"),
            RAMTreePanel(self, name="LiveTunePanel"),
            DefPanel(self, name="DefPanel"),
        ]
        self._panels = {x.Name: x for x in _panels}

        # center pane
        self._mgr.AddPane(
            self._console_panel,
            aui.AuiPaneInfo()
            .Name("ConsolePane")
            .Caption("Console")
            .CenterPane()
            .MinSize(600, 600)
            .NotebookDockable(),
        )
        self._mgr.AddPane(
            self._panels["LogGaugePanel"],
            aui.AuiPaneInfo()
            .Name("LogGaugePane")
            .Caption("Gauges")
            .Dockable()
            .Floatable()
            .Float()
            .CloseButton()
            .NotebookDockable()
            .MinSize(400, 400),
            target=self._mgr.GetPaneByName("ConsolePane"),
        )
        self._mgr.AddPane(
            self._panels["DefPanel"],
            aui.AuiPaneInfo()
            .Name("DefPane")
            .Caption("Definitions")
            .Floatable()
            .Float()
            .CloseButton()
            .NotebookDockable()
            .MinSize(400, 400)
            .Hide()
        )

        # left pane
        self._mgr.AddPane(
            self._panels["ROMPanel"],
            aui.AuiPaneInfo()
            .Name("ROMPane")
            .Caption("ROMs")
            .Dockable()
            .Floatable()
            .Left()
            .CloseButton()
            .NotebookDockable()
            .MinSize(250, 200),
        )
        self._mgr.AddPane(
            self._panels["LogParamPanel"],
            aui.AuiPaneInfo()
            .Name("LogParamPane")
            .Caption("Log Parameters")
            .Dockable()
            .Floatable()
            .Left()
            .CloseButton()
            .NotebookDockable()
            .MinSize(250, 200),
            target=self._mgr.GetPaneByName("ROMPane"),
        )
        self._mgr.AddPane(
            self._panels["LiveTunePanel"],
            aui.AuiPaneInfo()
            .Name("LiveTunePane")
            .Caption("Live Tuning")
            .Dockable()
            .Floatable()
            .Left()
            .CloseButton()
            .NotebookDockable()
            .MinSize(250, 200),
            target=self._mgr.GetPaneByName("ROMPane"),
        )

        for nb in self._mgr.GetNotebooks():
            nb.SetSelection(0)

        _rom_toolbar = aui.AuiToolBar(
            self,
            agwStyle=aui.AUI_TB_HORZ_LAYOUT,
        )
        self._tb_open = _rom_toolbar.AddTool(
            wx.ID_ANY,
            "Open ROM",
            wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR),
            wx.NullBitmap,
            wx.ITEM_NORMAL,
            "Open ROM",
            "Open ROM",
            None,
        )
        self._tb_save = _rom_toolbar.AddTool(
            wx.ID_ANY,
            "Save ROM",
            wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE, wx.ART_TOOLBAR),
            wx.NullBitmap,
            wx.ITEM_NORMAL,
            "Save ROM",
            "Save ROM",
            None,
        )
        self._tb_save_as = _rom_toolbar.AddTool(
            wx.ID_ANY,
            "Save ROM As",
            wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_TOOLBAR),
            wx.NullBitmap,
            wx.ITEM_NORMAL,
            "Save ROM As",
            "Save ROM As",
            None,
        )
        _rom_toolbar.Realize()

        _log_toolbar = aui.AuiToolBar(self, agwStyle=aui.AUI_TB_HORZ_LAYOUT)

        self._refresh_but = _log_toolbar.AddTool(
            wx.ID_ANY,
            "Refresh",
            wx.ArtProvider.GetBitmap(wx.ART_FIND, wx.ART_BUTTON),
            wx.NullBitmap,
            wx.ITEM_NORMAL,
            "Refresh Devices",
            "Refresh Device List",
            None,
        )

        self._iface_choice = wx.Choice(
            _log_toolbar,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            [_iface_text],
            0,
        )
        self._iface_choice.SetSelection(0)
        _log_toolbar.AddControl(self._iface_choice)

        self._protocol_choice = wx.Choice(
            _log_toolbar,
            wx.ID_ANY,
            wx.DefaultPosition,
            wx.DefaultSize,
            [_protocol_text],
            0,
        )
        self._protocol_choice.SetSelection(0)
        _log_toolbar.AddControl(self._protocol_choice)

        self._connect_but = wx.Button(
            _log_toolbar,
            wx.ID_ANY,
            _connect_text,
            wx.DefaultPosition,
            wx.DefaultSize,
            0,
        )
        self._connect_but.Enable(False)
        _log_toolbar.AddControl(self._connect_but)

        _log_toolbar.Realize()

        self._mgr.AddPane(
            _rom_toolbar,
            aui.AuiPaneInfo()
            .Name("ROMToolBar")
            .Caption("ROM Editing")
            .ToolbarPane()
            .Top(),
        )
        self._mgr.AddPane(
            _log_toolbar,
            aui.AuiPaneInfo()
            .Name("LogToolBar")
            .Caption("Logging")
            .ToolbarPane()
            .Bottom(),
        )

        self._mgr.Update()

    def _init_menubar(self):
        self._menubar = wx.MenuBar(0)

        # file menu
        self._m_file = wx.Menu()
        self._mi_open = wx.MenuItem(
            self._m_file,
            wx.ID_OPEN,
            "",
            "Open a binary ROM file",
            wx.ITEM_NORMAL,
        )
        self._mi_open.SetBitmap(
            wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_MENU)
        )
        self._m_file.Append(self._mi_open)

        self._mi_save = wx.MenuItem(
            self._m_file,
            wx.ID_SAVE,
            "",
            "Save edited ROM file(s)",
            wx.ITEM_NORMAL,
        )
        self._m_file.Append(self._mi_save)

        self._mi_save_as = wx.MenuItem(
            self._m_file,
            wx.ID_SAVEAS,
            "",
            "Save edited ROM file(s) as",
            wx.ITEM_NORMAL,
        )
        self._mi_save_as.SetBitmap(
            wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS, wx.ART_MENU)
        )
        self._m_file.Append(self._mi_save_as)

        self._mi_file_prefs = self._m_file.Append(
            wx.ID_PREFERENCES,
            "",
            "Open Preferences Dialog",
        )

        self._m_file.AppendSeparator()

        self._mi_exit = wx.MenuItem(
            self._m_file,
            wx.ID_EXIT,
            "",
            "Quit PyRRhic",
            wx.ITEM_NORMAL,
        )
        self._mi_exit.SetBitmap(
            wx.ArtProvider.GetBitmap(wx.ART_QUIT, wx.ART_MENU)
        )
        self._m_file.Append(self._mi_exit)

        self._menubar.Append(self._m_file, "File")

        # window menu
        self._m_window = wx.Menu()
        self._win_menu_items = {}

        self._m_romtables = wx.Menu()
        self._m_ramtables = wx.Menu()

        self._mi_window_close = self._m_window.Append(
            wx.ID_ANY, "Close All", "Close all open windows", wx.ITEM_NORMAL
        )
        self._m_window.AppendSeparator()

        # generate items for all static panels
        for panel_name, panel in self._panels.items():

            # don't allow Console to ever be closed
            if panel_name == "ConsolePanel":
                continue

            pane = self._mgr.GetPane(panel)
            caption = pane.caption

            m_item = self._m_window.AppendCheckItem(wx.ID_ANY, caption)
            m_item.Check(pane.IsShown())
            self._win_menu_items[panel_name] = m_item

        self._m_window.AppendSeparator()
        self._m_window.AppendSubMenu(
            self._m_romtables,
            "ROM Tables",
            "Opened ROM Tables",
        )
        self._m_window.AppendSubMenu(
            self._m_ramtables,
            "RAM Tables",
            "Opened RAM Tables",
        )

        self._menubar.Append(self._m_window, "Window")

        self.SetMenuBar(self._menubar)

    def _init_bindings(self):
        self.Bind(aui.EVT_AUI_PANE_CLOSE, self.OnTogglePane)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_IDLE, self.OnIdle)

        # file menu
        self.Bind(wx.EVT_MENU, self.OnOpenRom, id=self._mi_open.GetId())
        self.Bind(wx.EVT_MENU, self.OnSaveRom, id=self._mi_save.GetId())
        self.Bind(wx.EVT_MENU, self.OnSaveRomAs, id=self._mi_save_as.GetId())
        self.Bind(
            wx.EVT_MENU, self.OnPreferences, id=self._mi_file_prefs.GetId()
        )
        self.Bind(wx.EVT_MENU, self.OnClose, id=self._mi_exit.GetId())

        # window menu
        self.Bind(
            wx.EVT_MENU, self.OnCloseWindows, id=self._mi_window_close.GetId()
        )

        for item in self._win_menu_items.values():
            self.Bind(wx.EVT_MENU, self.OnTogglePane, id=item.GetId())

        # ROM toolbar
        self.Bind(wx.EVT_TOOL, self.OnOpenRom, id=self._tb_open.GetId())
        self.Bind(wx.EVT_TOOL, self.OnSaveRom, id=self._tb_save.GetId())
        self.Bind(wx.EVT_TOOL, self.OnSaveRomAs, id=self._tb_save_as.GetId())

        # Logger toolbar
        self.Bind(
            wx.EVT_TOOL, self.OnRefreshInterfaces, id=self._refresh_but.GetId()
        )
        self._iface_choice.Bind(wx.EVT_CHOICE, self.OnSelectInterface)
        self._protocol_choice.Bind(wx.EVT_CHOICE, self.OnSelectProtocol)
        self._connect_but.Bind(wx.EVT_BUTTON, self.OnConnectButton)

        # statusbar timers
        self.Bind(wx.EVT_TIMER, self._pop_left_status, self._left_status_timer)
        self.Bind(
            wx.EVT_TIMER, self._pop_center_status, self._center_status_timer
        )
        self.Bind(
            wx.EVT_TIMER, self._pop_right_status, self._right_status_timer
        )

        # pubsub subscriptions
        pub.subscribe(self._enable_livetune, "editor.livetune.enable")
        pub.subscribe(self.toggle_table, "editor.table.toggle")
        pub.subscribe(self.refresh_tree, "editor.table.rom.change")
        pub.subscribe(self._on_connection, "comms.connection.change")
        pub.subscribe(self.refresh_tree, "preferences.updated")
        pub.subscribe(self.update_freq, "comms.freq.updated")

        pub.subscribe(self._push_status, "status.push")
        pub.subscribe(self._error_box, "error.push")

    def _enable_livetune(self, livetune=None):
        userlvl = self._controller.Preferences["UserLevel"].Value

        enable = livetune is not None

        # only allow livetune UI for superdev user level
        if userlvl < UserLevel.Superdev:
            enable = False

        args = (self._controller, livetune) if enable else ()
        self._panels['LiveTunePanel'].initialize(*args)

    def _info_box(self, title, message):
        modal_dialog_ok(self, title, message, wx.ICON_INFORMATION)

    def _warning_box(self, title, message):
        modal_dialog_ok(self, title, message, wx.ICON_WARNING)

    def _error_box(self, title, message):
        modal_dialog_ok(self, title, message, wx.ICON_ERROR)

    def _push_status(
        self, left=None, center=None, right=None, temporary=False
    ):
        """Push text to the corresponding portion of the status bar.

        All arguments are optional.

        Use the ``temporary`` keyword to indicate that the text pushed to the
        status bar should be popped after a small delay.

        Args:
            left (str): text to push to the left part of the status bar
            center (str): text to push to the center part of the status bar
            right (str): text to push to the right part of the status bar
            temporary (bool): indication that the status(es) pushed to the
                status bar should be popped after a small delay
        """

        if isinstance(left, str):
            self.PushStatusText(left, 0)
            if temporary:
                self._left_status_timer.StartOnce(self._temp_status_delay)

        if isinstance(center, str):
            self.PushStatusText(center, 1)
            if temporary:
                self._center_status_timer.StartOnce(self._temp_status_delay)

        if isinstance(right, str):
            self.PushStatusText(right, 2)
            if temporary:
                self._right_status_timer.StartOnce(self._temp_status_delay)

    def _pop_left_status(self, event=None):
        self.PopStatusText(0)

    def _pop_center_status(self, event=None):
        self.PopStatusText(1)

    def _pop_right_status(self, event=None):
        self.PopStatusText(2)

    def toggle_table(self, table):

        if table.Panel is not None:
            pane = self._mgr.GetPane(table.Panel)
            pane.Show(not pane.IsShown())
            self._mgr.Update()

            # need to re-set max size every time pane is shown
            table.Panel.Parent.SetMaxClientSize(table.Panel.GetMaxSize())

        else:
            pane_name = table.PanelTitle
            p = TablePanel(self, pane_name, table)
            table.Panel = p
            start_pos = self.GetScreenPosition()

            # calculate pane (not panel) total size
            # scr_x = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
            # scr_y = wx.SystemSettings.GetMetric(wx.SYS_HSCROLL_Y)
            max_size = (p.GetSize()[0], p.GetSize()[1])

            self._mgr.AddPane(
                p,
                wx.aui.AuiPaneInfo()
                .Name(pane_name)
                .Caption(pane_name)
                .CloseButton()
                .PaneBorder()
                .Float()
                .Resizable()
                .FloatingPosition(start_pos)
                .Show(),
            )
            self._mgr.Update()

            # need to set the AUIFloatingPane max size here, since the
            # aui.AuiPaneInfo.MaxSize() approach doesn't seem to work
            p.Parent.SetClientSize(max_size)
            p.Parent.SetMaxClientSize(max_size)

    def refresh_tree(self, obj=None):
        for item in self._save_items:
            enabled = bool(self._controller.ModifiedROMs)
            if isinstance(item, wx.MenuItem):
                item.Enable(enabled)
            elif isinstance(item, aui.AuiToolBarItem):
                item.SetState(
                    aui.AUI_BUTTON_STATE_NORMAL
                    if enabled
                    else aui.AUI_BUTTON_STATE_DISABLED
                )
            self.Refresh()

    def OnPreferences(self, event):
        dlg = PrefsDialog(self, self._controller.Preferences)
        dlg.ShowModal()
        dlg.Destroy()

    def OnTogglePane(self, event=None):

        # determine which pane to toggle

        # menu item was clicked
        if event.GetEventType() == wx.wxEVT_MENU:
            _name_map = {
                x.GetId(): y
                for x, y in zip(
                    self._win_menu_items.values(), self._panels.items()
                )
            }
            panel_name, panel = _name_map[event.GetId()]
            pane = self._mgr.GetPane(panel)

        # close button on pane itself was clicked
        elif event.GetEventType() == aui.wxEVT_AUI_PANE_CLOSE:
            pane = event.GetPane()
            panel = pane.window
            panel_name = panel.Name

        # shouldn't ever reach here... do nothing if so
        else:
            return

        menu_item = self._win_menu_items[panel_name]
        show_pane = not pane.IsShown()
        menu_item.Check(show_pane)
        pane.Show(show_pane)
        pane.BestSize(panel.GetBestSize())

        # handle panes in a (auto)notebook
        if panel and isinstance(panel.Parent, aui.AuiNotebook):
            nb = panel.Parent
            nb_pane = self._mgr.GetPane(nb)
            idx = nb.GetPageIndex(panel)
            nb.HidePage(idx, not show_pane)

            # float panes last shown in a notebook that has since been closed
            if show_pane and not nb_pane.IsShown():
                pane.Float()

            elif show_pane:
                nb.SetSelection(idx, True)

        # commit changes to AUI manager
        self._mgr.Update()

    def OnCloseWindows(self, event=None):
        pass

    # ROM Editor Events
    def OnClose(self, event):
        self._controller.save_prefs()
        self._mgr.UnInit()
        self.Destroy()

    def OnOpenRom(self, event):
        if not self._controller.DefsValid:
            self.warning_box(
                "No Definitions Loaded",
                "No definitions loaded! Ensure definition paths are correct",
            )
            return

        dlg = wx.FileDialog(
            self,
            "Open ROM File",
            wildcard=_rom_wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE,
        )
        result = dlg.ShowModal()

        if result == wx.ID_OK:
            fpaths = dlg.GetPaths()

            for fpath in fpaths:
                # TODO: sanity check files here?
                self._controller.open_rom(fpath)

            pub.sendMessage("editor.table.rom.change")

    def OnSaveRom(self, event):

        # TODO: show dialog allowing user to select which ROMs to save

        num_saved = 0
        for rom in self._controller.ModifiedROMs.values():
            rom.save()
            num_saved += 1

        if num_saved:
            self.push_status("Saved {} ROMs".format(num_saved))
            self.refresh_tree()

    def OnSaveRomAs(self, event):

        # TODO: show dialog allowing user to select which ROMs to save

        num_saved = 0
        for rom in self._controller.ModifiedROMs.values():
            start_path = os.path.dirname(rom.Path)
            start_fname = os.path.basename(rom.Path)
            with wx.FileDialog(
                self,
                "Save ROM {}".format(start_fname),
                defaultDir=start_path,
                defaultFile=start_fname,
                wildcard=_rom_wildcard,
                style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            ) as dlg:

                result = dlg.ShowModal()
                if result == wx.ID_OK:
                    rom.save(dlg.GetPath())
                    num_saved += 1

        if num_saved:
            self.push_status("Saved {} ROMs".format(num_saved))
            self.refresh_tree()

    # Logger Events
    def _enable_log_toolbar(self, enable=True, connect=False):
        if enable:
            self._refresh_but.SetState(aui.AUI_BUTTON_STATE_NORMAL)
            self._iface_choice.Enable()
            self._protocol_choice.Enable()
            if connect:
                self._connect_but.Enable()
        else:
            self._refresh_but.SetState(aui.AUI_BUTTON_STATE_DISABLED)
            self._iface_choice.Disable()
            self._protocol_choice.Disable()
            if connect:
                self._connect_but.Disable()

    def _on_connection(self, connected=True, translator=None):
        self._connect_but.SetLabelText(
            _disconnect_text if connected else _connect_text
        )
        self._enable_log_toolbar(enable=not connected)
        self._connect_but.Enable()

        if connected:
            self._panels["LogParamPanel"].initialize(translator)
            self._push_status(
                left="Connected to ECU: {}".format(
                    translator.Definition.LoggerDef.Identifier
                )
            )
            self._push_status(left=_connect_success_text, temporary=True)
        else:
            self._panels["LogParamPanel"].clear()
            self._pop_left_status()

    def OnRefreshInterfaces(self, event=None):
        self._iface_choice.Clear()
        self._controller.refresh_interfaces()
        self._iface_choice.Append(
            [_iface_text] + list(self._controller.AvailableInterfaces.keys())
        )
        self._iface_choice.SetSelection(len(self._iface_choice.Items) - 1)
        self.OnSelectInterface()

    def OnSelectInterface(self, event=None):
        self._protocol_choice.Clear()
        self._protocol_choice.Append(_protocol_text)

        if self._iface_choice.GetStringSelection() != _iface_text:
            self._protocol_choice.Append(
                self._controller.get_supported_protocols(
                    self._iface_choice.GetStringSelection()
                )
            )
            self._protocol_choice.SetSelection(
                len(self._protocol_choice.Items) - 1
            )
        else:
            self._protocol_choice.SetSelection(0)

        self.OnSelectProtocol()

    def OnSelectProtocol(self, event=None):
        self._connect_but.Enable(
            self._protocol_choice.GetStringSelection() != _protocol_text
        )

    def OnConnectButton(self, event):
        # Attempt a logger connection
        if self._connect_but.GetLabelText() == _connect_text:

            # lock UI controls
            self._enable_log_toolbar(enable=False, connect=True)
            self._connect_but.SetLabelText(_connecting_text)

            # spawn a logger thread
            iface = self._iface_choice.GetStringSelection()
            protocol = self._protocol_choice.GetStringSelection()
            pub.sendMessage(
                "comms.spawn", interface_name=iface, protocol_name=protocol
            )

        # close an already existing logger connection
        else:
            # lock UI controls
            self._enable_log_toolbar(enable=False, connect=True)
            self._connect_but.SetLabelText(_disconnecting_text)
            pub.sendMessage("comms.kill")

    def update_freq(self, avg_freq):
        freq_str = "Query Freq: {: >6.2f} Hz".format(avg_freq)
        self._statusbar.SetStatusText(freq_str, i=2)

    def OnIdle(self, event):
        pub.sendMessage("comms.check")
        event.RequestMore()  # ensure UI updates continuously
