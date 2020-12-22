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

from logging import Handler, Formatter
import wx

from wx.lib.newevent import NewEvent

LogEvent, EVT_LOG = NewEvent()

class WxEventLogHandler(Handler):
    """`logging.Handler` that emits events to a parent window via `wx.PostEvent`

    The posted event contains the `LogRecord` as the property `record`
    Bind a function to handle the `EVT_LOG` event in the parent window.
    """

    def __init__(self, parent, formatter=None):
        super(WxEventLogHandler, self).__init__()
        self._parent = parent
        self.setFormatter(
            formatter
            if isinstance(formatter, Formatter) else
            Formatter('%(message)s')
        )

    def emit(self, record):
        message = self.format(record)
        wx.PostEvent(self._parent, LogEvent(message=message, record=record))

    def flush(self):
        pass
