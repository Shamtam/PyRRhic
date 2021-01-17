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

from ..common.enums import UserLevel, LogParamType
from .structures import RomTable, LogParam

_logger = logging.getLogger(__name__)

class Rom(object):
    def __init__(self, fpath, raw_data, definition):
        self._filepath = fpath
        self._bytes = raw_data
        self._definition = definition

        # dict containing top-level information of the ROM
        self._info = {}

        # nested `dict` keyed as follows
        # tables[<category>][<name>]
        self._tables = {}

        # nested `dict` keyed as follows:
        # log_params[<std|extended>][<name>]
        self._log_params = {}

        self._initialize()

    def _initialize(self):
        _logger.debug(
            'Initializing ROM Definition for {}'.format(self._filepath)
        )

        editor_def = self._definition.EditorDef
        logger_def = self._definition.LoggerDef

        self._info = {k:v for k, v in editor_def.DisplayInfo.items()}

        tables = {}
        for tab in editor_def.AllTables.values():

            # only consider tables that are fully defined
            if not tab.FullyDefined:
                continue

            cat = tab.Category
            if cat not in tables:
                tables[cat] = {}

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
    def Bytes(self):
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

class PyrrhicRomViewModel(dv.PyDataViewModel):

    def __init__(self, controller):
        super(PyrrhicRomViewModel, self).__init__()
        self._controller = controller
        self._roms = controller.LoadedROMs

    def GetColumnCount(self):
        return 1

    def GetColumnType(self, col):
        return 'string'

    def GetChildren(self, item, children):

        usrlvl = UserLevel(self._controller.Preferences['UserLevel'].Value)

        # root node, return all ROMs
        if not item:
            for fpath in self._roms:
                rom = self._roms[fpath]
                children.append(self.ObjectToItem(rom))
            return len(self._roms)

        node = self.ItemToObject(item)

        # ROM node, return info and table categories
        if isinstance(node, Rom):

            # generate info container node
            obj = ('infocontainer', (node, 'Info'))
            children.append(self.ObjectToItem(obj))

            # generate category nodes
            categories = []
            for category in node.Tables:
                tables = node.Tables[category].values()

                # only append category if all of its tables fall within
                # the currently selected user level
                if not all(
                    [usrlvl.value < x.Definition.Level.value  for x in tables]
                ):
                    categories.append(
                        self.ObjectToItem(('category', (node, category)))
                    )
            for x in categories: children.append(x)

            return len(categories) + 1

        # sub-node, either info container, category, or table
        elif isinstance(node, tuple):
            node_type, data = node

            # generate info nodes
            if node_type == 'infocontainer':
                for k, v in data[0].Info.items():
                    obj = ('info', (data[0], '{}: {}'.format(k, v)))
                    children.append(self.ObjectToItem(obj))
                return len(data[0].Info)

            # category nodes' children are tables
            if node_type == 'category':
                tables = []
                rom, category = data
                for tab in rom.Tables[category]:
                    table = rom.Tables[category][tab]
                    if (table.Definition.Level.value <= usrlvl.value):
                        tables.append(self.ObjectToItem(
                            ('table', (node, category, tab)))
                        )
                for x in tables: children.append(x)
                return len(tables)

        return 0

    def GetAttr(self, item, col, attr):
        if not item:
            return False

        node = self.ItemToObject(item)

        if isinstance(node, Rom):
            attr.SetBold(True)
            return True

        elif isinstance(node, tuple):
            node_type, data = node

            if node_type == 'info':
                attr.SetItalic(True)
                return True

        return False

    def IsContainer(self, item):

        # root is a container
        if not item:
            return True

        node = self.ItemToObject(item)

        if isinstance(node, Rom):
            return True
        if isinstance(node, tuple) and node[0] in ['infocontainer', 'category']:
            return True

        return False

    def HasDefaultCompare(self):
        return True

    def Compare(self, item1, item2, column, ascending):
        node1 = self.ItemToObject(item1)
        node2 = self.ItemToObject(item2)

        if all(isinstance(x, tuple) for x in [node1, node2]):
            node1_type, data1 = node1
            node2_type, data2 = node2

            # sort categories alphabetically
            if(
                all(x == 'category' for x in [node1_type, node2_type]) or
                all(x == 'table' for x in [node1_type, node2_type]) or
                all(x == 'info' for x in [node1_type, node2_type])
            ):
                return 1 if ascending == (data1[-1] > data2[-1]) else -1
            elif node1_type == 'infocontainer' and node2_type == 'category':
                return -1 if ascending else 1
            elif node2_type == 'infocontainer' and node1_type == 'category':
                return 1 if ascending else -1

        return 0

    def GetParent(self, item):

        # root has no parent
        if not item:
            return dv.NullDataViewItem

        node = self.ItemToObject(item)

        # ROMs have no parent
        if isinstance(node, Rom):
            return dv.NullDataViewItem

        elif isinstance(node, tuple):
            node_type, data = node

            if node_type in ['infocontainer', 'category']:
                parent = data[0]
            elif node_type == 'info':
                parent = ('infocontainer', data)
            elif node_type == 'table':
                parent = data[:2]

            else:
                raise ValueError('Unrecognized node')

            return self.ObjectToItem(parent)

    def HasValue(self, item, col):
        if col > 0:
            return False
        return True

    def GetValue(self, item, col):
        assert col == 0, "Unexpected column for PyrrhicRomViewModel"

        node = self.ItemToObject(item)

        if isinstance(node, Rom):
            return '{} ({})'.format(
                os.path.basename(node.Path),
                node.Path
            )
        elif isinstance(node, tuple):
            node_type, data = node
            return data[-1]

        return ''

class PyrrhicLoggerViewModel(dv.PyDataViewModel):

    def __init__(self, log_def, selected=False):
        super(PyrrhicLoggerViewModel, self).__init__()
        self._def = log_def
        self._selected = selected

    def GetColumnCount(self):
        return 1

    def GetColumnType(self, col):
        return 'string'

    def GetChildren(self, item, children):

        # root node, add param categories
        if not item:

            children.append(self.ObjectToItem(
                ('params', None, self._def.AllParameters)
            ))
            children.append(self.ObjectToItem(
                ('switches', None, self._def.AllSwitches)
            ))
            children.append(self.ObjectToItem(
                ('dtcs', None, self._def.AllDTCodes)
            ))
            return 3

        node = self.ItemToObject(item)

        if isinstance(node, tuple):
            node_type, parent, data = node

            out_items = []
            if node_type in ['params', 'switches', 'dtcs']:
                for par in data.values():
                    if par.Enabled == self._selected and par.Valid:
                        out_items.append(self.ObjectToItem(
                            (par.ParamType, node, par)
                        ))
                for x in out_items: children.append(x)
                return len(out_items)

        return 0

    def GetAttr(self, item, col, attr):
        if not item:
            return False

        node = self.ItemToObject(item)

        if isinstance(node, tuple):
            node_type, parent, data = node
            if node_type in ['params', 'switches', 'dtcs']:
                attr.SetBold(True)
                return True

        return False

    def IsContainer(self, item):

        # root is a container
        if not item:
            return True

        node = self.ItemToObject(item)

        if isinstance(node, tuple):
            node_type, parent, data = node
            if node_type in ['params', 'switches', 'dtcs']:
                return True

        return False

    def HasDefaultCompare(self):
        return True

    def Compare(self, item1, item2, column, ascending):
        node1 = self.ItemToObject(item1)
        node2 = self.ItemToObject(item2)

        if all(isinstance(x, tuple) for x in [node1, node2]):
            node1_type, parent1, data1 = node1
            node2_type, parent2, data2 = node2

            _type_map = {
                'params': 1,
                'switches': 2,
                'dtcs': 3,
            }

            if all(isinstance(x, LogParamType) for x in [node1_type, node2_type]):
                if node1_type == node2_type:
                    return 1 if ascending == (data1.Name > data2.Name) else -1
                else:
                    return 1 if node1_type == LogParamType.STD_PARAM else -1
            elif all(x in _type_map for x in [node1_type, node2_type]):
                n1 = _type_map[node1_type]
                n2 = _type_map[node2_type]
                return 1 if ascending == (n1 > n2) else -1
            else:
                return 0

        return 0

    def GetParent(self, item):

        # root has no parent
        if not item:
            return dv.NullDataViewItem

        node = self.ItemToObject(item)

        if isinstance(node, tuple):
            node_type, parent, data = node

            # categories have no parent
            if node_type in ['params', 'switches', 'dtcs']:
                return dv.NullDataViewItem
            elif isinstance(node_type, LogParamType):
                return self.ObjectToItem(parent)
            else:
                raise ValueError('Unrecognized node')

    def HasValue(self, item, col):
        if col > 0:
            return False
        return True

    def GetValue(self, item, col):
        assert col == 0, "Unexpected column for PyrrhicLoggerViewModel"

        node = self.ItemToObject(item)

        if isinstance(node, tuple):
            node_type, parent, data = node
            _type_map = {
                'params': 'Parameters',
                'switches': 'Switches',
                'dtcs': 'Diagnostic Trouble Codes',
            }
            if node_type in _type_map:
                return _type_map[node_type]
            elif isinstance(node_type, LogParamType):
                return '{} [{}]'.format(data.Name, data.Identifier)

        return ''
