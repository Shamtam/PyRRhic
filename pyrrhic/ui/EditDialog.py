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
from .base import bEditDialog

class FloatTextCtrlValidator(wx.Validator):
    """`wx.Validator` to be tied to a `wx.TextCtrl` that accepts float inputs"""

    def Validate(self, parent):
        ctrl = self.GetWindow()
        input = ctrl.GetValue()
        ret = False

        try:
            val = float(input)
        except ValueError:
            ctrl.SetBackgroundColour(wx.Colour(255, 214, 204))
        else:
            ctrl.SetBackgroundColour(wx.Colour(255, 255, 255))
            ret = True

        ctrl.Refresh()
        return ret

    def TransferFromWindow(self):
        return True

    def TransferToWindow(self):
        return True

    def Clone(self):
        return FloatTextCtrlValidator()

class EditDialog(bEditDialog):
    def __init__(self, parent, op='='):
        super().__init__(parent)
        self._input.SetValidator(FloatTextCtrlValidator())
        self.SetAffirmativeId(wx.ID_SAVE)

        _title_map = {
            '=': 'Set Cell(s)',
            '+': 'Add to Cell(s)',
            '*': 'Multiply Cell(s)',
        }

        _label_map = {
            '=': ' = ',
            '+': ' += ',
            '*': ' *= ',
        }

        _value_map = {
            '=': '',
            '+': '0.0',
            '*': '1.0',
        }

        self.SetTitle(_title_map.get(op, 'Edit Cell(s)'))

        label_text = 'Value{}'.format(_label_map.get(op, ' = '))
        self._label.SetLabelText(label_text)
        self._input.SetValue(_value_map.get(op, ''))

    def OnText(self, event):
        self.Validate()

    def OnCancel(self, event):
        event.Skip()

    def OnSave(self, event):
        if self.Validate():
            self.EndModal(wx.ID_SAVE)

    @property
    def Value(self):
        return float(self._input.GetValue())
