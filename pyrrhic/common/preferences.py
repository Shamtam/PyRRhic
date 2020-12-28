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

import json
import logging
import os

from collections.abc import MutableMapping
from pyrrhic.common.enums import UserLevel

from .helpers import PyrrhicJSONSerializable

_logger = logging.getLogger(__name__)

class PyrrhicPreference(PyrrhicJSONSerializable):
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

    def __eq__(self, other):
        return (
            isinstance(other, PyrrhicPreference)
            and other._name == self._name
            and other._value == self._value
        )

    def _get_val(self):
        return self._value

    def _set_val(self, val):
        raise NotImplementedError('To be implemented in subclasses')

    def to_json(self):
        return self._value

    def from_json(self):
        raise NotImplementedError

    def init_from_json(self, val):
        self._value = val

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

    def init_from_json(self, val):
        self._value = bool(val)

class DirPreference(PyrrhicPreference):
    def _set_val(self, val):
        if isinstance(val, str) and os.path.isdir(val):
            self._value = val

    def to_json(self):
        return os.path.abspath(self._value)

    def init_from_json(self, val):
        self._value = val if os.path.isdir(val) else None

class FilePreference(PyrrhicPreference):
    def _set_val(self, val):
        if isinstance(val, str) and os.path.isfile(val):
            self._value = val

    def to_json(self):
        return os.path.abspath(self._value)

    def init_from_json(self, val):
        self._value = val if os.path.isfile(val) else None

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

    def init_from_json(self, val):
        try:
            self._value = int(val) if int(val) in range(0x1000000) else 0
        except Exception:
            self._value = 0

    @property
    def ValueTuple(self):
        r, g, b = (
            self._value >> 16 & 0xFF,   # r
            self._value >> 8  & 0xFF,   # g
            self._value       & 0xFF    # b
        )
        return (r, g, b)

class EnumPreference(PyrrhicPreference):
    def __init__(self, name, choices, values=None, value=0, **kwargs):
        super(EnumPreference, self).__init__(name, value=value, **kwargs)
        self._choices = choices
        self._values = values if values else range(len(choices))

    def _set_val(self, val):
        if isinstance(val, int):
            self._value = val

    def init_from_json(self, val):
        try:
            self._value = int(val) if int(val) in self._values else self._values[0]
        except Exception:
            self._value = 0

    @property
    def Choices(self):
        return self._choices

    @property
    def Values(self):
        return self._values

class CategoryPreference(PyrrhicPreference):
    pass

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
    EnumPreference(
        'UserLevel',
        label='User Level',
        help='Determines which tables are available for viewing/editing',
        choices=[x.name for x in UserLevel],
        values=[x.value for x in UserLevel],
        value=1
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

class PreferenceDecoder(json.JSONDecoder):
    def decode(self, s):
        in_dict = super(PreferenceDecoder, self).decode(s)
        out_dict = {x.Name:x for x in _default_prefs}

        for pref in in_dict:
            if pref in out_dict and in_dict[pref] is not None:
                out_dict[pref].init_from_json(in_dict[pref])

        return out_dict

class PreferenceManager(MutableMapping, PyrrhicJSONSerializable):
    "Container for global application preferences"

    def __init__(self, prefs_fpath=None):
        self._prefs = {x.Name:x for x in _default_prefs}

        prefs = {}
        if prefs_fpath is not None and os.path.isfile(prefs_fpath):
            try:
                with open(prefs_fpath, 'r') as fp:
                    prefs = json.load(fp, cls=PreferenceDecoder)
                    self._prefs = prefs
            except:
                _logger.warn(
                    ('Unable to load preferences from {}. Using default '
                    + 'preferences').format(prefs_fpath)
                )

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
        out_prefs = {}

        for pref in self._prefs.values():

            # no need to export category headers
            if isinstance(pref, CategoryPreference) or not pref.Defined:
                continue

            out_prefs[pref.Name] = pref.to_json()

        return out_prefs
