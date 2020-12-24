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
import xml.etree.ElementTree as ET

from .structures import Scaling, Table, Table1D, _table_type_map
from .enums import (
    DataType, TableDataType, ByteOrder, UserLevel,
    _dtype_size_map, _ecuflash_to_dtype_map
)

_logger = logging.getLogger(__name__)

class DefinitionManager(object):
    """Overall container for definitions"""

    def __init__(self, ecuflashRoot=None):
        self._ecuflash_defs = {}
        self._ecuflash_defs_by_hex = None
        self._ecuflash_defs_by_str = None
        self._rrlogger_defs = {}

        if ecuflashRoot and os.path.isdir(ecuflashRoot):
            self.load_ecuflash_repository(ecuflashRoot)

    def load_ecuflash_repository(self, directory):
        """
        Load all ECUFlash definitions stored in the given directory tree.

        Arguments:
         - directory: absolute path of the definition repository's top-level
        """

        self._ecuflash_defs = {}
        self._ecuflash_defs_by_hex = None
        self._ecuflash_defs_by_str = None

        _fpaths = {}

        _logger.info('Loading ECUFlash repository located at {}'.format(directory))

        for dirname, dirs, files in os.walk(directory):
            for f in files:

                # only process xml files
                if 'xml' not in os.path.splitext(f)[1]:
                    continue

                abspath = os.path.join(dirname, f)
                root = ET.parse(abspath)
                xmlid_list = list(root.iter('xmlid'))

                _logger.debug(
                    'Loading definition from file {}'.format(
                        abspath
                    )
                )

                if len(xmlid_list) == 1:
                    xmlid = xmlid_list[0].text

                    # new definition, instantiate container
                    if xmlid not in self._ecuflash_defs:

                        kw = {}
                        kw['scalings'] = {}
                        scalings = root.findall('scaling')
                        for scaling in scalings:
                            if {'name', 'storagetype'} <= scaling.attrib.keys():
                                name = scaling.attrib['name']
                                if name not in kw['scalings']:
                                    kw['scalings'][name] = scaling
                                else:
                                    _logger.warn(
                                        'Ignoring duplicate scaling {}'.format(name)
                                    )
                            else:
                                _logger.warn(
                                    'Ignoring insufficiently defined scaling  {}'.format(scaling)
                                )

                        kw['parents'] = {x.text: None for x in root.findall('include')}
                        kw['tables'] = {
                            x.attrib['name']: x for x in root.findall('table')
                            if 'name' in x.attrib
                        }
                        kw.update({x.tag: x.text for x in root.find('romid')})

                        self._ecuflash_defs[xmlid] = ECUFlashDef(xmlid, **kw)
                        _fpaths[xmlid] = abspath

                    else:
                        _logger.warn(
                            'Already loaded {}, skipping definition file {}'.format(
                                xmlid,  abspath
                            )
                        )
                else:
                    _logger.warn(
                        'Malformed definition {}: multiple `xmlid`s defined'.format(
                            abspath
                        )
                    )

        for d in self._ecuflash_defs.values():
            try:
                d.resolve_dependencies(self._ecuflash_defs)
            except Exception as e:
                _logger.warn(
                    'Malformed definition file "{}"\n{}\n'.format(
                        _fpaths[d.Identifier], e
                    )
                )

        self._ecuflash_defs_by_hex = {
            d.Info['internalidhex'].upper(): d for d in self._ecuflash_defs.values()
            if d.Info['internalidhex'] is not None
        }
        self._ecuflash_defs_by_str = {
            d.Info['internalidstring'].upper(): d for d in self._ecuflash_defs.values()
            if d.Info['internalidstring'] is not None
        }

        _logger.info(
            'Finished loading {} ECUFlash definitions'.format(
                len(self._ecuflash_defs)
            )
        )

    @property
    def ECUFlashDefs(self):
        "`dict` of {`xmlid`: `<ECUFlashDef>`} key-val pairs"
        return self._ecuflash_defs

    @property
    def ECUFlashDefsByHex(self):
        "`dict` of {`internalidhex`: `<ECUFlashDef>`} key-val pairs"
        return self._ecuflash_defs_by_hex

    @property
    def ECUFlashDefsByString(self):
        "`dict` of {`internalidstring`: `<ECUFlashDef>`} key-val pairs"
        return self._ecuflash_defs_by_str

    @property
    def UniqueInternalIDAddrs(self):
        "`set` of all `internalidaddress` values in the ECUFlash repository"
        return set([
            int(x.Info['internalidaddress'], base=16) for x in self._ecuflash_defs.values()
            if x.Info['internalidaddress'] is not None
        ])

    @property
    def UniqueHexIDLengths(self):
        "`set` of all lengths of `internalidhex`s in the ECUFlash repository"
        return set([len(x)//2 for x in self._ecuflash_defs_by_hex.keys()])

    @property
    def UniqueStringIDLengths(self):
        "`set` of all lengths of `internalidstring`s in the ECUFlash repository"
        return set([len(x) for x in self._ecuflash_defs_by_str.keys()])

    @property
    def IsValid(self):
        return bool(self._ecuflash_defs)

class ECUFlashDef(object):
    """
    Encompasses all portions of an ECUFlash definition file.

    Use keywords to seed the definition during init. Keywords described below
    are used to seed the corresponding portions of the definition. Any other
    keywords are interpreted as `romid` elements. These keywords all match the
    tag names used in ECUFlash. Any extra keys that don't match a known ECUFlash
    `romid` element is ignored.

    ## Note: Instance initialization may not completely initialize the instance!
    ## See `resolve_dependencies` for more information.

    Arguments:
     - identifier - Unique identification string for this def

    Keywords [Default]:
    - parents [`{}`] - `dict` of `ECUFlashDef`s keyed by their unique identifier.
        If the value is `None`, it will be resolved during dependency resolution.

    - scalings [`{}`] - `dict` of scaling definitions. The dict should be keyed
        by the name of the corresponding scaling, and the value for each key
        is a `Scaling`.

    - tables [`{}`] - `dict` of table definitions. Each element can either be
        a `Table`, or a dictionary containing the necessary elements to
        instantiate a `Table` during dependency resolution.
    """

    def __init__(self, identifier, **kwargs):
        self._identifier = identifier

        # remove any unneeded/extraneous romid elements
        kwargs.pop('xmlid', None)
        kwargs.pop('include', None)

        self._parents = kwargs.pop('parents', {})
        self._scalings = kwargs.pop('scalings', {})
        self._tables = kwargs.pop('tables', {})

        self._all_scalings = {}
        self._all_tables = {}

        self._info = {
            'internalidaddress': None,
            'internalidstring': None,
            'internalidhex': None,
            'ecuid': None,
            'year': None,
            'market': None,
            'make': None,
            'model': None,
            'submodel': None,
            'transmission': None,
            'memmodel': None,
            'flashmethod': None,
            'filesize': None,
            'checksummodule': None,
            'caseid': None,
        }
        for key in kwargs:
            if key in self._info:
                self._info[key] = kwargs[key]
            else:
                _logger.warn(
                    'Invalid tag {} in def {}'.format(
                        key, identifier
                    )
                )

        self._initialized = False

    def __repr__(self):
        return '<ECUFlashDef {}>'.format(self._identifier)

    def _determine_axis_info(self, ax):
        """
        Generate the necessary information to instantiate a `Table1D`.

        Returns a 2-tuple (`name`, `kw`) containing the name and all necessary
        keyword arguments to a `Table1D` initializer call.

        `ax` is the `Element` corresponding to the axis `<table>` tag
        """
        name = ax.attrib.get('name', 'Axis')
        ax_kw = {
            'Address': ax.attrib.get('address', None),
        }

        # determine axis data type
        if 'scaling' in ax.attrib:
            ax_kw['Scaling'] = self._all_scalings[ax.attrib['scaling']]
            xml_scaling = ax_kw['Scaling'].xml
            ax_kw['Datatype'] = _ecuflash_to_dtype_map[
                xml_scaling.attrib['storagetype']
            ]
            ax_kw['Length'] = (
                int(ax.attrib['elements'])
                if 'elements' in ax.attrib else None
            )

        # axis has discrete data points
        elif len(ax):
            ax_kw.update({
                'Datatype': DataType.BLOB,
                'Values': [x.text for x in ax.findall('data')],
                'Length': len(ax.findall('data')),
            })

        return name, ax_kw

    def _scaling_from_xml(self, d):
        """
        Instantiate a `Scaling` object from an `xml.etree.ElementTree.Element`
        """

        # capture all attributes
        props = {}
        props.update(d.attrib)

        # need XML Element to determine storage type during dependency resolution
        props['xml'] = d

        if 'units' not in props:
            props['units'] = ''

        # for bloblist, generate mappings for conversion expressions
        if d.attrib['storagetype'] == 'bloblist':
            props['disp_expr'] = {x.attrib['value']: x.attrib['name'] for x in d}
            props['raw_expr'] = {x.attrib['name']: x.attrib['value'] for x in d}

        # if for some reason the expressions haven't been determined,
        # default to expressions that return the raw value
        if 'disp_expr' not in props:
            props['disp_expr'] = props['toexpr'] if 'toexpr' in props else 'x'
            del props['toexpr']

        if 'raw_expr' not in props and 'frexpr' in props:
            props['raw_expr'] = props['frexpr'] if 'frexpr' in props else 'x'
            del props['frexpr']

        return Scaling(props.pop('name'), self, **props)

    def _table_from_xml(self, tab):
        """
        Instantiate an appropriate `Table` from an `xml.etree.ElementTree.Element`
        """

        if not isinstance(tab, ET.Element):
            raise ValueError('`tab` must be an `xml.etree.ElementTree.Element`')

        attrs = tab.attrib

        name = attrs['name']
        axes = []

        # try to infer table type from number of table children if no
        # table attribute is stored in the table tag
        table_type = attrs.get('type', None)
        ax_info = list(filter(lambda x: x.tag == 'table', tab))
        if ax_info:
            table_type = ('{:d}D'.format(len(ax_info) + 1))

        # instantiate any axes
        for ax in ax_info:
            ax_name, ax_kw = self._determine_axis_info(ax)
            axes.append(Table1D(ax_name, self, **ax_kw))

        desc = tab.find('description')

        level = (
            UserLevel(int(attrs.get('level', None)))
            if 'level' in attrs else None
        )

        scaling_name = attrs.get('scaling', None)

        # this seems to be hardcoded in ECUFlash defs, so need to handle
        # it specifically
        scaling_name = None if scaling_name == 'ChecksumFix' else scaling_name

        scaling = self._all_scalings.get(scaling_name, None)
        dtype = (
            _ecuflash_to_dtype_map[scaling.xml.attrib['storagetype']]
            if scaling is not None else None
        )

        length = attrs.get('elements', None)

        # for bloblist tables, assume each value is same length of
        # bytes, and use first entry in scaling to determine number
        # of bytes
        if dtype == DataType.BLOB:
            nbytes = len(scaling.xml.find('data').attrib['value'])/2
        else:
            nbytes = _dtype_size_map[dtype]*length if dtype and length else None

        address = attrs.get('address', None)

        kw = {
            'Category': attrs.get('category', None),
            'Description': desc.text if desc else None,
            'Level': level,
            'Scaling': scaling,
            'Datatype': dtype,
            'Length': length,
            'NumBytes': nbytes,
            'Address': address,
        }

        # instantiate specific table type if determined, or base class if not
        args = [name, self] + axes
        if table_type is not None:
            table = _table_type_map[table_type](*args, **kw)
        else:
            table = Table(name, self, **kw)

        return table

    def resolve_dependencies(self, defs_dict):
        """
        Resolve all portions of the definition into their proper encapsulations.

        Because definitions can be hierarchical, when loading from ECUFlash XML
        files, it is necessary to first load and seed all definitions with all
        of the data stored in the original XML file, then resolve all portions
        into their final encapsulating object (i.e. `Scaling` or `Table`),
        taking into account any hierarchy.

        `defs_dict` should be a `dict` containing all of the definitions in the
        repository. It is keyed by the `xmlid` of each definition, and each
        value is either an `ECUFlashDef` or another `dict` with these keys:
        - `path`: absolute path of the original xml file of the definition
        - `root`: raw `ElementTree` of the definition
        - `parents`: list of `xmlid`s indicating any inherited definitions
        - `scalings`: `dict` of `Scaling`s contained in the definition
        - `tables`: `dict` of `Table`s contained in the definition

        In terms of hierarchy, the order of the `include` elements is considered
        from latest to earliest. In other words, if a definition contained:

        ```xml
            <include>32BITBASE</include>
            <include>WXYZ0000</include>
        ```

        Then any information missing from this definition would first be
        gathered from `WXYZ0000`, and if still not found, would then be
        gathered from `32BITBASE`. If data is unable to be resolved after
        scanning parents, then an exception is thrown.
        """

        # already initialized, nothing to resolve
        if self._initialized:
            return

        _logger.debug(
            'Resolving dependencies for definition {}'.format(self._identifier)
        )

        # resolve parents
        for par in self._parents:
            if par not in defs_dict:
                raise ValueError(
                    'Unable to resolve parent {} for {}'.format(
                        par, self._identifier
                    )
                )
            else:
                self._parents[par] = defs_dict[par]

        # ensure all parents' dependencies are resolved before attempting to
        # resolve tables
        for par in self._parents.values():
            par.resolve_dependencies(defs_dict)

        # resolve scalings
        scale_names = list(filter(
            lambda x: not isinstance(self._scalings[x], Scaling), self._scalings
        ))
        for s in scale_names:
            scale = self._scalings[s]
            self._scalings[s] = self._scaling_from_xml(scale)

        self._all_scalings = {k: v for k, v in self._scalings.items()}

        # add all scalings from all parents to this definition
        if self._parents:
            for parent in reversed(self._parents.values()):
                for sname, sc in parent.AllScalings.items():
                    if sname not in self._all_scalings:
                        self._all_scalings[sname] = sc

        # resolve tables
        table_names = list(filter(
            lambda x: not isinstance(self._tables[x], Table), self._tables
        ))
        for t in table_names:
            tab = self._tables[t]
            table = self._table_from_xml(tab)

            if not table.IsFullyDefined and self._parents:

                # use a DFS to resolve any undefined table parameters
                # iterate over parents and their parents in reverse order
                checked_defs = []
                unchecked_defs = list(reversed(self._parents.keys()))

                while not table.IsFullyDefined and unchecked_defs:

                    xmlid = unchecked_defs.pop(0)
                    checked_defs.append(xmlid)
                    current_def = defs_dict[xmlid]

                    # ensure current def has been fully resolved
                    current_def.resolve_dependencies(defs_dict)

                    # add any unchecked parents for this def to the front of
                    # the unchecked list
                    if current_def._parents:
                        unchecked_defs = list(filter(
                            lambda x: x not in checked_defs,
                            list(reversed(current_def._parents.keys()))
                        )) + unchecked_defs

                    # update undefined table properties from this table
                    if t in current_def._tables:
                        new_table = current_def._tables[t]

                        # if local table type is undefined and parent is defined,
                        # instantiate appropriate table type
                        if type(table) == Table and type(new_table) != Table:
                            axes = new_table.Axes
                            args = [table.Name, self] + axes
                            table = type(new_table)(*args, **{})
                            table.update(table)

                        # if local table type and parent type don't match,
                        # assume a definition error and remove table from def
                        elif type(table) != type(new_table):
                            _logger.warn(
                                'Definition error for table "{}"\n'.format(table.Name) +
                                'Definition in "{}" conflicts with definition in "{}"\n'.format(
                                    table.Parent.Identifier, new_table.Parent.Identifier
                                )
                            )
                            del self._tables[t]
                            continue

                        # update undefined properties
                        table.update(new_table)

            self._tables[t] = table

        self._all_tables = {k: v for k, v in self._tables.items()}

        # add all tables from all parents to this definition
        if self._parents:
            for parent in reversed(self._parents.values()):
                for tname, tab in parent.AllTables.items():
                    if tname not in self._all_tables:
                        self._all_tables[tname] = tab

        self._initialized = True

    @property
    def Identifier(self):
        return self._identifier

    @property
    def Info(self):
        return self._info

    @property
    def Parents(self):
        return self._parents

    @property
    def Scalings(self):
        return self._scalings

    @property
    def AllScalings(self):
        return self._all_scalings

    @property
    def Tables(self):
        return self._tables

    @property
    def AllTables(self):
        return self._all_tables
