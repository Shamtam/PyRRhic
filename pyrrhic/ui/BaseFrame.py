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

from .wxutils import modal_dialog_ok

class BaseFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(BaseFrame, self).__init__(*args, **kwargs)
        self._controller = None # initialized in subclasses

    def info_box(self, title, message):
        modal_dialog_ok(self, title, message, wx.ICON_INFORMATION)

    def warning_box(self, title, message):
        modal_dialog_ok(self, title, message, wx.ICON_WARNING)

    def error_box(self, title, message):
        modal_dialog_ok(self, title, message, wx.ICON_ERROR)

    @property
    def Controller(self):
        return self._controller
