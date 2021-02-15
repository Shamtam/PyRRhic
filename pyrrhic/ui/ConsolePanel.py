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

from logging import getLogger, CRITICAL, ERROR, WARNING, INFO, DEBUG
from pubsub import pub

from ..common.logging import _console_formatter, _lvl_map
from .panelsBase import bConsolePanel
from .wxutils import WxEventLogHandler, EVT_LOG

class ConsolePanel(bConsolePanel):
    def __init__(self, *args, **kwargs):
        super(ConsolePanel, self).__init__(*args, **kwargs)
        self._handler = WxEventLogHandler(self, _console_formatter)
        getLogger().addHandler(self._handler)
        self._handler.setLevel(INFO)
        log_lvl = _lvl_map[self._handler.level]
        self._log_level.SetSelection(log_lvl)

        self.Bind(EVT_LOG, self.OnLogRecord)

    def OnLogRecord(self, event):
        rec = event.record
        msg = event.message
        lvl = rec.levelno

        _color_pref_map = {
            CRITICAL: 'CriticalLogColor',
            ERROR   : 'ErrorLogColor',
            WARNING : 'WarningLogColor',
            INFO    : 'InfoLogColor',
            DEBUG   : 'DebugLogColor',
        }

        _lvl_to_color = lambda x: self.Parent.Controller.Preferences[_color_pref_map[x]].ValueTuple
        style = wx.TextAttr(_lvl_to_color(lvl))
        self._log_text.SetDefaultStyle(style)
        self._log_text.AppendText('{}\n'.format(msg))
        self._log_text.ShowPosition(self._log_text.GetLastPosition())

    def OnSetLogLevel(self, event):
        _lvl_map = [CRITICAL, ERROR, WARNING, INFO, DEBUG]
        lvl = _lvl_map[self._log_level.GetSelection()]
        self._handler.setLevel(lvl)

    def OnClearLog(self, event):
        self._log_text.Clear()
