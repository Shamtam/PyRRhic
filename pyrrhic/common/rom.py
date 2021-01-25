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
import os

from wx import dataview as dv

from ..common.enums import UserLevel
from ..common.helpers import Container
from .structures import RomTable

_logger = logging.getLogger(__name__)

# Dummy classes to make ViewModel hierarchy easy to handle
class InfoContainer(Container):
    pass
class TableCategoryContainer(Container):
    pass
class TableContainer(Container):
    pass
class LogParamContainer(Container):
    pass

class Rom(object):
    def __init__(self, fpath, raw_data, definition):
        self._filepath = fpath
        self._orig_bytes = raw_data
        self._bytes = bytearray(raw_data)
        self._definition = definition

        # dict containing top-level information of the ROM
        self._info = InfoContainer(self)

        # nested `dict` keyed as follows
        # tables[<category>][<name>]
        self._tables = TableCategoryContainer(self)

        # nested `dict` keyed as follows:
        # log_params[<std|extended>][<name>]
        self._log_params = LogParamContainer(self)

        self._initialize()

    def _initialize(self):
        _logger.debug(
            'Initializing ROM Definition for {}'.format(self._filepath)
        )

        editor_def = self._definition.EditorDef
        logger_def = self._definition.LoggerDef

        self._info = InfoContainer(
            self, {k:v for k, v in editor_def.DisplayInfo.items()}
        )

        tables = TableCategoryContainer(self)
        for tab in editor_def.AllTables.values():

            # only consider tables that are fully defined
            if not tab.FullyDefined:
                continue

            cat = tab.Category
            if cat not in tables:
                tables[cat] = TableContainer(tables, name=cat)

            name = tab.Name
            if name in tables:
                _logger.warn(
                    ('Duplicate table definition {}:{}. '
                    + 'Ignoring duplicate definition').format(cat, name)
                )
                continue

            tables[cat][name] = RomTable(self, tab)

        self._tables = tables

    @property
    def OriginalBytes(self):
        '`bytes` object containing the original raw ROM binary'
        return self._orig_bytes

    @property
    def Bytes(self):
        'Mutable `bytearray` object containing the current raw ROM binary'
        return self._bytes

    @property
    def Info(self):
        return self._info

    @property
    def Path(self):
        return self._filepath

    @property
    def Tables(self):
        return self._tables

    @property
    def IsModified(self):
        return self._orig_bytes != self._bytes
