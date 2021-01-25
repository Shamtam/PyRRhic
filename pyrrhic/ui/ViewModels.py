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

import os
import wx

from ..common.enums import UserLevel
from ..common.helpers import Container
from ..common.rom import Rom, InfoContainer, TableContainer
from ..common.structures import RomTable

from natsort import natsort_key, ns
from wx import dataview as dv

# class ViewNode(object):
#     """Dummy class to facilitate persistent objects for mapping simple
#     arbitrary objects to/from items in a `PyDataViewModel`"""

#     def __init__(self, name, parent, data=None):
#         self._name = name
#         self._parent = parent
#         self._data = data

#     def __repr__(self):
#         return '<ViewNode {}, {}>'.format(
#             self._name,
#             repr(self._data) if self._data else 'No Data'
#         )

#     @property
#     def Name(self):
#         return self._name

#     @property
#     def Parent(self):
#         return self._parent

#     @property
#     def Data(self):
#         return self._data

class OptionalToggleRenderer(dv.DataViewCustomRenderer):
    """Extension of `DataViewToggleRenderer` that optionally omits the checkbox

    A checkbox will only be rendered if the underlying model value is a `bool`.
    """

    def __init__(self, **kw):
        kw['varianttype'] = 'long'
        dv.DataViewCustomRenderer.__init__(self, **kw)
        self._value = -1

        # get default checkbox size
        _checkbox = wx.CheckBox(wx.GetTopLevelWindows()[0])
        self._size = _checkbox.Size.GetHeight()
        _checkbox.Destroy()

    def SetValue(self, value):
        self._value = value
        return True

    def GetValue(self):
        return self._value

    def GetSize(self):
        return wx.Size(self._size, self._size)

    def Render(self, rect, dc, state):

        render = wx.RendererNative.Get()
        parent = self.GetOwner().GetOwner()

        if self._value != -1:
            render.DrawCheckBox(
                parent,
                dc,
                wx.Rect(rect.GetTopLeft(), wx.Size(self._size, self._size)),
                wx.CONTROL_CHECKED if self._value else wx.CONTROL_CURRENT
            )
        return True

    def ActivateCell(self, rect, model, item, col, mouseEvent):
        if self._value != -1:
            val = True if self._value else False
            model.SetValue(not val, item, col)
            model.ItemChanged(item)
        return True

    def HasEditorCtrl(self):
        return False

    @property
    def Size(self):
        return self._size

class RomViewModel(dv.PyDataViewModel):

    def __init__(self, controller):
        super(RomViewModel, self).__init__()
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
            children.append(self.ObjectToItem(node.Info))

            # generate category nodes
            categories = []
            for category in node.Tables:
                container = node.Tables[category]
                tables = container.values()

                # only append category if some of its tables fall within
                # the currently selected user level
                if not all(
                    [usrlvl.value < x.Definition.Level.value  for x in tables]
                ):
                    categories.append(self.ObjectToItem(container))
            for x in categories: children.append(x)

            return len(categories) + 1

        # info container node
        elif isinstance(node, InfoContainer):

            for k, v in node.items():
                children.append(self.ObjectToItem('{}: {}'.format(k, v)))
            return len(node)

        # category node
        elif isinstance(node, TableContainer):
            for tab in node.values():
                children.append(self.ObjectToItem(tab))
            return len(node)

        return 0

    def GetAttr(self, item, col, attr):
        if not item:
            return False

        node = self.ItemToObject(item)

        if isinstance(node, Rom):
            attr.SetItalic(True)
            attr.SetBold(node.IsModified)
            return True

        # node is an info entry
        elif isinstance(node, str):
            attr.SetItalic(True)
            return True

        # node is a category
        elif isinstance(node, TableContainer):
            attr.SetBold(
                any([x.IsModified for x in node.values()])
            )
            return True

        # mark modified tables bold
        elif isinstance(node, RomTable):
            attr.SetBold(node.IsModified)
            return True

        return False

    def IsContainer(self, item):

        # root is a container
        if not item:
            return True

        node = self.ItemToObject(item)

        return (
            True if isinstance(node, (Rom, InfoContainer, TableContainer))
            else False
        )

    def HasDefaultCompare(self):
        return True

    def Compare(self, item1, item2, column, ascending):
        node1 = self.ItemToObject(item1)
        node2 = self.ItemToObject(item2)
        nodes = [node1, node2]

        # sort ROMs by filepath
        if all(isinstance(x, Rom) for x in nodes):
            n1 = natsort_key(node1.Path, alg=ns.PATH)
            n2 = natsort_key(node2.Path, alg=ns.PATH)

        # sort info entries alphabetically
        elif all(isinstance(x, str) for x in nodes):
            n1 = natsort_key(node1)
            n2 = natsort_key(node2)

        # sort categories alphabetically
        elif all(isinstance(x, TableContainer) for x in nodes):
            n1 = natsort_key(node1.Name)
            n2 = natsort_key(node2.Name)

        # sort tables alphabetically
        elif all(isinstance(x, RomTable) for x in nodes):
            n1 = natsort_key(node1.Definition.Name)
            n2 = natsort_key(node2.Definition.Name)

        # one node is info, the other is category, sort info to top
        elif type(node1).__name__ != type(node2).__name__:
            n1 = type(node1).__name__
            n2 = type(node2).__name__

        else:
            return 0

        return 1 if ascending == (n1 > n2) else -1

    def GetParent(self, item):

        # root has no parent
        if not item:
            return dv.NullDataViewItem

        node = self.ItemToObject(item)
        parent = dv.NullDataViewItem

        if isinstance(node, InfoContainer):
            parent = self.ObjectToItem(node.Parent)
        elif isinstance(node, TableContainer):
            parent = self.ObjectToItem(node.Parent.Parent)
        elif isinstance(node, RomTable):
            rom = node.Parent
            category = node.Definition.Category
            parent = self.ObjectToItem(rom.Tables[category])
        elif isinstance(node, str):
            for rom in self._roms:
                if node in ['{}: {}'.format(k, v) for k, v in rom.Info]:
                    parent = rom.Info
                    break

        return parent

    def HasValue(self, item, col):
        if col > 0:
            return False
        return True

    def GetValue(self, item, col):
        assert col == 0, "Unexpected column for RomViewModel"

        node = self.ItemToObject(item)

        if isinstance(node, Rom):
            return '{} ({})'.format(
                os.path.basename(node.Path),
                node.Path
            )
        elif isinstance(node, InfoContainer):
            return 'Info'
        elif isinstance(node, TableContainer):
            return node.Name
        elif isinstance(node, RomTable):
            return node.Definition.Name
        elif isinstance(node, str):
            return node

        return ''

# TODO: update LoggerDef/viewmodel to use `Container` instead of tuples
class TranslatorViewModel(dv.PyDataViewModel):

    def __init__(self, translator):
        super(TranslatorViewModel, self).__init__()
        self._translator = translator

    def GetColumnCount(self):
        return 3 # TODO: add more columns (scaling? what else?)

    def GetColumnType(self, col):
        _col_map = {
            0: 'bool',      # enable/disable togglebox
            1: 'string',    # identifier
            2: 'string',    # name
        }
        return _col_map[col]

    def GetChildren(self, item, children):
        d = self._translator.Definition
        if d is None:
            return 0

        # root node, add param categories
        if not item:

            children.append(self.ObjectToItem(
                ('params', None, d.AllParameters)
            ))
            children.append(self.ObjectToItem(
                ('switches', None, d.AllSwitches)
            ))
            children.append(self.ObjectToItem(
                ('dtcs', None, d.AllDTCodes)
            ))
            return 3

        node = self.ItemToObject(item)

        if isinstance(node, tuple):
            node_type, parent, node_data = node

            out_items = []
            if node_type in ['params', 'switches', 'dtcs']:
                for par in node_data.values():
                    if par.Valid:
                        out_items.append(self.ObjectToItem(
                            ('param', node, par)
                        ))
                for x in out_items: children.append(x)
                return len(out_items)

        return 0

    def GetAttr(self, item, col, attr):
        if not item:
            return False

        if col == 1:
            node = self.ItemToObject(item)

            if isinstance(node, tuple):
                node_type, parent, node_data = node
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
            node_type, parent, node_data = node
            if node_type in ['params', 'switches', 'dtcs']:
                return True

        return False

    def HasDefaultCompare(self):
        return True

    def Compare(self, item1, item2, column, ascending):
        node1 = self.ItemToObject(item1)
        node2 = self.ItemToObject(item2)
        node1_type, parent1, node_data1 = node1
        node2_type, parent2, node_data2 = node2

        # parameters
        if all(isinstance(x, tuple) and x[0] == 'param' for x in [node1, node2]):

            # sort by identifier
            if column == 1:
                n1 = natsort_key(node_data1.Identifier)
                n2 = natsort_key(node_data2.Identifier)

            # sort by name
            elif column == 2:
                n1 = natsort_key(node_data1.Name)
                n2 = natsort_key(node_data2.Name)

            else:
                return 0

            return 1 if ascending == (n1 > n2) else -1

        # headers
        elif all(isinstance(x, tuple) and x[1] is None for x in [node1, node2]):
            _type_map = {
                'params': 1,
                'switches': 2,
                'dtcs': 3,
            }
            return _type_map[node1_type] > _type_map[node2_type]

        return 0

    def GetParent(self, item):

        # root has no parent
        if not item:
            return dv.NullDataViewItem

        node = self.ItemToObject(item)

        if isinstance(node, tuple):
            node_type, parent, node_data = node

            # categories have no parent
            if node_type in ['params', 'switches', 'dtcs']:
                return dv.NullDataViewItem
            elif node_type == 'param':
                return self.ObjectToItem(parent)
            else:
                raise ValueError('Unrecognized node')

    def HasValue(self, item, col):
        if col > 2:
            return False
        return True

    def GetValue(self, item, col):
        assert col in range(0, 3), "Unexpected column for TranslatorViewModel"

        node = self.ItemToObject(item)

        _col_map = {
            0: -1,
            1: '',
            2: '',
        }

        if isinstance(node, tuple):
            node_type, parent, node_data = node
            _type_map = {
                'params': 'Parameters',
                'switches': 'Switches',
                'dtcs': 'Diagnostic Trouble Codes',
            }
            if node_type in _type_map:
                _col_map = {
                    0: -1,
                    1: '',
                    2: _type_map[node_type],
                }
            elif node_type == 'param':
                _col_map = {
                    0: 1 if node_data.Enabled else 0,
                    1: node_data.Identifier,
                    2: node_data.Name,
                }

        return _col_map[col]

    def SetValue(self, value, item, col):
        if col == 0:
            node = self.ItemToObject(item)

            if isinstance(node, tuple):
                node_type, parent, node_data = node
                if node_type == 'param':
                    if value:
                        node_data.enable()
                    else:
                        node_data.disable()

    @property
    def Translator(self):
        return self._translator
