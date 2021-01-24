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

from wx.aui import AUI_BUTTON_STATE_NORMAL, AUI_BUTTON_STATE_DISABLED

from .base import bLoggerFrame

class LoggerFrame(bLoggerFrame):
    def __init__(self, parent, controller):
        self._controller = controller
        super(LoggerFrame, self).__init__(parent)

        self._connect_text = 'Connect'
        self._disconnect_text = 'Disconnect'
        self._connect_but.SetLabelText(self._connect_text)

        self._iface_text = 'Interface Selection'
        self._protocol_text = 'Protocol Selection'

        self._temp_status_delay = 3000 # ms
        self._left_status_timer = wx.Timer(self)
        self._center_status_timer = wx.Timer(self)
        self._right_status_timer = wx.Timer(self)

        self.Bind(
            wx.EVT_TIMER, self._pop_left_status, self._left_status_timer
        )
        self.Bind(
            wx.EVT_TIMER, self._pop_center_status, self._center_status_timer
        )
        self.Bind(
            wx.EVT_TIMER, self._pop_right_status, self._right_status_timer
        )

        self.OnRefreshInterfaces()

    def _enable_toolbar_controls(self, enable=True, connect=False):
        if enable:
            self._refresh_but.SetState(AUI_BUTTON_STATE_NORMAL)
            self._iface_choice.Enable()
            self._protocol_choice.Enable()
            if connect:
                self._connect_but.Enable()
        else:
            self._refresh_but.SetState(AUI_BUTTON_STATE_DISABLED)
            self._iface_choice.Disable()
            self._protocol_choice.Disable()
            if connect:
                self._connect_but.Disable()

    def _disable_toolbar_controls(self, connect=False):
        self._enable_toolbar_controls(enable=False, connect=connect)

    def _pop_left_status(self, event=None):
        self._statusbar.PopStatusText(field=0)

    def _pop_center_status(self, event=None):
        self._statusbar.PopStatusText(field=1)

    def _pop_right_status(self, event=None):
        self._statusbar.PopStatusText(field=2)

    def refresh_gauges(self):
        self._gauge_panel.refresh_gauges()

    def update_gauges(self, params):
        self._gauge_panel.update_gauges(params)

    def on_connection(self, connected=True, translator=None):
        text = self._disconnect_text if connected else self._connect_text
        self._connect_but.SetLabelText(text)
        self._connect_but.Enable()
        self._enable_toolbar_controls(enable=not connected)

        if connected:
            self._param_panel.initialize(translator)
            self.push_status(left='ID: {}'.format(translator.Definition.Identifier))
            self.push_status(left='Connected', temporary=True)
        else:
            self._param_panel.clear()
            self._pop_left_status()

    def push_status(self, left=None, center=None, right=None, temporary=False):
        """Push text to the corresponding portion of the status bar.

        Pass a `str` to the `left`, `center` and `right` keywords to set
        the text of the corresponding part of the statusbar. Use the
        `temporary` keyword to indicate that the text pushed to the
        status bar should be popped after a small delay (which is held
        in the local binding `LoggerFrame._temp_status_delay`).
        """

        if isinstance(left, str):
            self._statusbar.PushStatusText(left, field=0)
            if temporary:
                self._left_status_timer.StartOnce(self._temp_status_delay)

        if isinstance(center, str):
            self._statusbar.PushStatusText(center, field=1)
            if temporary:
                self._center_status_timer.StartOnce(self._temp_status_delay)

        if isinstance(right, str):
            self._statusbar.PushStatusText(right, field=2)
            if temporary:
                self._right_status_timer.StartOnce(self._temp_status_delay)

    def update_freq(self, avg_freq):
        freq_str = 'Query Freq: {: >6.2f} Hz'.format(avg_freq)
        self._statusbar.SetStatusText(freq_str, i=2)

    def OnRefreshInterfaces(self, event=None):
        self._iface_choice.Clear()
        self._controller.refresh_interfaces()
        self._iface_choice.Append(
            [self._iface_text] +
            list(self._controller.AvailableInterfaces.keys())
        )
        self._iface_choice.SetSelection(len(self._iface_choice.Items) - 1)
        self.OnSelectInterface()

    def OnSelectInterface(self, event=None):
        self._protocol_choice.Clear()
        self._protocol_choice.Append(self._protocol_text)

        if self._iface_choice.GetStringSelection() != self._iface_text:
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
            self._protocol_choice.GetStringSelection() != self._protocol_text
        )

    def OnConnectButton(self, event):
        # Attempt a logger connection
        if self._connect_but.GetLabelText() == self._connect_text:

            # lock UI controls
            self._disable_toolbar_controls(connect=True)
            self._connect_but.SetLabelText('Connecting...')

            # spawn a logger thread
            iface = self._iface_choice.GetStringSelection()
            protocol = self._protocol_choice.GetStringSelection()
            self._controller.spawn_logger(iface, protocol)

        # close an already existing logger connection
        else:
            # lock UI controls
            self._disable_toolbar_controls(connect=True)
            self._connect_but.SetLabelText('Disconnecting...')

            self._controller.kill_logger()

    def OnIdle(self, event):
        self._controller.check_logger()
        event.RequestMore() # ensure UI updates continuously
