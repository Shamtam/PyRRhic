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

from pubsub import pub

from wx.aui import AUI_BUTTON_STATE_NORMAL, AUI_BUTTON_STATE_DISABLED

from .base import bLoggerFrame

class LoggerFrame(bLoggerFrame):
    def __init__(self, parent, controller):
        self._controller = controller
        super().__init__(parent)

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

        pub.subscribe(self.push_status, 'logger.status')
        pub.subscribe(self.update_freq, 'logger.freq.updated')

        self.OnRefreshInterfaces()
