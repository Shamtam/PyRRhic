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

"""Common data structures used across all of PyRRhic."""

import logging
import numpy as np
import struct

from sympy import solve

from .enums import (
    ByteOrder,
    DataType,
    UserLevel,
    _byte_order_struct_map,
    _dtype_struct_map,
    _dtype_size_map,
)
from .helpers import LogParamContainer, PyrrhicJSONSerializable, TableContainer
from .utils import bound_int


_logger = logging.getLogger()


class Scaling(PyrrhicJSONSerializable):
    """Encapsulation of a conversion between raw and display numerical values.

    Besides ``parent`` and ``name``, all attributes are optional, and can
    be specified via keyword argument.

    Attributes:
        parent (:class:`.ScalingContainer`)
        name (str): Unique internal identifer
        min: Minimum allowed display value (float), or ``None`` (default)
        max: Maximum allowed display value (float), or ``None`` (default)
        step (float): Increment/decrement step size, defaults to ``1e-3``
        padding: Number of zeroes to left-pad the displayed value with (int),
            or ``None`` if no padding should be applied (default)
        precision: Number of decimal places (int), defaults to ``3``
        format (str): String representing display format. Valid values are
            ``f`` (default), ``d``, ``x``, and ``s`` (standard C/Python format).
        units (str): User-facing string, defaults to a blank string
        expression: For regular numerical scalings, this is a string containing
            the function used to calculate the scaled numbers between raw and
            display values. The expression should be a simple expression
            containing a single variable, ``x``, along with standard functions
            and arithmetic operations. This string is processed internally by
            ``sympy.sympify``. Refer to SymPy documentation for acceptable
            tokens and operations that can be used in the expressions.

            For bloblists, this is a dictionary mapping ``bytes`` to ``str``.
    """

    def __init__(self, parent, name, **kwargs):
        self.parent = parent
        self.name = name
        self.min = kwargs.pop("min", None)
        self.max = kwargs.pop("max", None)
        self.step = kwargs.pop("step", 1e-3)
        self.padding = kwargs.pop("padding", None)
        self.precision = kwargs.pop("precision", 3)
        self.format = kwargs.pop("format", "f")
        self.units = kwargs.pop("units", "")
        self.expression = kwargs.pop("expression", "x")

        # for bloblists, cache a reversed dictionary for converting a display
        # string back to the raw bytes
        self._reverse_expression = None
        if isinstance(self.expression, dict):
            self._reverse_expression = {
                v: k for k, v in self.expression.items()
            }

    def __repr__(self):
        return "<Scaling {}>".format(self.name)

    def to_disp_val(self, raw_val):
        """Returns converts the given raw value a display value in its native
        format."""

        if isinstance(self.expression, dict):
            return self.expression[raw_val]

        else:
            expr = f"({self.expression}) - y"

            val = float(solve(expr, "y")[0].subs("x", raw_val))

            if self.min:
                val = max(val, self.min)

            if self.max:
                val = min(val, self.max)

            return val

    def to_disp_str(self, raw_val):
        """Returns a formatted string for the given raw numerical value."""

        val = self.to_disp_val(raw_val)

        if isinstance(val, str):
            return val

        if self.format in ["d", "x"]:
            prefix = "0x" if self.format == "x" else ""
            pad = f"0{self.padding:d}" if self.padding else ""
            val = int(val)
            return f"{prefix}{{:{pad}{self.format}}}".format(val)

        elif self.format == "f":
            return f"{{:.{self.precision:d}f}}".format(val)

    def to_raw(self, str_val):
        """Returns the raw value for the given string in its native format."""

        if isinstance(self.expression, dict):
            inv_map = {v: k for k, v in self.expression.items()}
            return inv_map[str_val]

        else:
            try:
                # bloblists should directly map between bytes and display str
                if (
                    self.format == "s"
                    and isinstance(self.expression, dict)
                    and self._reverse_expression is not None
                ):
                    return self._reverse_expression[str_val]

                elif self.format == "x":
                    val = int(str_val, base=16)
                elif self.format == "d":
                    val = int(str_val)
                else:
                    val = float(str_val)

            except ValueError:
                raise ValueError(f'Unable to convert "{str_val}" to float')

            expr = f"({self.expression}) - y"
            return float(solve(expr, "x")[0].subs("y", val))


class TableDef(PyrrhicJSONSerializable):
    """Encapsulation of a table definition.

    Besides ``parent`` and ``name``, all attributes are optional, and can be
    specified via keyword argument.

    Attributes:
        parent: Definition container that contains this table (either
            a subclass of :class:`.Container` or :class:`.TableDef`, for axes)
        name (str): User-facing display name (also used as unique identifier)
        description (str): Extended description text for table
        level (:class:`.UserLevel`): User level of the table
        scalings (list): list of ``str``, associated scaling names
        datatype (:class:`.DataType`): Underlying table data type
        endian (:class:`.ByteOrder`): Underlying byte order
        axes (list): List of ``dict`` defining the table's axes. Each ``dict``
            in the list should contain all keywords necessary to instantiate
            a suitable :class:`.TableDef` instance to describe each axis.
        elements (int): Number of elements in the table. This should only be
            used for regular 1D tables
        values (list): List of ``str`` containing table's display values. This
            should only be used for static 1D tables
        address (int): Base table address
    """

    def __init__(self, parent, name, **kwargs):
        self.parent = parent
        self.name = name
        self.description = kwargs.pop("description", None)
        self.level = kwargs.pop("level", None)
        self.scalings = kwargs.pop("scalings", [])
        self.datatype = kwargs.pop("datatype", None)
        self.endian = kwargs.pop("endian", ByteOrder.BIG_ENDIAN)
        self.address = kwargs.pop("address", None)
        self.elements = kwargs.pop("elements", None)

        # instantiate axes based on supplied axis keyword dicts
        self.axes = []
        axes = kwargs.pop("axes", [])
        if axes and 1 <= len(axes) <= 2:
            for idx, ax in enumerate(axes):
                ax_name = ax.pop("name", f"Axis {idx}")
                self.axes.append(TableDef(self, ax_name, **ax))
        elif axes:
            raise ValueError(f"Invalid number of axes supplied ({len(axes)})")

        self.values = kwargs.pop("values", [])
        if self.values and (self.axes or not self.datatype == DataType.STATIC):
            raise ValueError(
                "Non-static table and/or 2D/3D table should not have defined "
                "values"
            )

    def __repr__(self):
        return "<TableDef{}D {}/{}>".format(
            len(self.axes) + 1, self.Category, self.name
        )

    @property
    def Category(self):
        if isinstance(self.parent, TableContainer):
            return self.parent.name
        else:
            return None

    @property
    def ROMDefinition(self):
        """The :class:`.ROMDefinition` that contains this table's definition."""

        # regular tables
        if isinstance(self.parent, TableContainer):
            return self.parent.parent

        # axes
        elif isinstance(self.parent, TableDef):
            return self.parent.ROMDefinition

    @property
    def Length(self):
        """Total number of elements in table"""
        # 2D and 3D tables
        if self.axes:
            lengths = [x.Length for x in self.axes]
            if all([isinstance(x, int) for x in lengths]):
                return np.prod(lengths)

        # bloblist tables must be linked to a single Scaling with an expression
        # dictionary that maps raw bytes to display strings
        elif (
            self.datatype == DataType.BLOB
            and isinstance(self.scalings, list)
            and len(self.scalings) == 1
        ):
            scaling = self.EditorDef.get_scaling(self.scalings[0])
            if (
                isinstance(scaling, Scaling)
                and isinstance(scaling.expression, dict)
            ):
                return len(scaling.expression)

        # static tables must have defined values
        elif self.datatype == DataType.STATIC and self.values:
            return len(self.values)

        # axes must have a defined number of elements if not static/bloblist
        elif self.elements is not None:
            return self.elements

        # standard 1D tables always have length 1
        else:
            return 1

    @property
    def NumBytes(self):
        """Total size of table, in bytes."""

        if (
            self.datatype not in [DataType.BLOB, DataType.STATIC]
            and self.Length is not None
        ):
            return self.Length * _dtype_size_map[self.datatype]

        # for bloblists, use first key from scaling's byte/str mapping to
        # determine total table size
        elif (
            self.datatype == DataType.BLOB
            and isinstance(self.scalings, list)
            and len(self.scalings) == 1
        ):
            scaling = self.EditorDef.get_scaling(self.scalings[0])
            if (
                isinstance(scaling, Scaling)
                and isinstance(scaling.expression, dict)
            ):
                return len(next(iter(self.scalings[0].expression.keys())))


class LogParamDef(PyrrhicJSONSerializable):
    """Encapsulation of a logger parameter definition.

    Besides ``parent`` and ``identifier``, all attributes are optional, and can
    be specified via keyword argument.

    Attributes:
        parent: Subclass of :class:`.Container` that contains this definition
        identifier (str): Unique identifier
        name (str): User-facing display name for the parameter
        description (str): Extended description text for the parameter
        scalings (list): list of ``str``, associated scaling names
        datatype (:class:`.DataType`): Underlying parameter data type. Use one
            of the ``DataType.BIT#`` values for switch parameters
        endian (:class:`.ByteOrder`): Underlying parameter byte order
        addresses (list): list of ``int``
        endpoint (:class:`.LoggerEndpoint`): Parameter's target endpoint
        byte_idx (int): Byte index corresponding to this parameter used for
            detecting endpoint support
        bit_idx (int): Bit index within the byte corresponding to this
            parameter, used for detecting endpoint support
        group (int): group (DS2 only?)
        subgroup (int): subgroup (DS2 only?)
        groupsize (int): group size (DS2 only?)
    """

    def __init__(self, parent, identifier, **kwargs):
        self.parent = parent
        self.identifier = identifier
        self.name = kwargs.pop("name", identifier)
        self.description = kwargs.pop("description", None)
        self.scalings = kwargs.pop("scalings", [])
        self.datatype = kwargs.pop("datatype", None)
        self.endian = kwargs.pop("endian", ByteOrder.BIG_ENDIAN)
        self.addresses = kwargs.pop("addresses", [])
        self.endpoint = kwargs.pop("endpoint", None)
        self.byte_idx = kwargs.pop("byte_idx", None)
        self.bit_idx = kwargs.pop("bit_idx", None)
        self.group = kwargs.pop("group", None)
        self.subgroup = kwargs.pop("subgroup", None)
        self.groupsize = kwargs.pop("groupsize", None)

    def __repr__(self):
        if 0 <= self.datatype <= 7:
            type_str = "SwitchDef"
        elif self.byte_idx is not None and self.bit_idx is not None:
            type_str = "StdParamDef"
        elif self.addresses:
            type_str = "ExtParamDef"
        else:
            type_str = self.__class__.__name__

        return f"<{type_str} {self.identifier}/{self.name}>"

    @property
    def ROMDefinition(self):
        """The :class:`.ROMDefinition` that contains this parameter definition."""

        if isinstance(self.parent, LogParamContainer):
            return self.parent.parent


class LogDTCDef(PyrrhicJSONSerializable):
    """Encapsulation of a logger diagnostic trouble code definition.

    Besides ``parent`` and ``identifier``, all attributes are optional, and can
    be specified via keyword argument.

    Attributes:
        parent: Subclass of :class:`.Container` that contains this definition
        identifier (str): Unique identifier
        name (str): User-facing display name for the parameter
        description (str): Extended description text for the parameter
        bit (:class:`.DataType`): Use one of the ``DataType.BIT#`` values.
        temp_addr (int):
        mem_addr (int):
    """

    def __init__(self, parent, identifier, **kwargs):
        self.parent = parent
        self.identifier = identifier
        self.name = kwargs.pop("name", identifier)
        self.description = kwargs.pop("description", None)
        self.bit = kwargs.pop("datatype", None)
        self.temp_addr = kwargs.pop("temp_addr", None)
        self.mem_addr = kwargs.pop("temp_addr", None)

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.identifier}/{self.name}>"

    @property
    def ROMDefinition(self):
        """The :class:`.ROMDefinition` that contains this DTC definition."""

        if isinstance(self.parent, LogParamContainer):
            return self.parent.parent


class EditorTable(object):
    """Base class for table definition/bytes to UI translation objects"""

    def __init__(self, parent, tabledef):
        self._parent = parent
        self._definition = tabledef
        self._panel = None
        self._axes = []

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
            idx = (idx1 * cols + idx2) * elem_size
        # 1D/2D table
        else:
            idx = max(idx1, idx2) * elem_size

        return (
            self._bytes[idx : idx + elem_size]
            != self._orig_bytes[idx : idx + elem_size]
        )

    def check_valid_value(self, val):
        """Returns a boolean indicating whether the given value is valid
        for this table."""

        # TODO: make this more specific, check min/max, etc.

        dtype = self._definition.Datatype
        if dtype in [DataType.BLOB, DataType.STATIC]:
            return False
        else:
            try:
                float(val)
            except ValueError:
                return False
            else:
                return True

    def _cell_info(self, idx1, idx2):
        """Returns a `4-tuple` of info for the given indices.

        Returned tuple is (idx, bidx, elem_size, unpack_str) where
        - `idx` is the `int` or `2-tuple` used to retrieve the cell
            value from the numpy array returned by the `Values` property
        - `bidx` is the starting index of the cell value in the raw
            byte array containing this table's data
        - `elem_size` is the size of this a cell's data, in bytes
        - `unpack_str` is a `struct`-style format `str` used to
            pack/unpack the numeric value into a raw bytes
        """
        order = self._definition.ByteOrder
        dtype = self._definition.Datatype

        border_str = _byte_order_struct_map[order]
        dtype_str = _dtype_struct_map[dtype]
        unpack_str = border_str + dtype_str
        elem_size = _dtype_size_map[dtype]

        # 3D table
        if self._axes is not None and len(self._axes) == 2:
            cols = self._axes[0].Definition.Length
            idx = (idx1, idx2)
            bidx = (idx1 * cols + idx2) * elem_size

        # 1D/2D table
        else:
            idx = max(idx1, idx2)
            bidx = idx * elem_size

        return idx, bidx, elem_size, unpack_str

    def step(self, idx1, idx2=0, decrement=False):
        "Increase/decrease the value at the supplied index by one step size"

        dtype = self._definition.Datatype

        if dtype in [DataType.BLOB, DataType.STATIC]:
            return

        # TODO: make step size dynamic and pull from definition
        if dtype == DataType.FLOAT:
            step = 1e-3
        else:
            step = 1

        idx, bidx, elem_size, unpack_str = self._cell_info(idx1, idx2)

        val = struct.unpack_from(unpack_str, self._bytes, bidx)[0]
        flip = -1 if decrement else 1
        new_val = val + step * flip

        if dtype != DataType.FLOAT:
            new_val = bound_int(dtype, new_val)

        self._bytes[bidx : bidx + elem_size] = struct.pack(unpack_str, new_val)

    def add_raw(self, offs, idx1, idx2=0):
        "Add `offs` to the value stored at the supplied index"

        dtype = self._definition.Datatype

        if dtype in [DataType.FLOAT, DataType.STATIC]:
            return

        idx, bidx, elem_size, unpack_str = self._cell_info(idx1, idx2)

        val = struct.unpack_from(unpack_str, self.Bytes, bidx)[0]
        new_val = bound_int(dtype, val + offs)
        self._bytes[bidx : bidx + elem_size] = struct.pack(unpack_str, new_val)

    def set_cell(self, val, idx1, idx2=0):
        "Set the value of the cell at the supplied index"

        dtype = self._definition.Datatype

        if dtype == DataType.STATIC:
            return

        idx, bidx, elem_size, unpack_str = self._cell_info(idx1, idx2)

        new_val = (
            self._definition.Scaling.to_raw(val)
            if self._definition.Scaling
            else val
        )

        if dtype != DataType.FLOAT:
            new_val = bound_int(dtype, int(new_val))

        self._bytes[bidx : bidx + elem_size] = struct.pack(unpack_str, new_val)

    def add_cell(self, val, idx1, idx2=0):
        "Add the given value to the cell at the supplied index"

        dtype = self._definition.Datatype

        if dtype == DataType.STATIC:
            return

        idx, bidx, elem_size, unpack_str = self._cell_info(idx1, idx2)

        disp_val = self.DisplayValues[idx] + val
        new_val = (
            self._definition.Scaling.to_raw(disp_val)
            if self._definition.Scaling
            else disp_val
        )

        if dtype != DataType.FLOAT:
            new_val = bound_int(dtype, int(new_val))

        self._bytes[bidx : bidx + elem_size] = struct.pack(unpack_str, new_val)

    def mult_cell(self, val, idx1, idx2=0):
        "Multiply the cell at the supplied index by the given value"

        dtype = self._definition.Datatype

        if dtype == DataType.STATIC:
            return

        idx, bidx, elem_size, unpack_str = self._cell_info(idx1, idx2)

        disp_val = val * self.DisplayValues[idx]
        new_val = (
            self._definition.Scaling.to_raw(disp_val)
            if self._definition.Scaling
            else disp_val
        )

        if dtype != DataType.FLOAT:
            new_val = bound_int(dtype, int(new_val))

        self._bytes[bidx : bidx + elem_size] = struct.pack(unpack_str, new_val)

    def revert(self):
        raise NotImplementedError

    @property
    def Axes(self):
        return self._axes

    @property
    def Definition(self):
        return self._definition

    @property
    def DataType(self):
        return self._definition.Datatype

    @property
    def OriginalBytes(self):
        "Returns the unmodified raw byte data for this table"
        return self._orig_bytes

    @property
    def Bytes(self):
        "Returns the raw byte data currently contained by this table"
        return self._bytes

    @property
    def PanelTitle(self):
        raise NotImplementedError

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
        raise NotImplementedError

    @property
    def NumBytes(self):
        return self._definition.NumBytes

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
                shape = (1,)
            elif rows == 1:
                shape = (cols,)
            elif cols == 1:
                shape = (rows,)
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


class RomTable(EditorTable):
    def __init__(self, parent, tabledef):
        super().__init__(parent, tabledef)

        self.initialize_bytes()

        if self._definition.Axes:
            for ax in self._definition.Axes:
                self._axes.append(RomTable(parent, ax))

        self._current_scaling = self._definition.Scaling

    def __repr__(self):
        return "<RomTable {}/{}>".format(
            self._definition.Category, self._definition.Name
        )

    def initialize_bytes(self):
        if self._definition.Datatype != DataType.STATIC:
            addr = self._definition.Address
            length = self.NumBytes
            self._orig_bytes = self._parent.OriginalBytes[addr : addr + length]
            self._bytes = memoryview(self._parent.Bytes)[addr : addr + length]
        else:
            self._orig_bytes = None
            self._bytes = None

    def revert(self):
        if self.IsModified:
            self._bytes[0:] = self._orig_bytes

            if self._axes:
                for ax in self._axes:
                    ax.revert()

    @property
    def PanelTitle(self):
        return "{} ({})".format(self._definition.Name, self._parent.Path)

    @property
    def IsModified(self):
        modified = self._orig_bytes != self._bytes
        if self._axes:
            for ax in self._axes:
                modified = modified or ax.IsModified
        return modified


class RamTable(EditorTable):
    def __init__(self, rom_table):
        super().__init__(rom_table.Parent, rom_table.Definition)
        self._rom_table = rom_table
        self._axes = rom_table.Axes

        self._ram_addr = None
        self._orig_bytes = None
        self._bytes = None

        self._active = False

        # # initialize table data by setting original bytes and mutable
        # # bytes to something different (arbitrary). this forces the
        # # table to be marked as modified, which will indicate that the
        # # table data needs to be populated by reading its current state
        # # from RAM upon livetune initialization
        # self.initialize_bytes(
        #     orig_bytes=b'\x00'*self._rom_table.Definition.NumBytes,
        #     current_bytes=b'\xFF'*self._rom_table.Definition.NumBytes
        # )

    def __repr__(self):
        final_str = "["

        final_str += (
            "{:x}".format(self.RomAddress)
            if self.RomAddress is not None
            else "???"
        )

        final_str += " -> "

        final_str += (
            "{:x}".format(self.RamAddress)
            if self.RamAddress is not None
            else "???"
        )

        final_str += "]"

        return "<RamTable {}/{} {}>".format(
            self._definition.Category, self._definition.Name, final_str
        )

    def initialize_bytes(self, byte_view=None):
        """Initialize the `RamTable` from the given `memoryview`

        Should be called from a `LiveTuneData` instance when the table
        is to be allocated or unallocated from the live tuning RAM
        segment.

        If this table is being allocated, then a `memoryview` should be
        passed in to the `byte_view` keyword. This `memoryview` should
        correspond to the mutable byte section of the `LiveTuneData`
        instance that is assigned to store the raw bytes for this table.

        Otherwise, the table is being unallocated, the `byte_view`
        keyword should be omitted, which will clear the stored bytes
        from this `RamTable` instance (marking it as unallocated).

        Keywords [Default]:
        `byte_view` [`None`]: `memoryview` containing a section of raw
            bytes that contains the data of this table, or `None` to
            indicate that this table is not allocated
        """

        if isinstance(byte_view, memoryview):

            if len(byte_view) != self.NumBytes:
                raise ValueError(
                    (
                        "Specified `memoryview` has invalid length {}, "
                        "expecting length {}"
                    ).format(len(byte_view), self.NumBytes)
                )

            self._orig_bytes = byte_view.tobytes()
            self._bytes = byte_view

        else:
            self._orig_bytes = None
            self._bytes = None

    def activate(self, activate=True):
        self._active = activate

    def revert(self):
        if self.IsModified:
            self._bytes[0:] = self._orig_bytes

    @property
    def Bytes(self):
        if self._bytes is None:
            return self._rom_table.Bytes
        else:
            return self._bytes

    @property
    def RomAddress(self):
        return self._rom_table.Definition.Address

    @property
    def RamAddress(self):
        return self._ram_addr

    @RamAddress.setter
    def RamAddress(self, addr):
        self._ram_addr = addr

    @property
    def PanelTitle(self):
        return "[LIVE:0x{:x}] {}".format(self._ram_addr, self._definition.Name)

    @property
    def IsModified(self):
        return self._orig_bytes != self._bytes

    @property
    def Active(self):
        return self._active


class LogParam(object):
    "Base class for logger elements"

    def __init__(self, parent, identifier, name, desc, dtype, endpoint):
        self._parent = parent
        self._identifier = identifier
        self._name = (
            name  # kwargs.pop('Name', 'LogParam_{}'.format(identifier))
        )
        self._desc = desc
        self._datatype = dtype
        self._endpoint = endpoint

        self._enabled = False
        self._supported = False
        self._value = None

    def __repr__(self):
        return "<{} {}: {}>".format(
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
                    order = ">"  # TODO: implement byte order
                    val = struct.unpack(
                        "{}{}".format(order, key), self._value
                    )[0]
                    return self._scaling.to_disp(val)
                else:
                    return int.from_bytes(self._value, "big")
            else:
                return None
        else:
            return self._value

    @property
    def ValueStr(self):

        if isinstance(self, SwitchParam):
            if self._value is None:
                return ""
            else:
                return "True" if self._value else "False"

        elif isinstance(self, (StdParam, ExtParam)):
            if self._value is None:
                return ""
            elif self._scaling is not None:
                return "{:.4g}".format(
                    self.Value
                )  # TODO: implement proper formatting
            else:
                return self._value.hex()

        else:
            return "{}".format(self._value)


class StdParam(LogParam):
    "Standard Parameter"

    def __init__(self, *args, **kwargs):
        """Initializer

        Positional arguments directly passed to base class `__init__`,
        use keywords to initialize the instance. Any supplied keywords
        must be correctly typed or they'll be ignored; refer to property
        descriptions for correct types.
        """
        super().__init__(*args)
        self._addrs = kwargs.pop("Addresses", None)
        self._bitidx = kwargs.pop("ECUBit")
        self._byteidx = kwargs.pop("ECUByteIndex")
        self._scalings = kwargs.pop("Scalings", {})
        self._scaling = kwargs.pop("Scaling", None)

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
        super().__init__(*args)
        self._addrs = kwargs.pop("Addresses", None)
        self._scalings = kwargs.pop("Scalings", {})
        self._scaling = kwargs.pop("Scaling", None)

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
            x: kwargs.pop(x) for x in ["ECUByteIndex", "ECUBit", "Addresses"]
        }
        super().__init__(*args, **kw)


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
        super().__init__(*args[:-2])

    @property
    def TempAddr(self):
        return self._tempaddr

    @property
    def MemAddr(self):
        return self._memaddr

    @property
    def Valid(self):
        return True
