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
from logging import Formatter, getLogger, CRITICAL, ERROR, WARNING, INFO, DEBUG

from .panelsBase import bLogPanel
from .wxutils import WxEventLogHandler, EVT_LOG

_std_formatter = Formatter(
    '{module}/{funcName}: {message}',
    '%H:%M:%S',
    style='{'
)

_debug_formatter = Formatter(
    '{module}/{funcName} [{filename}:{lineno}]: {message}',
    '%H:%M:%S',
    style='{'
)

class LogPanel(bLogPanel):
    def __init__(self, *args, **kwargs):
        super(LogPanel, self).__init__(*args, **kwargs)
        self._handler = WxEventLogHandler(self)
        getLogger().addHandler(self._handler)

        _lvl_map = {
            CRITICAL: 0,
            ERROR   : 1,
            WARNING : 2,
            INFO    : 3,
            DEBUG   : 4,
        }
        log_lvl = _lvl_map[getLogger().getEffectiveLevel()]
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

        start_pos = self._log_text.GetLastPosition()
        self._log_text.AppendText('{}\n'.format(msg))
        end_pos = self._log_text.GetLastPosition()

        self._log_text.SetStyle(start_pos, end_pos, style)
        self._log_text.ShowPosition(end_pos)

    def OnSetLogLevel(self, event):
        _lvl_map = [CRITICAL, ERROR, WARNING, INFO, DEBUG]
        lvl = _lvl_map[self._log_level.GetSelection()]
        getLogger().setLevel(lvl)

        fmt = _debug_formatter if lvl < INFO else _std_formatter
        self._handler.setFormatter(fmt)

    def OnClearLog(self, event):
        self._log_text.Clear()
