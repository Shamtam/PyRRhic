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

from pubsub import pub
from wx import propgrid as pg

from .base import PrefsDialog as bPrefsDialog
from ..common.preferences import (
    CategoryPreference, IntPreference, UintPreference, FloatPreference,
    StringPreference, BoolPreference, DirPreference, FilePreference,
    ColorPreference, EnumPreference
)

_logger = logging.getLogger(__name__)

_pref_to_prop_map = {
    CategoryPreference: pg.PropertyCategory,
    IntPreference:      pg.IntProperty,
    UintPreference:     pg.UIntProperty,
    FloatPreference:    pg.FloatProperty,
    StringPreference:   pg.StringProperty,
    BoolPreference:     pg.BoolProperty,
    DirPreference:      pg.DirProperty,
    FilePreference:     pg.FileProperty,
    ColorPreference:    pg.ColourProperty,
    EnumPreference:     pg.EnumProperty,
}

_fileprop_style_map = {
    'open': wx.FD_OPEN,
    'save': wx.FD_SAVE,
    'openmulti': wx.FD_OPEN | wx.FD_MULTIPLE,
}


class PrefsDialog(bPrefsDialog):
    def __init__(self, parent, prefMgr):
        super().__init__(parent)
        self._prefs = prefMgr

        pub.subscribe(self._initialize, 'controller.init')

    def _initialize(self, controller):
        "Initialize PropertyGrid from the associated `PyrrhicPreferences` instance"

        for name in self._prefs:
            pref = self._prefs[name]
            label = pref.Label
            helpStr = pref.HelpText
            hintStr = pref.HintText
            val = pref.Value
            attribs = pref.Attributes

            args = [label, name]

            if isinstance(pref, EnumPreference):
                args.append(pref.Choices)
                args.append(pref.Values)

            prop = _pref_to_prop_map[type(pref)](*args)

            if helpStr:
                prop.SetHelpString(helpStr)
            if hintStr:
                prop.SetHelpText(hintStr)
            if val is not None:
                prop.SetValue(val)

            # handle special attributes
            prop_attrs = {}

            if isinstance(prop, pg.FileProperty):
                # wildcard
                if {'fdesc', 'ext'} <= attribs.keys():
                    wc = '{0} (*.{1})|*.{1}'.format(
                        attribs['fdesc'],
                        attribs['ext']
                    )
                    prop_attrs[pg.PG_FILE_WILDCARD] = wc

                # path
                if 'fullpath' in attribs:
                    prop_attrs[pg.PG_FILE_SHOW_FULL_PATH] = attribs['fullpath']

                # dialog style (i.e. Open, Save, etc.)
                if 'style' in attribs:
                    prop_attrs[pg.PG_FILE_DIALOG_STYLE] = (
                        _fileprop_style_map[attribs['style']]
                    )

            if isinstance(prop, (pg.FileProperty, pg.DirProperty)):
                # dialog title
                prop_attrs[pg.PG_DIALOG_TITLE] = 'Choose {}'.format(label)

            prop.SetAttributes(prop_attrs)

            self._PGM.Append(prop)

    def OnInitialize(self, event):
        for name in self._prefs:
            pref = self._prefs[name]
            label = pref.Label
            helpStr = pref.HelpText
            hintStr = pref.HintText
            val = pref.Value
            attribs = pref.Attributes

            prop = self._PGM.GetPropertyByLabel(label)

            if val is not None:

                # convert 24bit RGB packed int into `ColourPropertyValue`
                if isinstance(prop, pg.ColourProperty):
                    r, g, b = pref.ValueTuple
                    val = pg.ColourPropertyValue(wx.Colour(r, g, b))

                prop.SetValue(val)

    def OnEdit(self, event):
        event.Skip()

    def OnCommit(self, event):
        for name in self._prefs:
            pref = self._prefs[name]

            # skip category headers
            if isinstance(pref, CategoryPreference):
                continue

            prop = self._PGM.GetPropertyByName(
                '{}'.format(name)
            )
            pref.Value = prop.GetValue()

        self._controller.process_preferences()
        self.Hide()

    def OnCancel(self, event):
        self.Hide()
