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

import os

from collections import OrderedDict
from collections.abc import MutableMapping

class PyrrhicPreference(object):
    "Base preference class"

    def __init__(self, name, **kwargs):
        """Initializer.

        Arguments:
        - name: `str`, internal name of the property

        Keywords [Default]:
        - label [name]: Display name of the property, defaults to internal name
        - help [`''`]: Detailed help text for this property
        - hint [`''`]: Hint text displayed when property is undefined
        - value [`None`]: Initialized value of the property
        - attribs['{}']: Any extra attributes related to this property
        """

        self._name = name
        self._label = kwargs.pop('label', name)
        self._help = kwargs.pop('help', '')
        self._hint = kwargs.pop('hint', '')
        self._value = kwargs.pop('value', None)
        self._attribs = kwargs.pop('attribs', {})

    def __repr__(self):
        return '<{}: {}={}>'.format(
            type(self), self._name, self._value
        )

    def _get_val(self):
        return self._value

    def _set_val(self, val):
        raise NotImplementedError('To be implemented in subclasses')

    @property
    def Name(self):
        return self._name

    @property
    def Label(self):
        return self._label

    @property
    def HelpText(self):
        return self._help

    @property
    def HintText(self):
        return self._hint

    @property
    def Value(self):
        return self._get_val()

    @Value.setter
    def Value(self, val):
        return self._set_val(val)

    @property
    def Attributes(self):
        return self._attribs

    @property
    def Defined(self):
        return self._value is not None

class IntPreference(PyrrhicPreference):
    def _set_val(self, val):
        if isinstance(val, int):
            self._value = val

class UintPreference(PyrrhicPreference):
    def _set_val(self, val):
        if isinstance(val, int) and val >= 0:
            self._value = val

class FloatPreference(PyrrhicPreference):
    def _set_val(self, val):
        if isinstance(val, float):
            self._value = val

class StringPreference(PyrrhicPreference):
    def _set_val(self, val):
        if isinstance(val, str):
            self._value = val

class BoolPreference(PyrrhicPreference):
    def _set_val(self, val):
        if isinstance(val, bool):
            self._value = val

class DirPreference(PyrrhicPreference):
    def _set_val(self, val):
        if isinstance(val, str) and os.path.isdir(val):
            self._value = val

class FilePreference(PyrrhicPreference):
    def _set_val(self, val):
        if isinstance(val, str) and os.path.isfile(val):
            self._value = val

class ColorPreference(PyrrhicPreference):
    """Stores a colour as a 24-bit packed integer in RGB order"""
    def _set_val(self, val):
        # parse 3-tuple of ints
        if (
            isinstance(val, tuple)
            and len(val) == 3
            and all(lambda x: isinstance(x, int), [x for x in val])
        ):
            r, g, b = val
            self._value = (r << 16) + (g << 8) + b
        elif isinstance(val, int):
            self._value = val

    @property
    def ValueTuple(self):
        r, g, b = (
            self._value >> 16 & 0xFF,   # r
            self._value >> 8  & 0xFF,   # g
            self._value       & 0xFF    # b
        )
        return (r, g, b)

class EnumPreference(PyrrhicPreference):
    def __init__(self, name, choices, value=0):
        super(EnumPreference, self).__init__(name, value=value)
        self._choices = choices

    def Value(self, val):
        if isinstance(val, int) and val in range(len(self._choices)):
            self._value = val

    @property
    def Choices(self):
        return self._choices

class CategoryPreference(PyrrhicPreference):
    pass

class PreferenceManager(MutableMapping):
    "Container for global application preferences"

    _default_prefs = [
        CategoryPreference('Editor'),
        DirPreference(
            'ECUFlashRepo',
            label='ECUFlash Definition Repository Location',
            help=(
                'Top-level directory containing one ECUFlash Definition ' +
                'Repository (e.g. .../SubaruDefs/ECUFlash/subaru standard)'
            )
        ),

        CategoryPreference('Logger'),
        FilePreference(
            'RRLoggerDef',
            label='RomRaider Logger Definition File',
            help='XML file containing RomRaider logger definitions',
            attribs={
                'ext': 'xml',
                'fdesc': 'XML Files',
                'fullpath': True,
                'style': 'open',
            }
        ),

        CategoryPreference('Log Colors'),
        ColorPreference(
            'CriticalLogColor',
            label='Critical',
            help='Critical message color in log',
            value=0xc00000
        ),
        ColorPreference(
            'ErrorLogColor',
            label='Error',
            help='Error message color in log',
            value=0xc07d00
        ),
        ColorPreference(
            'WarningLogColor',
            label='Warning',
            help='Warning message color in log',
            value=0xc0c000
        ),
        ColorPreference(
            'InfoLogColor',
            label='Info',
            help='Info message color in log',
            value=0x0
        ),
        ColorPreference(
            'DebugLogColor',
            label='Debug',
            help='Debug message color in log',
            value=0xcccccc
        ),
    ]

    def __init__(self, prefs={}):
        self._prefs = OrderedDict([(x.Name, x) for x in self._default_prefs])

        for pref in prefs:
            if pref in self._default_prefs:
                self._prefs[pref] = prefs[pref]

    def __getitem__(self, key):
        return self._prefs[key]

    def __setitem__(self, key, value):
        self._prefs[key] = value

    def __delitem__(self, key):
        del self._prefs[key]

    def __iter__(self):
        return iter(self._prefs)

    def __len__(self):
        return len(self._prefs)

    def to_json(self):
        raise NotImplementedError('TODO')
