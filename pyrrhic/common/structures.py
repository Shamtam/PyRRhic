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

from math import prod
from xml.etree.ElementTree import Element, ProcessingInstruction

from .enums import UserLevel, DataType, _dtype_size_map

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

    def __repr__(self):
        return '<Scaling {}:{}>'.format(
            self.parent.Identifier,
            self.name
        )

class Table(object):
    """
    Common base class encompassing a table definition.

    Requires a name (a unique identifier). Keywords can be used to initialize
    any class properties. Any supplied keywords must be correctly typed or
    they'll be ignored; refer to property descriptions for correct types.
    """
    def __init__(self, name, parent, **kwargs):
        self._name = name
        self._parent = parent
        self._category = kwargs.pop('Category', None)
        self._desc = kwargs.pop('Description', None)
        self._level = kwargs.pop('Level', None)
        self._scaling = kwargs.pop('Scaling', None)
        self._datatype = kwargs.pop('Datatype', None)

        try:
            # handle addresses passed in as a hex string or as a raw int
            addr = kwargs.pop('Address', None)
            if isinstance(addr, int):
                self._address = addr
            elif isinstance(addr, str):
                self._address = int(addr, base=16)
            else:
                self._address = None

        except ValueError:
            _logger.warn('Invalid address "{}" for table {} in def {}\n'.format(
                addr, name, parent.Identifier
            ))
            addr = None

    def __repr__(self):
        return '<Table{}D {}/{}>'.format(
            len(self.Axes) + 1,
            self._category,
            self._name
        )

    def update(self, table):
        """
        Update undefined parameters from the passed in `Table` instance
        """

        # check all properties in this instance and the passed-in instance
        props = [p for p in vars(self).keys() if 'axis' not in p]

        # all defined properties in passed-in instance
        new_props = set([p for p in props if table.__getattribute__(p) is not None])

        # all undefined properties in self
        undef_props = set([k for k in props if self.__getattribute__(k) is None])

        # intersect both sets, update this instance's properties
        update_props = new_props.intersection(undef_props)
        for p in update_props:
            self.__setattr__(p, table.__getattribute__(p))

        # update axes
        axes = [p for p in vars(self).keys() if 'axis' in p]
        new_axes = [table.__getattribute__(x) for x in axes]
        undef_axes = [self.__getattribute__(x) for x in axes]
        for ax, newax in zip(undef_axes, new_axes):
            if not ax.IsFullyDefined:
                ax.update(newax)

    @property
    def IsFullyDefined(self):
        """
        Returns `True` if all table properties are defined, `False` otherwise.
        """
        # get all non-`Axis` properties
        props = [
            p for p, value in vars(self).items()
            if 'axis' not in p
        ]
        axes = [
            p for p, value in vars(self).items()
            if 'axis' in p
        ]
        undef_props = [x for x in props if self.__getattribute__(x) is None]
        undef_axes = [x for x in axes if not self.__getattribute__(x).IsFullyDefined]
        return (not undef_props) and (not undef_axes)

    @property
    def Name(self):
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
        raise NotImplementedError(
            '`Table.Length` must be implemented in subclasses'
        )

    @property
    def NumBytes(self):
        if(
            self._datatype != DataType.BLOB and
            (self.Length is not None and self._datatype is not None)
        ):
            return self.Length*_dtype_size_map[self._datatype]
        else:
            return None

    @property
    def Address(self):
        return self._address

    @property
    def Axes(self):
        raise NotImplementedError(
            '`Table.Axes` must be implemented in subclasses'
        )

class Table1D(Table):
    def __init__(self, *args, **kwargs):
        super(Table1D, self).__init__(*args[:2], **kwargs)
        self._values = kwargs.pop('Values', None)
        self._length = kwargs.pop('Length', None)

    @property
    def Length(self):
        return self._length

    @property
    def Values(self):
        return self._values

    @property
    def Axes(self):
        return []

class Table2D(Table):
    def __init__(self, *args, **kwargs):
        super(Table2D, self).__init__(*args[:2], **kwargs)
        self._x_axis = args[2]

    @property
    def XAxis(self):
        return self._x_axis

    @property
    def Length(self):
        axes = [p for p in vars(self).items() if 'axis' in p]

        if axes:
            lengths = [self.__getattribute__(x).Length for x in axes]
            if all([x is not None for x in lengths]):
                return prod(lengths)
            else:
                return None

    @property
    def Axes(self):
        return [self._x_axis]

class Table3D(Table2D):
    def __init__(self, *args, **kwargs):
        super(Table3D, self).__init__(*args[:3], **kwargs)
        self._y_axis = args[3]

    @property
    def YAxis(self):
        return self._y_axis

    @property
    def Axes(self):
        return [self._x_axis, self._y_axis]

_table_type_map = {
    '1D': Table1D,
    '2D': Table2D,
    '3D': Table3D,
    'X Axis': Table1D,
    'Y Axis': Table1D,
    'Static X Axis': Table1D,
    'Static Y Axis': Table1D,
}
