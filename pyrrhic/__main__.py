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
import sys
import wx

from .common import _log_file
from .common.logging import _file_formatter
from .ui.PyrrhicFrame import PyrrhicFrame
from .controller import PyrrhicController

from . import _debug


class PyrrhicApp(wx.App):
    def OnInit(self):
        self.frame = PyrrhicFrame(None)
        self.controller = PyrrhicController(self.frame)
        self.SetTopWindow(self.frame)
        self.frame.Show()
        return True


with open(_log_file, 'w') as fp:

    # setup root logging
    _root_log = logging.getLogger()
    _handler = logging.FileHandler(_log_file)
    _handler.setFormatter(_file_formatter)
    _root_log.addHandler(_handler)
    _root_log.setLevel(logging.INFO)

    sys.excepthook = (
        lambda t, v, tb:
            _root_log.critical('Unhandled Exception', exc_info=(t, v, tb))
    )

    app = PyrrhicApp(False)

    if _debug:
        _root_log.setLevel(logging.DEBUG)
        from wx.lib.inspection import InspectionTool
        InspectionTool().Show()

    app.MainLoop()
