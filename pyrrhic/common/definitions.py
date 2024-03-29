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

from .helpers import PyrrhicJSONSerializable
from .structures import (
    Scaling, TableDef, LogParam, StdParam, ExtParam, SwitchParam, DTCParam
)
from .enums import (
    DataType, LoggerEndpoint, LoggerProtocol, UserLevel,
    _dtype_size_map, _ecuflash_to_dtype_map, _rrlogger_to_dtype_map
)
from .helpers import Container

class DefinitionContainer(Container):
    pass
class ECUFlashContainer(Container):
    pass
class ECUFlashSearchTree(Container):
    pass
class RRLoggerContainer(Container):
    pass

_logger = logging.getLogger(__name__)

class DefinitionManager(object):
    """Overall container for definitions"""

    def __init__(self, ecuflashRoot=None, rrlogger_path=None):
        self._defs = DefinitionContainer(self, name='Definitions')
        self._ecuflash_defs = ECUFlashContainer(self, name='ECUFlash Definitions')
        self._ecuflash_editor_tree = ECUFlashSearchTree(self)
        self._ecuflash_logger_tree = ECUFlashSearchTree(self)
        self._rrlogger_defs = RRLoggerContainer(self, name='RR Logger Definitions')

        if ecuflashRoot and os.path.isdir(ecuflashRoot):
            self.load_ecuflash_repository(ecuflashRoot)

        if rrlogger_path and os.path.isfile(rrlogger_path):
            self.load_rrlogger_file(rrlogger_path)

        # initialize base logger definitions on initialization and
        # generate combined definition structure
        for protocol in self._rrlogger_defs:
            protocol_dict = self._rrlogger_defs[protocol]
            if 'Base' in protocol_dict:
                protocol_dict['Base'].resolve_dependencies(
                    protocol_dict
                )

            # find all matching editor/logger definitions and combine them
            # them into ROMDefinitions
            for logger_id in protocol_dict:

                if protocol not in self._defs:
                    self._defs[protocol] = DefinitionContainer(
                        self._defs, name=protocol.name
                    )

                protocol_def_dict = self._defs[protocol]

                if logger_id in self._ecuflash_logger_tree:
                    ecuflash_defs = self._ecuflash_logger_tree[logger_id]

                    if logger_id not in protocol_def_dict:
                        protocol_def_dict[logger_id] = DefinitionContainer(
                            protocol_def_dict, name=logger_id
                        )

                    for editor_id in ecuflash_defs:
                        ecuflash_def = ecuflash_defs[editor_id]
                        rrlogger_def = protocol_dict[logger_id]

                        protocol_def_dict[logger_id][editor_id] = ROMDefinition(
                            ecuflash_def, rrlogger_def
                        )

    def load_ecuflash_repository(self, directory):
        """
        Load all ECUFlash definitions stored in the given directory tree.

        Arguments:
         - directory: absolute path to the top-level of the repository
        """

        self._ecuflash_defs = {}

        _fpaths = {}

        _logger.info('Loading ECUFlash repository located at {}'.format(directory))

        files = [
            os.path.join(root, f) for root, dirs, files in os.walk(directory)
            for f in files
            if 'xml' in os.path.splitext(f)[1]
        ]
        for abspath in files:

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

        # generate search trees. See the "SearchTree" properties
        editor_tree = {}
        logger_tree = {}
        for d in self._ecuflash_defs.values():
            i = d.Info
            addr = i['internalidaddress']
            id_hex = i['internalidhex']
            id_str = i['internalidstring']
            ecuid = i['ecuid']

            # update outer level of logger tree
            if ecuid:
                if ecuid not in logger_tree:
                    logger_tree[ecuid] = {}

            if not addr:
                continue

            # determine editor identifier
            addr = int(addr, base=16)
            if addr not in editor_tree:
                editor_tree[addr] = {}

            if addr and id_hex:
                val = bytes.fromhex(id_hex)
            elif addr and id_str:
                val = id_str.encode('ascii')
            else:
                continue

            # determine length of editor identifier
            nbytes = len(val)
            if nbytes not in editor_tree[addr]:
                editor_tree[addr][nbytes] = {}

            # update logger tree
            if ecuid:
                if val not in logger_tree[ecuid]:
                    logger_tree[ecuid][val] = d
                else:
                    raise ValueError(
                        'Logger tree: Duplicate definition of ecuid/internalid ' +
                        '{}/{}'.format(ecuid, val)
                    )

            # update editor tree
            if val not in editor_tree[addr][nbytes]:
                editor_tree[addr][nbytes][val] = d
            else:
                raise ValueError(
                    'Editor tree: Duplicate definition of internalid {}'.format(val)
                )

        self._ecuflash_editor_tree = editor_tree
        self._ecuflash_logger_tree = logger_tree

        _logger.info(
            'Loaded {} ECUFlash definitions'.format(
                len(self._ecuflash_defs)
            )
        )

    def load_rrlogger_file(self, filepath):
        self._rrlogger_defs = {}

        _logger.info('Loading RomRaider Logger definition file {}'.format(
            filepath
        ))

        root = ET.parse(filepath)
        xml_protocols = [x for x in root.iter('protocol')]

        _defs = {}

        for xml_protocol in xml_protocols:
            protocol = xml_protocol.attrib.get('id', None)

            if protocol not in [x.name for x in LoggerProtocol]:
                _logger.warn(
                    'Skipping loading of unknown protocol {}'.format(protocol)
                )
                continue

            protocol = LoggerProtocol[protocol]

            # initialize protocol container
            if protocol not in _defs:
                _defs[protocol] = {}
                _defs[protocol]['Base'] = {}

            if protocol == LoggerProtocol.SSM:
                xml_params = xml_protocol.iter('parameter')
                xml_switches = xml_protocol.iter('switch')
                xml_dtcodes = xml_protocol.iter('dtcode')
                xml_ecuparams = xml_protocol.iter('ecuparam')

                _scalings = {}

                # parameter and ecuparam elements
                _defs[protocol]['Base']['params'] = {}
                _defs[protocol]['Base']['scalings'] = {}
                for param in list(xml_params) + list(xml_ecuparams):

                    # handle calculated parameters
                    if list(param.iter('depends')):
                        continue # TODO: skip these for now...

                    ident = param.attrib['id']
                    xml_conversions = param.iter('conversion')

                    # extract scalings
                    param_scalings = {}
                    for idx, conv in enumerate(xml_conversions):
                        name = (
                            conv.attrib['units'] if 'units' in conv.attrib
                            else 'Conv{}'.format(idx)
                        )
                        param_scalings['{}_{}'.format(ident, name)] = conv

                    # store parameter information to base definition
                    _defs[protocol]['Base']['params'][ident] = {
                        'param': param,
                        'scalings': param_scalings
                    }

                    # create definition key for each specific ECU
                    if param.tag == 'ecuparam':
                        xml_ecus = param.iter('ecu')
                        for ecu in xml_ecus:
                            ids = ecu.attrib['id'].upper().split(',')
                            addrs = ecu.findall('address')

                            for ecuid in ids:
                                if ecuid not in _defs[protocol]:
                                    _defs[protocol][ecuid] = {}
                                    _defs[protocol][ecuid]['params'] = {}
                                    _defs[protocol][ecuid]['scalings'] = {}

                                _defs[protocol][ecuid]['params'][ident] = {
                                    'param': param,
                                    'scalings': param_scalings,
                                    'addrs': addrs,
                                }

                    _defs[protocol]['Base']['scalings'].update(param_scalings)

                    _scalings.update(param_scalings)

                _defs[protocol]['Base']['switches'] = {
                    param.attrib['id']: param for param in xml_switches
                }

                _defs[protocol]['Base']['dtcodes'] = {
                    param.attrib['id']: param for param in xml_dtcodes
                }

            elif protocol == LoggerProtocol.OBD:
                pass

            elif protocol == LoggerProtocol.DS2:
                pass

            elif protocol == LoggerProtocol.NCS:
                pass

        # instantiate RRLoggerDef instances
        for pkey in _defs:

            if pkey not in self._rrlogger_defs:
                self._rrlogger_defs[pkey] = {}

            for d in _defs[pkey]:
                dinfo = _defs[pkey][d]
                parents = {} if d == 'Base' else {'Base': None}
                params = dinfo.get('params', {})
                scalings = dinfo.get('scalings', {})
                switches = dinfo.get('switches', {})
                dtcodes = dinfo.get('dtcodes', {})
                self._rrlogger_defs[pkey][d] = RRLoggerDef(
                    d,
                    parents=parents,
                    scalings=scalings,
                    parameters=params,
                    switches=switches,
                    dtcodes=dtcodes
                )

            _logger.info(
                'Loaded {} RomRaider Logger {} protocol definitions'.format(
                    len(self._rrlogger_defs[pkey]), pkey.name
                )
            )

    @property
    def Definitions(self):
        """Combined editor/logger definitions.

        Stored as a nested `dict` of `ROMDefinition` values keyed by a
        `logger_id` on the outer level, and an `editor_id` on the inner
        level. These ids are `str`s, and are the same keys used for as
        keys for the ECUFlash and RRLogger defs, respectively
        """
        return self._defs

    @property
    def ECUFlashDefs(self):
        "`dict` of {`xmlid`: `<ECUFlashDef>`} key-val pairs"
        return self._ecuflash_defs

    @property
    def ECUFlashEditorSearchTree(self):
        """Nested `dict` search tree to quickly locate an ECUFlash def

        Outer dictionary is keyed by `internalidaddress`, the next level
        is keyed by length of the internalid value, and the the final
        level is keyed by the bytes of the internalid. If both tags are
        present, `internalidhex` is used over `internalidstring`.

        e.g.: `A2UI001L` has an address of 0x2000, and only contains a
        `internalidstring` field. Thus, its def would be located at
        self._ecuflash_editor_tree[0x2000][8]['A2UI001L']
        """
        return self._ecuflash_editor_tree

    @property
    def ECUFlashLoggerSearchTree(self):
        """Nested `dict` search tree to quickly locate an ECUFlash def

        Outer dictionary is keyed by `ecuid`, the final level is keyed
        by the bytes of the internalid. If both tags are present,
        `internalidhex` is used over `internalidstring`.

        e.g.: `A2UI001L` is a particular image for ECUID `4B12785207`,
        so its def would be located at self._ecuflash_logger_tree['4B12785207']['A2UI001L']
        """
        return self._ecuflash_logger_tree

    @property
    def RRLoggerDefs(self):
        "`dict` of {`identifier`: `<RRLoggerDef>`} key-val pairs"
        return self._rrlogger_defs

    @property
    def IsValid(self):
        return bool(self._ecuflash_defs)

class ECUFlashDef(object):
    "Encompasses all portions of an ECUFlash definition file."

    def __init__(self, identifier, **kwargs):
        """Initializer.

        Use keywords to seed the definition during init.

        Keywords described below are used to seed the corresponding
        portions of the definition. For these keywords, if the value for
        a given dict key is `None`, it will be resolved during
        dependency resolution.

        Any other keywords are interpreted as `romid` elements. These
        keywords all match the tag names used in ECUFlash. Any extra
        keys that don't match a known ECUFlash `romid` element is ignored.

        ## Note: Instantiation does not initialize the instance!
        ## See `resolve_dependencies` for more information.

        Arguments:
        - identifier - Unique identification string for this def

        Keywords [Default]:
        - parents [`{}`] - `dict` of `ECUFlashDef`s keyed by their unique
            identifier. If the value is `None`, it will be resolved during
            dependency resolution.

        - scalings [`{}`] - `dict` of scaling definitions. The dict should
            be keyed by the name of the corresponding scaling, and the value
            for each key is a `Scaling`.

        - tables [`{}`] - `dict` of table definitions. Each element can
            either be a `TableDef`, or a dictionary containing the necessary
            elements to instantiate a `TableDef` during dependency resolution.
        """
        self._identifier = identifier

        # remove any unneeded/extraneous romid elements
        kwargs.pop('xmlid', None)
        kwargs.pop('include', None)

        self._parents = kwargs.pop('parents', {})
        self._scalings = kwargs.pop('scalings',{})
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
        Generate the necessary information to instantiate a 1D `TableDef`.

        Returns a 2-tuple (`name`, `kw`) containing the name and all
        necessary keyword arguments to a `TableDef` initializer call.

        `ax` is the `Element` corresponding to the axis `<table>` tag
        """
        name = ax.attrib.get('name', 'Axis')
        ax_kw = {
            'Address': ax.attrib.get('address', None),
            'Length': int(ax.attrib['elements']) if 'elements' in ax.attrib else None,
        }

        # try to determine axis data type
        if 'scaling' in ax.attrib:
            ax_kw['Scaling'] = self._all_scalings[ax.attrib['scaling']]
            xml_scaling = ax_kw['Scaling'].xml
            ax_kw['Datatype'] = _ecuflash_to_dtype_map[
                xml_scaling.attrib['storagetype']
            ]

        # axis has discrete data points
        elif len(ax):
            ax_kw.update({
                'Datatype': DataType.STATIC,
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
            props['disp_expr'] = {
                x.attrib['value'].upper(): x.attrib['name'] for x in d
            }
            props['raw_expr'] = {
                x.attrib['name']: x.attrib['value'].upper() for x in d
            }

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
        Instantiate an appropriate `TableDef` from an `xml.etree.ElementTree.Element`
        """

        if not isinstance(tab, ET.Element):
            raise ValueError('`tab` must be an `xml.etree.ElementTree.Element`')

        attrs = tab.attrib

        name = attrs['name']
        axes = [] if attrs.get('type', None) in ['1D', '2D', '3D'] else None

        # try to infer table type from number of table children if no
        # table attribute is stored in the table tag
        ax_info = list(filter(lambda x: x.tag == 'table', tab))

        # instantiate any axes for 2D/3D tables
        for ax in ax_info:
            if axes is None:
                axes = []
            ax_name, ax_kw = self._determine_axis_info(ax)
            axes.append(TableDef(ax_name, None, **ax_kw))

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

        length = attrs.get('elements', None) # only used for 1D tables

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
            'Axes': axes,
        }

        # for defs with no parents, generate default values for
        # necessary table properties
        if not self._parents:
            _default_kw = {
                'Category': '<Uncategorized>',
                'Description': '<No Description Available>',
                'Level': UserLevel.Superdev,
                'Length': 1,
            }
            for key in _default_kw:
                if kw[key] is None:
                    kw[key] = _default_kw[key]

        # instantiate specific table type if determined, or base class if not
        table = TableDef(name, self, **kw)

        _logger.debug(
            'Instantiating table {}:{}'.format(self._identifier, name)
        )
        return table

    def resolve_dependencies(self, defs_dict):
        """
        Resolve all portions of the definition into their proper encapsulations.

        Because definitions can be hierarchical, when loading from
        ECUFlash XML files, it is necessary to first load and seed all
        definitions with all of the data stored in the original XML file,
        then resolve all portions into their final encapsulating object
        (i.e. `Scaling` or `TableDef`), taking into account any hierarchy.

        `defs_dict` should be a `dict` containing all of the definitions
        in the repository. It is keyed by the `xmlid` of each definition,
        and each value should be an `ECUFlashDef`.

        In terms of hierarchy, the order of the `include` elements is
        considered from latest to earliest. In other words, if a
        definition contained:

        ```xml
            <include>32BITBASE</include>
            <include>WXYZ0000</include>
        ```

        Then any information missing from this definition would first be
        gathered from `WXYZ0000`, and if still not found, would then be
        gathered from `32BITBASE`. If data is unable to be resolved
        after scanning parents, then an exception is thrown.
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
            lambda x: not isinstance(self._tables[x], TableDef), self._tables
        ))
        for t in table_names:
            tab = self._tables[t]
            table = self._table_from_xml(tab)

            # if not table.IsFullyDefined and self._parents:
            if self._parents:

                # use a DFS to resolve any undefined table parameters
                # iterate over parents and their parents in reverse order
                checked_defs = []
                unchecked_defs = list(reversed(self._parents.keys()))

                while unchecked_defs:

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

            #             # if local table type is undefined and parent is defined,
            #             # instantiate appropriate table type
            #             if type(table) == TableDef and type(new_table) != TableDef:
            #                 axes = new_table.Axes
            #                 args = [table.Name, self] + axes
            #                 table = type(new_table)(*args, **{})
            #                 table.update(table)

            #             # if local table type and parent type don't match,
            #             # assume a definition error and remove table from def
            #             elif type(table) != type(new_table):
            #                 _logger.warn(
            #                     'Definition error for table "{}"\n'.format(table.Name) +
            #                     'Definition in "{}" conflicts with definition in "{}"\n'.format(
            #                         table.Parent.Identifier, new_table.Parent.Identifier
            #                     )
            #                 )
            #                 del self._tables[t]
            #                 continue

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
        if self._info:
            id_hex = self._info.get('internalidhex', None)
            id_str = self._info.get('internalidstring', None)

            if id_hex:
                return bytes.fromhex(id_hex)
            elif id_str:
                return id_str.encode('ascii')

        return self._identifier

    @property
    def Info(self):
        return self._info

    @property
    def DisplayInfo(self):
        _disp_map = {
            'internalidaddress' : 'Calibration ID Address',
            'internalidstring'  : 'Calibration ID [ASCII]',
            'internalidhex'     : 'Calibration ID [Bytes]',
            'ecuid'             : 'ECU ID',
            'year'              : 'Year',
            'market'            : 'Market',
            'make'              : 'Make',
            'model'             : 'Model',
            'submodel'          : 'Sub-model',
            'transmission'      : 'Transmission',
            'memmodel'          : 'Memory Model',
            'flashmethod'       : 'Flash Method',
            'filesize'          : 'ROM Size',
            'checksummodule'    : 'Checksum Module',
            'caseid'            : 'Case ID',
        }
        return {_disp_map[k]:v for k, v in self._info.items() if v is not None}

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

class RRLoggerDef(object):
    "Encompasses portions of a RomRaider Logger definition for a specific ECU"

    def __init__(self, identifier, **kwargs):
        """Initializer.

        Use keywords to seed the definition during init.

        Keywords described below are used to seed the corresponding
        portions of the definition. For all keywords, if the value for
        a given dict key is `None`, it will be resolved during
        dependency resolution.

        ## Note: Instantiation does not initialize the instance!
        ## See `resolve_dependencies` for more information.

        Arguments:
        - identifier - Unique identification string for this def

        Keywords [Default]:
        - parents [`{}`] - `dict` of `RRLoggerDef`s keyed by their
            unique identifier

        - scalings [`{}`] - `dict` of scaling definitions. The dict
            should be keyed by the name of the corresponding scaling,
            and the value for each key is a `Scaling`

        - parameters [`{}`] - `dict` of logger parameters containing all
            `parameter` and `ecuparam` definitions. The dict should be
            keyed by the identifier of the parameter, and the value for
            each key is a `StdParam` or `ExtParam`

        - switches [`{}`] - `dict` of logger switches. The dict should
            be keyed by the identifier of the switch, and the value for
            each key is a `SwitchParam`

        - dtcodes [`{}`] - `dict` of logger dtcodes. The dict should
            be keyed by the identifier of the dtcode, and the value for
            each key is a `DTCParam`
        """
        self._identifier = identifier

        self._parents = kwargs.pop('parents', {})
        self._scalings = kwargs.pop('scalings',{})
        self._parameters = kwargs.pop('parameters', {})
        self._switches = kwargs.pop('switches', {})
        self._dtcodes = kwargs.pop('dtcodes', {})

        self._all_scalings = {}
        self._all_parameters = {}
        self._all_switches = {}
        self._all_dtcodes = {}

        self._initialized = False

    def _scaling_from_xml(self, name, conv):
        """
        Instantiate a `Scaling` object from an `xml.etree.ElementTree.Element`

        Arguments:
        - `name`: `str` specifying the name for this scaling
        - `conv`: `xml.etree.ElementTree.Element` of the `conversion`
            tag to be used to instantiate the resulting `Scaling`
        """
        props = {}
        props['xml'] = conv
        props['units'] = conv.attrib.get('units', '')
        props['disp_expr'] = conv.attrib.get('expr', 'x')
        props['min'] = conv.attrib.get('gauge_min', None)
        props['max'] = conv.attrib.get('gauge_max', None)

        return Scaling(name, self, **props)

    def resolve_dependencies(self, defs_dict):
        """
        Resolve all portions of the definition into their proper encapsulations.

        Because definitions can be hierarchical, when loading a
        RomRaider Logger XML file, it is necessary to first load and
        seed all definitions with all of the data stored in the original
        XML file, then resolve all portions into their final
        encapsulating object (i.e. `Scaling` or `LogParam`), taking into
        account any hierarchy.

        `defs_dict` should be a `dict` containing all of the definitions
        contained in the same logger protocol as this definition. It is
        keyed by the `Identifier` of each definition, and each value
        should be a `RRLoggerDef`.
        """
        # already initialized, nothing to resolve
        if self._initialized:
            return

        _logger.debug('Resolving RomRaider Logger definition {}'.format(
            self._identifier
        ))

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

        for par in self._parents.values():
            par.resolve_dependencies(defs_dict)

        # resolve scalings
        scale_names = list(filter(
            lambda x: not isinstance(self._scalings[x], Scaling), self._scalings
        ))
        for s in scale_names:
            scale = self._scalings[s]
            self._scalings[s] = self._scaling_from_xml(s, scale)

        self._all_scalings = {k: v for k, v in self._scalings.items()}

        # add all scalings from all parents to this definition
        if self._parents:
            for parent in reversed(self._parents.values()):
                for sname, sc in parent.AllScalings.items():
                    if sname not in self._all_scalings:
                        self._all_scalings[sname] = sc

        # resolve parameters
        param_ids = list(
            filter(
                lambda x: not isinstance(
                    self._parameters[x], (StdParam, ExtParam)
                ),
                self._parameters
            )
        )
        for pid in param_ids:
            pinfo = self._parameters[pid]
            xml_param = pinfo['param']
            xml_scalings = pinfo.get('scalings', {})
            xml_addrs = pinfo.get('addrs', [])
            param_class = (
                StdParam if xml_param.tag == 'parameter'
                else ExtParam
            )

            kw = {}
            name = xml_param.attrib['name']
            desc = xml_param.attrib['desc']
            endpoint = LoggerEndpoint(int(xml_param.attrib['target']))

            # determine addresses and byte/bit indices
            if param_class == StdParam:
                kw['ECUByteIndex'] = int(xml_param.attrib.get('ecubyteindex'))
                kw['ECUBit'] = int(xml_param.attrib.get('ecubit'))
                kw['Addresses'] = [
                    int(x.text, base=16) for x in xml_param.findall('address')
                ]

            elif param_class == ExtParam and 'Base' not in self.Identifier:
                kw['Addresses'] = [int(x.text, base=16) for x in xml_addrs]

            # determine datatype from conversions with a `storagetype` specified
            convs = list(
                filter(lambda x: 'storagetype' in x.attrib, xml_scalings.values())
            )
            if convs:
                conv = convs[0]
                dtype = _rrlogger_to_dtype_map[conv.attrib['storagetype']]

            # try and determine datatype from address if necessary
            else:
                length_addrs = list(filter(
                    lambda x: 'length' in x.attrib,
                    xml_param.findall('address')
                ))
                if length_addrs:
                    length = int(length_addrs[0].attrib['length'])
                else:
                    length = 1

                _length_to_dtype_map = {
                    1: DataType.UINT8,
                    2: DataType.UINT16,
                    4: DataType.FLOAT
                }

                dtype = _length_to_dtype_map[length]

            # determine scalings and default scaling
            kw['Scalings'] = {
                k: v for k, v in self._all_scalings.items()
                if k in xml_scalings
            }
            kw['Scaling'] = (
                list(kw['Scalings'].values())[0] if kw['Scalings']
                else None
            )

            self._parameters[pid] = param_class(
                self, pid, name, desc, dtype, endpoint, **kw
            )

        self._all_parameters = {k: v for k, v in self._parameters.items()}

        # add all parameters from all parents to this definition
        if self._parents:
            for parent in reversed(self._parents.values()):
                for pid, par in parent.AllParameters.items():
                    if pid not in self._all_parameters:
                        self._all_parameters[pid] = par

        # resolve switches
        switch_ids = list(
            filter(
                lambda x: not isinstance(self._switches[x], SwitchParam),
                self._switches
            )
        )
        for pid in switch_ids:
            xml_switch = self._switches[pid]

            kw = {}
            name = xml_switch.attrib['name']
            desc = xml_switch.attrib['desc']
            endpoint = LoggerEndpoint(int(xml_switch.attrib['target']))

            kw['ECUByteIndex'] = int(xml_switch.attrib.get('ecubyteindex'))
            kw['ECUBit'] = int(xml_switch.attrib['bit'])
            dtype = DataType(kw['ECUBit'])

            kw['Addresses'] = [int(xml_switch.attrib['byte'], base=16)]

            self._switches[pid] = SwitchParam(
                self, pid, name, desc, dtype, endpoint, **kw
            )

        self._all_switches.update({k: v for k, v in self._switches.items()})

        # add all switches from all parents to this definition
        if self._parents:
            for parent in reversed(self._parents.values()):
                for pid, par in parent.AllSwitches.items():
                    if pid not in self._all_switches:
                        self._all_switches[pid] = par

        # resolve dtcodes
        dtc_ids = list(
            filter(
                lambda x: not isinstance(self._dtcodes[x], DTCParam),
                self._dtcodes
            )
        )
        for pid in dtc_ids:
            xml_dtcode = self._dtcodes[pid]

            kw = {}
            name = xml_dtcode.attrib['name']
            desc = xml_dtcode.attrib['desc']
            endpoint = LoggerEndpoint.ECU
            dtype = DataType(int(xml_dtcode.attrib['bit']))
            tmpaddr = int(xml_dtcode.attrib['tmpaddr'], base=16)
            memaddr = int(xml_dtcode.attrib['memaddr'], base=16)

            self._dtcodes[pid] = DTCParam(
                self, pid, name, desc, dtype, endpoint, tmpaddr, memaddr
            )

        self._all_dtcodes.update({k: v for k, v in self._dtcodes.items()})

        # add all dtcodes from all parents to this definition
        if self._parents:
            for parent in reversed(self._parents.values()):
                for pid, par in parent.AllDTCodes.items():
                    if pid not in self._all_dtcodes:
                        self._all_dtcodes[pid] = par

        self._initialized = True

    def resolve_valid_params(self, capabilities):
        for p in (
            list(self._all_parameters.values())
            + list(self._all_switches.values())
        ):
            if isinstance(p, (StdParam, SwitchParam)):
                byte_idx = p.ByteIndex
                bit_idx = p.BitIndex
                if (capabilities[byte_idx] >> bit_idx) & 0x01 == 0x01:
                    p.set_supported()

            elif isinstance(p, ExtParam):
                if p.Addresses:
                    p.set_supported()

    @property
    def Identifier(self):
        return self._identifier

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
    def Parameters(self):
        return self._parameters

    @property
    def Switches(self):
        return self._switches

    @property
    def DTCodes(self):
        return self._dtcodes

    @property
    def AllParameters(self):
        return self._all_parameters

    @property
    def AllSwitches(self):
        return self._all_switches

    @property
    def AllDTCodes(self):
        return self._all_dtcodes

class ROMDefinition(PyrrhicJSONSerializable):
    def __init__(self, EditorDef=None, LoggerDef=None):
        self._editor_def = EditorDef
        self._logger_def = LoggerDef

    def __repr__(self):
        return '<{}: {}/{}>'.format(
            type(self).__name__,
            self._logger_def.Identifier,
            self._editor_def.Identifier
        )

    def to_json(self):
        # TODO
        raise NotImplementedError

    def from_json(self):
        # TODO
        raise NotImplementedError

    @property
    def EditorDef(self):
        return self._editor_def

    @property
    def LoggerDef(self):
        return self._logger_def

    @property
    def EditorID(self):
        return self._editor_def.Identifier if self._editor_def else None

    @property
    def LoggerID(self):
        return self._logger_def.Identifier if self._logger_def else None
