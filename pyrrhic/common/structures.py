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
import numpy as np
import struct

from sympy import sympify, lambdify, solve
from math import prod
from xml.etree.ElementTree import Element

from .enums import (
    ByteOrder, DataType, UserLevel, ByteOrder,
    _byte_order_struct_map, _dtype_struct_map, _dtype_size_map
)
from .utils import bound_int

_logger = logging.getLogger()

class Scaling(object):
    def __init__(self, name, parent, **kwargs):
        self.name = name
        self.parent = parent
        self.disp_expr = kwargs.pop('disp_expr', 'x')
        self.raw_expr = kwargs.pop('raw_expr', 'x')
        self.units = kwargs.pop('units', None)
        self.min = kwargs.pop('min', None)
        self.max = kwargs.pop('max', None)
        self.xml = kwargs.pop('xml', None)

        self._to_disp = (
            lambdify('x', self.disp_expr, 'numpy')
            if isinstance(self.disp_expr, str) else
            lambda x: self.disp_expr[x]
        )

        self._to_raw = (
            lambdify('x', self.raw_expr, 'numpy')
            if isinstance(self.raw_expr, str) else
            lambda x: self.raw_expr[x]
        )

    def __repr__(self):
        return '<Scaling {}:{}>'.format(
            self.parent.Identifier,
            self.name
        )

    def to_disp(self, value):
        return self._to_disp(value)

    def to_raw(self, value):
        return self._to_raw(value)

class TableDef(object):
    """
    Common base class encompassing a table definition.

    Requires a name (a unique identifier). Keywords can be used to
    initialize any class properties. Any supplied keywords must be
    correctly typed or they'll be ignored; refer to property
    descriptions for correct types.
    """
    def __init__(self, name, parent, **kwargs):
        self._name = name
        self._parent = parent
        self._category = kwargs.pop('Category', None)
        self._desc = kwargs.pop('Description', None)
        self._level = kwargs.pop('Level', None)
        self._scaling = kwargs.pop('Scaling', None)
        self._datatype = kwargs.pop('Datatype', None)
        self._axes = kwargs.pop('Axes', None)
        self._values = kwargs.pop('Values', None)
        self._length = kwargs.pop('Length', None)
        self._byte_order = kwargs.pop('ByteOrder', ByteOrder.BIG_ENDIAN) # TODO: placeholder... pull this from definition

        addr = kwargs.pop('Address', None)
        try:
            # handle addresses passed in as a hex string or as a raw int
            if isinstance(addr, int):
                self._address = addr
            elif isinstance(addr, str):
                self._address = int(addr, base=16)
            else:
                self._address = None

        except ValueError:
            _logger.warn('Invalid address "{}" for table {} in def {}'.format(
                addr, name, parent.Identifier
            ))
            self._address = None

        # update any axes to point to this table as its parent
        if self._axes:
            for ax in self._axes:
                ax._parent = self

    def __repr__(self):
        if self._axes:
            return '<TableDef{}D {}/{}>'.format(
                len(self._axes) + 1,
                self._category,
                self._name
            )
        else:
            return '<TableDef1D {}/{}>'.format(self._category, self._name)

    def update(self, table):
        """
        Update undefined parameters from the passed in `Table` instance
        """

        _logger.debug('Updating table {}:{} from parent {}'.format(
            self.Parent.Identifier, self._name, table.Parent.Identifier
        ))

        # all non-axis properties in this instance
        props = [p for p in vars(self).keys() if 'axes' not in p]

        # all defined properties in passed-in instance
        new_props = set([p for p in props if table.__getattribute__(p) is not None])

        # all undefined properties in self
        undef_props = set([k for k in props if self.__getattribute__(k) is None])

        # intersect both sets, update this instance's properties
        update_props = new_props.intersection(undef_props)
        for p in update_props:
            _logger.debug(
                'Updating table -- {}:{}.{} -> {}:{}'.format(
                    table.Parent.Identifier,
                    table.Name,
                    p,
                    self._parent,
                    self._name
                )
            )
            self.__setattr__(p, table.__getattribute__(p))

        # for matching table type based on axes, update each axis
        if self._axes and table._axes and len(self._axes) == len(table._axes):
            for ax, newax in zip(self._axes, table._axes):
                if not ax.FullyDefined:
                    _logger.debug(
                        'Updating axis -- {}:{}[{}] -> {}:{}[{}]'.format(
                            table.Parent.Identifier,
                            table.Name,
                            newax.Name,
                            self._parent,
                            self._name,
                            ax.Name,
                        )
                    )
                    ax.update(newax)

        # for tables whose axes are inherited
        elif not self._axes and table._axes:
            self._axes = table._axes

    @property
    def FullyDefined(self):
        """
        Returns `True` if all table properties are defined, `False` otherwise.
        """
        props = [
            p for p, value in vars(self).items()
            if 'axes' not in p
        ]
        undef_axes = []

        # remove irrelevant properties for 2D/3D tables
        if self._axes:
            props.remove('_values')
            props.remove('_length')
            undef_axes = [
                x for x in self._axes
                if not x.FullyDefined
            ]

        if not self._axes:
            # static axis, no need for address, length or scaling
            if self._values is not None:
                props.remove('_address')
                props.remove('_length')
                props.remove('_scaling')
            # standard axis, no need for values
            if self._address is not None:
                props.remove('_values')

        # axes don't need descriptive elements
        if isinstance(self._parent, TableDef):
            props.remove('_category')
            props.remove('_desc')
            props.remove('_level')

        undef_props = [x for x in props if self.__getattribute__(x) is None]
        return (not undef_props) and (not undef_axes)

    @property
    def Name(self):
        return self._name

    @property
    def Identifier(self):
        "Alias for TableDef.Name"
        return self._name

    @property
    def Parent(self):
        return self._parent

    @property
    def Category(self):
        return self._category

    @property
    def Description(self):
        return self._desc

    @property
    def Level(self):
        return self._level

    @property
    def Scaling(self):
        return self._scaling

    @Scaling.setter
    def Scaling(self, s):
        if isinstance(s, Scaling):
            self._scaling = s

    @property
    def Datatype(self):
        return self._datatype

    @property
    def Length(self):

        # 2D and 3D tables
        if self._axes:
            lengths = [x.Length for x in self._axes]
            if all([x is not None for x in lengths]):
                return prod(lengths)

        # 1D tables
        # bloblist
        elif self._values is not None:
            return len(self._values)

        # standard table
        elif self._length is not None:
            return self._length

        return None

    @property
    def NumBytes(self):
        if self._datatype not in [DataType.BLOB, DataType.STATIC]:
            return self.Length*_dtype_size_map[self._datatype]
        elif self._datatype == DataType.BLOB:
            # use first key from scaling disp_expression dictionary
            # to determine blob length
            return len(bytes.fromhex(list(self.Scaling.disp_expr.keys())[0]))
        return None

    @property
    def Address(self):
        return self._address

    @property
    def Axes(self):
        return self._axes

    @property
    def Values(self):
        return self._values

    @property
    def ByteOrder(self):
        return self._byte_order

class RomTable(object):
    def __init__(self, parent, tabledef):
        self._parent = parent
        self._definition = tabledef
        self._axes = None
        self._panel = None

        self.initialize_bytes()

        if self._definition.Axes:
            self._axes = []
            for ax in self._definition.Axes:
                self._axes.append(RomTable(parent, ax))

        self._current_scaling = self._definition.Scaling

    def __repr__(self):
        return '<RomTable {}/{}>'.format(
            self._definition.Category, self._definition.Name
        )

    def initialize_bytes(self):
        if self._definition.Datatype != DataType.STATIC:
            addr = self._definition.Address
            length = self._definition.NumBytes
            self._orig_bytes = self._parent.OriginalBytes[addr:addr + length]
            self._bytes = memoryview(self._parent.Bytes)[addr:addr + length]
        else:
            self._orig_bytes = None
            self._bytes = None

    def check_val_modified(self, idx1, idx2=0):
        """Returns a boolean indicating whether the value at the given
        row/column has been modified."""
        order = self._definition.ByteOrder
        dtype = self._definition.Datatype

        if dtype == DataType.STATIC:
            return False

        elem_size = _dtype_size_map[dtype]

        # 3D table
        if self._axes is not None and len(self._axes) == 2:
            cols = self._axes[0].Definition.Length
            idx = (idx1*cols + idx2)*elem_size
        # 1D/2D table
        else:
            idx = max(idx1, idx2)*elem_size

        return (
            self._bytes[idx:idx + elem_size] !=
            self._orig_bytes[idx:idx + elem_size]
        )

    def step(self, idx1, idx2=0, decrement=False):
        "Increase/decrease the value at the supplied index by one step size"

        order = self._definition.ByteOrder
        dtype = self._definition.Datatype

        if dtype in [DataType.BLOB, DataType.STATIC]:
            return

        # TODO: make step size dynamic and pull from definition
        if dtype == DataType.FLOAT:
            step = 1e-3
        else:
            step = 1

        border_str = _byte_order_struct_map[order]
        dtype_str = _dtype_struct_map[dtype]
        unpack_str = border_str + dtype_str
        elem_size = _dtype_size_map[dtype]

        # 3D table
        if self._axes is not None and len(self._axes) == 2:
            cols = self._axes[0].Definition.Length
            idx = (idx1*cols + idx2)*elem_size
        # 1D/2D table
        else:
            idx = max(idx1, idx2)*elem_size

        val = struct.unpack_from(unpack_str, self._bytes, idx)[0]
        flip = -1 if decrement else 1
        new_val = val + step*flip

        if dtype != DataType.FLOAT:
            new_val = bound_int(dtype, new_val)

        self._bytes[idx:idx + elem_size] = struct.pack(unpack_str, new_val)

    def add_raw(self, offs, idx1, idx2=0):
        "Add `offs` to the value stored at the supplied index"

        order = self._definition.ByteOrder
        dtype = self._definition.Datatype

        if dtype in [DataType.FLOAT, DataType.STATIC]:
            return

        border_str = _byte_order_struct_map[order]
        dtype_str = _dtype_struct_map[dtype]
        unpack_str = border_str + dtype_str
        elem_size = _dtype_size_map[dtype]

        # 3D table
        if self._axes is not None and len(self._axes) == 2:
            cols = self._axes[0].Definition.Length
            idx = (idx1*cols + idx2)*elem_size
        # 1D/2D table
        else:
            idx = max(idx1, idx2)*elem_size

        val = struct.unpack_from(unpack_str, self.Bytes, idx)[0]
        new_val = bound_int(dtype, val + offs)
        self.Bytes[idx:idx + elem_size] = struct.pack(unpack_str, new_val)

    @property
    def Axes(self):
        return self._axes

    @property
    def Definition(self):
        return self._definition

    @property
    def OriginalBytes(self):
        "Returns the unmodified raw byte data for this table"
        return self._orig_bytes

    @property
    def Bytes(self):
        "Returns the raw byte data currently contained by this table"
        return self._bytes

    @property
    def Values(self):
        "Returns a numpy array of the raw values of this table"
        border = self._definition.ByteOrder
        dtype = self._definition.Datatype

        if dtype not in [DataType.BLOB, DataType.STATIC]:

            # 3D table
            if self._axes is not None and len(self._axes) == 2:
                cols = self._axes[0].Definition.Length
                rows = self._axes[1].Definition.Length

            # 1D/2D table
            else:
                cols = self._definition.Length
                rows = 1

            if rows == 1 and cols == 1:
                shape = (1, 1)
            elif rows == 1:
                shape = (1, cols)
            else:
                shape = (rows, cols)

            border_str = _byte_order_struct_map[border]
            dtype_str = _dtype_struct_map[dtype]
            unpack_str = border_str + dtype_str

            buf = np.frombuffer(self.Bytes, unpack_str)
            return np.reshape(buf, shape)

        elif dtype == DataType.BLOB:
            return self.Bytes.hex().upper()

        elif dtype == DataType.STATIC:
            return self.Definition.Values

    @property
    def DisplayValues(self):
        "Returns a numpy array of the display-converted values of this table"
        if self._definition.Scaling:
            return self._definition.Scaling.to_disp(self.Values)
        else:
            return self.Values

    @property
    def PanelTitle(self):
        return '{} ({})'.format(
            self._definition.Name,
            self._parent.Path
        )

    @property
    def Panel(self):
        return self._panel

    @Panel.setter
    def Panel(self, f):
        self._panel = f

    @property
    def Parent(self):
        "Parent `Rom` object that contains this table"
        return self._parent

    @property
    def IsModified(self):
        modified = self._orig_bytes != self._bytes
        if self._axes:
            for ax in self._axes:
                modified = modified or ax.IsModified
        return modified

class LogParam(object):
    "Base class for logger elements"

    def __init__(self, parent, identifier, name, desc, dtype, endpoint):
        self._parent = parent
        self._identifier = identifier
        self._name = name #kwargs.pop('Name', 'LogParam_{}'.format(identifier))
        self._desc = desc #kwargs.pop('Description', '')
        self._datatype = dtype
        self._endpoint = endpoint

        self._enabled = False
        self._supported = False
        self._value = None

    def __repr__(self):
        return '<{} {}: {}>'.format(
            type(self).__name__, self._identifier, self._name
        )

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False
        self._value = None

    def set_supported(self):
        self._supported = True

    def set_unsupported(self):
        self._supported = False

    @property
    def Parent(self):
        return self._parent

    @property
    def Identifier(self):
        return self._identifier

    @property
    def Name(self):
        return self._name

    @property
    def Description(self):
        return self._desc

    @property
    def Datatype(self):
        return self._datatype

    @property
    def Endpoint(self):
        return self._endpoint

    @property
    def Enabled(self):
        return self._enabled

    @property
    def Valid(self):
        if self._addrs and self._supported:
            return bool(len(self._addrs))
        return False

    @property
    def RawValue(self):
        return self._value

    @RawValue.setter
    def RawValue(self, val):
        self._value = val

    @property
    def Value(self):
        if isinstance(self, (StdParam, ExtParam)):
            if self._value is not None:
                if self._scaling is not None:
                    key = _dtype_struct_map[self._datatype]
                    order = '>' # TODO: implement byte order
                    val = struct.unpack('{}{}'.format(order, key), self._value)[0]
                    return self._scaling.to_disp(val)
                else:
                    return int.from_bytes(self._value, 'big')
            else:
                return None
        else:
            return self._value

    @property
    def ValueStr(self):

        if isinstance(self, SwitchParam):
            if self._value is None:
                return ''
            else:
                return 'True' if self._value else 'False'

        elif isinstance(self, (StdParam, ExtParam)):
            if self._value is None:
                return ''
            elif self._scaling is not None:
                return '{:.4g}'.format(self.Value) # TODO: implement proper formatting
            else:
                return self._value.hex()

        else:
            return '{}'.format(self._value)

class StdParam(LogParam):
    "Standard Parameter"

    def __init__(self, *args, **kwargs):
        """Initializer

        Positional arguments directly passed to base class `__init__`,
        use keywords to initialize the instance. Any supplied keywords
        must be correctly typed or they'll be ignored; refer to property
        descriptions for correct types.
        """
        super(StdParam, self).__init__(*args)
        self._addrs = kwargs.pop('Addresses', None)
        self._bitidx = kwargs.pop('ECUBit')
        self._byteidx = kwargs.pop('ECUByteIndex')
        self._scalings = kwargs.pop('Scalings', {})
        self._scaling = kwargs.pop('Scaling', None)

    @property
    def Addresses(self):
        "`list` of `int`"
        return self._addrs

    @property
    def BitIndex(self):
        "`int`"
        return self._bitidx

    @property
    def ByteIndex(self):
        "`int`"
        return self._byteidx

    @property
    def Scalings(self):
        "`list` of `str` indicating scalings used by this parameter"
        return list(self._scalings.keys())

    @property
    def Scaling(self):
        "`Scaling` instance, or `None`"
        return self._scaling

    @Scaling.setter
    def Scaling(self, scale_name):
        "Set the current scaling"
        self._scaling = (
            self._scalings[scale_name]
            if scale_name in self._scalings
            else None
        )

class ExtParam(LogParam):
    "Extended (endpoint-specific) Parameter"

    def __init__(self, *args, **kwargs):
        """Initializer

        Positional arguments directly passed to base class `__init__`,
        use keywords to initialize the instance. Any supplied keywords
        must be correctly typed or they'll be ignored; refer to property
        descriptions for correct types.
        """
        super(ExtParam, self).__init__(*args)
        self._addrs = kwargs.pop('Addresses', None)
        self._scalings = kwargs.pop('Scalings', {})
        self._scaling = kwargs.pop('Scaling', None)

    @property
    def Addresses(self):
        "`list` of `int`"
        return self._addrs

    @property
    def Scalings(self):
        "`list` of `str` indicating scalings used by this parameter"
        return list(self._scalings.keys())

    @property
    def Scaling(self):
        "`Scaling` instance, or `None`"
        return self._scaling

    @Scaling.setter
    def Scaling(self, scale_name):
        "Set the current scaling"
        self._scaling = (
            self._scalings[scale_name]
            if scale_name in self._scalings
            else None
        )

class SwitchParam(StdParam):
    "Switch Parameter"

    def __init__(self, *args, **kwargs):
        """Initializer

        Positional arguments directly passed to base class `__init__`,
        use keywords to initialize the instance. Any supplied keywords
        must be correctly typed or they'll be ignored; refer to property
        descriptions for correct types.
        """
        kw = {
            x: kwargs.pop(x) for x in ['ECUByteIndex', 'ECUBit', 'Addresses']
        }
        super(SwitchParam, self).__init__(*args, **kw)

class DTCParam(LogParam):
    "Diagnostic Trouble Codes"

    def __init__(self, *args):
        """Initializer

        Positional arguments directly passed to base class `__init__`,
        use keywords to initialize the instance. Any supplied keywords
        must be correctly typed or they'll be ignored; refer to property
        descriptions for correct types.
        """
        self._tempaddr, self._memaddr = args[-2:]
        super(DTCParam, self).__init__(*args[:-2])

    @property
    def TempAddr(self):
        return self._tempaddr

    @property
    def MemAddr(self):
        return self._memaddr

    @property
    def Valid(self):
        return True
