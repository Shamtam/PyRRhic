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
import re
import xml.etree.ElementTree as ET

from pubsub import pub

from .helpers import (
    DefinitionContainer,
    EditorDefContainer,
    LogParamContainer,
    LoggerProtocolContainer,
    PyrrhicJSONSerializable,
)
from .structures import (
    LogParamDef,
    Scaling,
    TableDef,
    StdParam,
    ExtParam,
    SwitchParam,
    DTCParam,
)
from .enums import (
    DataType,
    LoggerEndpoint,
    LoggerProtocol,
    UserLevel,
    _dtype_size_map,
    _byte_order_map,
    _ecuflash_to_dtype_map,
    _rrlogger_to_dtype_map,
)
from .helpers import (
    EditorDefContainer,
    LoggerDefContainer,
    ScalingContainer,
    CategoryContainer,
    TableContainer,
)
from .utils import _ecuflash_format_parse_re, _rrlogger_format_parse_re

_ecuflash_attrib_map = {"inc": "step", "toexpr": "expression"}
_rrlogger_attrib_map = {
    "expr": "expression",
    "gauge_min": "min",
    "gauge_max": "max",
    "gauge_step": "step",
}

_logger = logging.getLogger(__name__)


class InvalidDef(Exception):
    pass


class DefinitionManager(object):
    """Overall container for definitions"""

    def initialize_from_legacy(self, ecuflashRoot, rrlogger_path):
        """Initialize definitions from legacy ECUFlash/RomRaider definitions."""

        editor_defs = load_ecuflash_repository(ecuflashRoot)
        logger_defs, logger_scalings = load_rrlogger_file(rrlogger_path)

        # generate combined definition dicts
        self._all_defs = DefinitionContainer(self, name="Definitions")
        self._defs_by_editor_id = DefinitionContainer(
            self, name="Definitions (by Editor ID)"
        )
        self._defs_by_logger_id = DefinitionContainer(
            self, name="Definitions (by Logger ID)"
        )

        for (editor_def, editor_scalings) in editor_defs.values():
            internal_id = editor_def.Identifier
            ecuid = editor_def.Info["ecuid"]
            romdef = None

            for protocol_defs in logger_defs.values():

                # Editor and Logger definitions
                if ecuid in protocol_defs:
                    logger_def = protocol_defs[ecuid]
                    scalings = ScalingContainer(
                        None,
                        data={**editor_scalings, **logger_scalings},
                        name=f"{internal_id}/{ecuid} Scalings",
                    )
                    romdef = ROMDefinition(editor_def, logger_def, scalings)

                    if ecuid not in self._defs_by_logger_id:
                        self._defs_by_logger_id[ecuid] = {internal_id: romdef}
                    else:
                        self._defs_by_logger_id[ecuid][internal_id] = romdef

                    break

            # Editor-only definitions
            if romdef is None:
                scalings = ScalingContainer(
                    None,
                    data={**editor_scalings},
                    name=f"{internal_id} Scalings",
                )
                romdef = ROMDefinition(editor_def, None, scalings)

            scalings.parent = romdef
            self._defs_by_editor_id[internal_id] = romdef

            self._all_defs[f"{internal_id}/{ecuid}"] = romdef

        # Logger only definitions
        editor_def = None
        internal_id = None
        for protocol_defs in logger_defs.values():
            log_only_defs = (
                set(protocol_defs.keys()) - set(self._defs_by_logger_id.keys())
            )

            for ecuid in log_only_defs:
                logger_def = protocol_defs[ecuid]
                scalings = ScalingContainer(
                    None,
                    data={**logger_scalings},
                    name=f"{internal_id}/{ecuid} Scalings",
                )
                romdef = ROMDefinition(editor_def, logger_def, scalings)
                scalings.parent = romdef
                self._all_defs[f"{internal_id}/{ecuid}"] = romdef

        pub.sendMessage("definitions.init", mgr=self)

    @property
    def Definitions(self):
        """Combined editor/logger definitions.

        Stored as a `dict` of `ROMDefinition` values keyed by a combined string
        ``<editor_id>/<logger_id>``, where ``editor_id`` and ``logger_id`` are
        the same keys used for ECUFlash and RRLogger defs, respectively.
        """
        return self._all_defs

    @property
    def DefinitionsByEditorID(self):
        """Nested `dict` search tree to quickly locate an ECUFlash def

        The second element is a nested dictionary. The outermost ``dict`` maps
        an ``internalidaddress`` (``int``) to a second ``dict``. The second
        level maps the length of the internal id (``int``) to another ``dict``
        keyed by the actual internal id. The final ``dict`` maps the internal
        id (``bytes``) to the :class:`.EditorDef` instance. If the definition
        contains both ``internalidhex`` and ``internalidstring``, the latter is
        ignored and this dictionary uses ``internalidhex`` as the key. This
        nested dictionary can be used to quickly check if a definition exists
        for an arbitrarily loaded ROM image for editing. A retrieval of a
        definition instance from this dictionary may resemble the following:
            ```
            d = editor_tree[0x2000][8][b"A2UI001L"]
            ```
        """
        return self._defs_by_editor_id

    @property
    def DefinitionsByLoggerID(self):
        """Nested `dict` search tree to quickly locate an ECUFlash def.

        The final element is also a nested dictionary, similar to the previous
        element. The outermost ``dict`` maps an ``ecuid`` (``str``) to another
        ``dict`` keyed by a definition's internal id (``bytes``), in the same
        priority as the previous editing search tree. The second (and final)
        level maps the internal id to the definition instance. This nested
        dictionary can be used to quickly check if an editor definition exists
        for a given logging target. A retrieval of a definition instance from
        this dictionary may resemble the following:
            ```
            d = logger_tree[bytes.fromhex("4B12785207")][b"A2UI001L"]
            ```
        """
        return self._defs_by_logger_id


class EditorDef(object):
    """Encompasses all ROM-editing portions of a ROM definition."""

    def __init__(self, identifier, **kwargs):
        """Initializer.

        Use keywords to seed the definition during init.

        Args:
            identifier (str): Unique identification string for this def
            info (dict): Dictionary containing general information about the
                definition. The only keys considered correspond to elements
                of the ``<romid>`` tag in an ECUFlash definition.
            parents (:class:`.DefinitionContainer`): Mapping of parent
                definitions' unique identifiers to their corresponding
                :class:`.EditorDef` instance
            tables (:class:`.CategoryContainer`): Nested mapping of table
                definitions. The first level maps category names to a
                :class:`.TableContainer`, which then maps table names to their
                corresponding :class:`.TableDef` instance.
        """
        self._identifier = identifier

        romid_info = kwargs.pop("info", {})

        keys = [
            "internalidaddress",
            "internalid",
            "ecuid",
            "year",
            "market",
            "make",
            "model",
            "submodel",
            "transmission",
            "memmodel",
            "flashmethod",
            "filesize",
            "checksummodule",
            "caseid",
        ]

        ignore_keys = ["xmlid"]

        self._info = {k: None for k in keys}
        for key in self._info:
            val = romid_info.pop(key, None)

            if key != "internalid":
                self._info[key] = val

            else:
                # prioritize hex ID over string ID
                val = romid_info.pop("internalidhex", None)
                if val is not None:
                    self._info[key] = bytes.fromhex(val)

                else:
                    val = romid_info.pop("internalidstring", None)
                    if val is not None:
                        self._info[key] = val.encode("ascii")

        for key in romid_info:
            if key not in ignore_keys:
                _logger.warn(
                    f"Ignoring unused rom info `{key}`:`{romid_info[key]}`"
                    f"supplied on initialization of definition `{identifier}`"
                )

        self._parents = kwargs.pop(
            "parents", DefinitionContainer(self, name=f"{identifier} Parents")
        )
        self._tables = kwargs.pop(
            "tables", CategoryContainer(self, name=f"{identifier} Tables")
        )

    def __repr__(self):
        return "<EditorDef {}>".format(self._identifier)

    @property
    def Identifier(self):
        """Unique ``str`` identifier for editor definition."""
        return self._identifier

    @property
    def Info(self):
        """``dict`` of general ROM information."""
        return self._info

    @property
    def DisplayInfo(self):
        """``dict`` containing user-facing general ROM information."""
        _disp_map = {
            "internalidaddress": "Calibration ID Address",
            "internalid": "Calibration ID",
            "ecuid": "ECU ID",
            "year": "Year",
            "market": "Market",
            "make": "Make",
            "model": "Model",
            "submodel": "Sub-model",
            "transmission": "Transmission",
            "memmodel": "Memory Model",
            "flashmethod": "Flash Method",
            "filesize": "ROM Size",
            "checksummodule": "Checksum Module",
            "caseid": "Case ID",
        }
        return {
            _disp_map[k]: v for k, v in self._info.items() if v is not None
        }

    @property
    def Parents(self):
        """``list`` of :class:``.EditorDef`` this ROM inherits from.

        Order of parents in this list works from innermost to outermost level
        of hierarchy. For example, if the list resembled the list [``BASE2``,
        ``BASE1``], then any information contained in ``BASE2`` would override
        any information contained in ``BASE1``.
        """
        return self._parents

    @property
    def Tables(self):
        """:class:`.CategoryContainer`, nested mapping of table definitions.

        The first level maps category names to a :class:`.TableContainer`. Each
        of these containers then maps table names to their corresponding
        :class:`.TableDef` instance.
        """
        return self._tables


class LoggerDef(object):
    "Encompasses all logging portions of a ROM definition"

    def __init__(self, identifier, **kwargs):
        """Initializer.

        Use keywords to seed the definition during init.

        Args:
            identifier (str): Unique identification string for this def
            parents (:class:`.DefinitionContainer`): Mapping of parent
                definitions' unique logger identifiers to their corresponding
                :class:`.LoggerDef` instance
            parameters (:class:`.LogParamContainer`): Mapping of parameter
                identifiers to their corresponding :class:`.StdParam` or
                :class:`.ExtParam` instances
            switches (:class:`.LogParamContainer`): Mapping of switch
                identifiers to their corresponding :class:`.SwitchParam`
                instances
            dtcodes (:class:`.LogParamContainer`): Mapping of logger dtcode
                identifiers to their corresponding :class:`.DTCParam`
                instances
        """
        self._identifier = identifier

        self._parents = kwargs.pop(
            "parents", DefinitionContainer(self, name="Parents")
        )
        self._parameters = kwargs.pop(
            "parameters", LogParamContainer(self, name="Logger Parameters")
        )
        self._switches = kwargs.pop(
            "switches", LogParamContainer(self, name="Logger Switches")
        )
        self._dtcodes = kwargs.pop(
            "dtcodes", LogParamContainer(self, name="Logger DTCs")
        )

    def __repr__(self):
        return f"<{self.__class__.__name__} {self._identifier}>"

    def resolve_valid_params(self, capabilities):
        for p in list(self._all_parameters.values()) + list(
            self._all_switches.values()
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
    def Parameters(self):
        return self._parameters

    @property
    def Switches(self):
        return self._switches

    @property
    def DTCodes(self):
        return self._dtcodes


class ROMDefinition(PyrrhicJSONSerializable):
    def __init__(self, editor_def=None, logger_def=None, scalings=None):
        self.editor_def = editor_def
        self.logger_def = logger_def
        self.scalings = scalings

    def __repr__(self):
        return "<{}: {}/{}>".format(
            self.__class__.__name__,
            self.EditorID,
            self.LoggerID,
        )

    def to_json(self):
        # TODO
        raise NotImplementedError

    def from_json(self):
        # TODO
        raise NotImplementedError

    @property
    def EditorID(self):
        return self.editor_def.Identifier if self.editor_def else None

    @property
    def LoggerID(self):
        return self.logger_def.Identifier if self.logger_def else None


def _extract_ecuflash_table_datatype_info(table_xml, scaling_xmls):
    """Extract datatype information from the supplied XML ``Element``.

    Given a ``<table>`` XML, this will check if it either contains data tags,
    or has a scaling defined in the global scaling dictionary. Using either of
    these, datatype properties can be inferred for the table.

    Args:
        table_xml (``Element``): ``<table>`` tag ``Element`` instance
        scaling_xmls (``dict``): Nested mapping of scaling definitions. First
            level maps definition identifiers to a :class:`.ScalingContainer`,
            which then maps scaling names to the scaling's raw XML ``Element``

    Returns:
        dict: datatype related keyword arguments to be passed to a
        :class:`.TableDef` initializer call
    """

    kw = {}

    # static axis
    if len(table_xml) and table_xml.findall("data"):
        static_data = [x.text for x in table_xml.findall("data")]
        kw["datatype"] = DataType.STATIC
        kw["values"] = static_data
        kw["length"] = len(static_data)

    # determine datatype from scaling, if defined
    scaling_name = table_xml.attrib.get("scaling", None)

    if scaling_name is not None:

        # traverse up from current def through parents
        for scalings in reversed(scaling_xmls.values()):

            if scaling_name in scalings:

                scaling_xml = scalings[scaling_name]

                kw["scaling"] = scaling_name
                kw["datatype"] = _ecuflash_to_dtype_map[
                    scaling_xml.attrib["storagetype"]
                ]
                kw["endian"] = _byte_order_map[
                    scaling_xml.attrib.get("endian", "big")
                ]
                break

    return kw


def _extract_table_from_ecuflash_xml(table_xml, scaling_xmls):
    """Generate keywords to instantiate a :class:`.TableDef`.

    Args:
        table_xml (``Element``): ``<table>`` tag ``Element`` instance
        scaling_xmls (``dict``): Nested mapping of scaling definitions. First
            level maps definition identifiers to a :class:`.ScalingContainer`,
            which then maps scaling names to the scaling's raw XML ``Element``

    Returns:
        dict: keyword arguments to be passed to a :class:`.TableDef`
        initializer call.
    """
    attrs = table_xml.attrib

    ax_info = list(filter(lambda x: x.tag == "table", table_xml))

    # verify type and number of defined axes match
    if "type" in attrs:

        if "Axis" in attrs["type"]:
            num_axes = 0

        else:
            type_match = re.match(r"(?P<dimension>\d)[Dd]", attrs["type"])

            if not type_match:
                _logger.warn(f"Invalid type {attrs['type']}")
                raise InvalidDef

            num_axes = int(attrs["type"][0]) - 1

        if num_axes != len(ax_info):
            _logger.warning("Number of defined axes doesn't match type")
            raise InvalidDef

    # extract axis info
    axes_kws = [{} for x in range(len(ax_info))]

    for idx, (xml, ax_kw) in enumerate(zip(ax_info, axes_kws)):

        ax_kw["name"] = xml.attrib.get("name", f"Axis {idx}")

        if "address" in xml.attrib:
            ax_kw["address"] = int(xml.attrib["address"], 16)
        if "elements" in xml.attrib:
            ax_kw["elements"] = int(xml.attrib["elements"])

        ax_kw.update(_extract_ecuflash_table_datatype_info(xml, scaling_xmls))

    kw = {
        "level": UserLevel(int(attrs.get("level", 5))),
        "axes": axes_kws,
    }

    desc = table_xml.find("description")
    if desc is not None:
        kw["description"] = desc.text

    kw.update(_extract_ecuflash_table_datatype_info(table_xml, scaling_xmls))

    return kw


def _scaling_from_ecuflash_xml(scaling_xml):
    """Generate a keyword dictionary to instantiate a :class:`.Scaling`.

    `scaling_xml` is a `xml.etree.ElementTree.Element` as parsed from an
    ECUFlash definition file.
    """
    kw = {}

    # extract min/max/step
    for k in ["min", "max", "inc"]:
        if k in scaling_xml.attrib:
            kw[_ecuflash_attrib_map.get(k, k)] = float(scaling_xml.attrib[k])

    # extract formatting
    fmt_str = scaling_xml.attrib.get("format", "%0.6f")
    fmt_match = _ecuflash_format_parse_re.match(fmt_str).groupdict()

    if fmt_match.get("format", None) is not None:
        kw["format"] = fmt_match["format"]

    for k in ["padding", "precision"]:
        if fmt_match.get(k, None) is not None:
            kw[k] = int(fmt_match[k])

    # extract unit and expression
    for k in ["units", "toexpr"]:
        if k in scaling_xml.attrib and scaling_xml.attrib[k]:
            kw[_ecuflash_attrib_map.get(k, k)] = scaling_xml.attrib[k]

    return kw


def _extract_param_from_rrlogger_xml(param_info, scaling_xmls):
    """Generate keywords to instantiate a :class:`.LogParamDef`.

    Args:
        param_info (``dict``): dictionary containing at most 3 mappings:
            - ``param``: ``xml.etree.ElementTree.Element`` corresponding to the
                ``parameter``, ``ecuparam`` or ``switch`` tag
            - ``scalings``: ``list`` of scaling names used by this parameter
            - ``addrs``: list of ``xml.etree.ElementTree.Element`` containing
                all ``address`` tags within the ``ecu`` tag
        scaling_xmls (``dict``): mapping of scaling names to the scaling's raw
            XML ``xml.etree.ElementTree.Element``

    Returns:
        dict: keyword arguments to be passed to a :class:`.LogParamDef`
        initializer call.
    """

    xml = param_info["param"]
    scaling_names = param_info.get("scalings", [])
    addrs = param_info.get("addrs", [])

    kw = {
        "name": xml.attrib["name"],
        "description": xml.attrib["desc"],
        "endpoint": LoggerEndpoint(int(xml.attrib["target"])),
    }

    if xml.tag == "parameter":
        kw["byte_idx"] = int(xml.attrib["ecubyteindex"])
        kw["bit_idx"] = int(xml.attrib["ecubit"])
        kw["addresses"] = [
            int(x.text, base=16) for x in xml.findall("address")
        ]
    elif xml.tag == "ecuparam" and addrs:
        kw["addresses"] = [int(x.text, base=16) for x in addrs]

    # determine datatype from conversions with a specified `storagetype`
    convs = list(
        filter(lambda x: "storagetype" in x.attrib, xml.findall("conversion"))
    )
    if convs:
        conv = convs[0]
        kw["datatype"] = _rrlogger_to_dtype_map[conv.attrib["storagetype"]]

        if "endian" in conv.attrib:
            kw["endian"] = _byte_order_map[conv.attrib["endian"]]

    # try to determine datatype from address
    else:
        length_addrs = list(
            filter(
                lambda x: "length" in x.attrib,
                xml.findall("address"),
            )
        )
        if length_addrs:
            length = int(length_addrs[0].attrib["length"])
        else:
            length = 1

        _length_to_dtype_map = {
            1: DataType.UINT8,
            2: DataType.UINT16,
            4: DataType.FLOAT,
        }

        kw["datatype"] = _length_to_dtype_map[length]

    if scaling_names:
        kw["scalings"] = scaling_names

    for a in ["group", "subgroup", "groupsize"]:
        if a in xml.attrib:
            kw[a] = int(xml.attrib[a])

    return kw


def _scaling_from_rrlogger_xml(scaling_xml):
    """Generate a keyword dictionary to instantiate a :class:`.Scaling`.

    `scaling_xml` is a `xml.etree.ElementTree.Element` as parsed from a
    RomRaider Logger definition file.
    """
    kw = {"padding": 0}

    # extract min/max/step
    for k in ["gauge_min", "gauge_max", "gauge_step"]:
        if k in scaling_xml.attrib:
            kw[_ecuflash_attrib_map.get(k, k)] = float(scaling_xml.attrib[k])

    # extract formatting
    fmt_str = scaling_xml.attrib.get("format", "0.000000")
    fmt_match = _rrlogger_format_parse_re.match(fmt_str).groupdict()

    if fmt_match.get("precision", None) is not None:
        kw["precision"] = len(fmt_match["precision"])

    # extract unit and expression
    for k in ["units", "expr"]:
        if k in scaling_xml.attrib and scaling_xml.attrib[k]:
            kw[_ecuflash_attrib_map.get(k, k)] = scaling_xml.attrib[k]

    return kw


def load_ecuflash_repository(directory):
    """Generate :class:`.EditorDef` instances for an ECUFlash repository.

    Args:
        directory (str): absolute path to the top-level of the repository

    Returns:
        dict: mapping of a definintion's ``xmlid`` to a 2-tuple containing
        its correspoding :class:`.EditorDef` instance and a
        :class:`.ScalingContainer` that holds all locally defined scalings
    """

    xml_repo = {}

    fpaths = {}

    _logger.info("Loading ECUFlash repository located at {}".format(directory))

    files = [
        os.path.join(root, f)
        for root, dirs, files in os.walk(directory)
        for f in files
        if "xml" in os.path.splitext(f)[1]
    ]

    # load all XML files/elements into dictionaries
    for abspath in files:

        root = ET.parse(abspath)
        xmlid_list = list(root.iter("xmlid"))

        _logger.debug("Loading definition from file {}".format(abspath))

        # invalid definition
        if len(xmlid_list) != 1:
            _logger.warn(
                "Malformed definition {}: no/multiple `xmlid`s defined".format(
                    abspath
                )
            )
            continue

        xmlid = xmlid_list[0].text

        # duplicate definition
        if xmlid in xml_repo:
            _logger.warn(
                "Already loaded {}, skipping definition file {}".format(
                    xmlid, abspath
                )
            )
            continue

        # new definition, extract and store XML elements
        xml_elems = {}

        # parse all scalings
        xml_elems["scalings"] = {}
        scalings = root.findall("scaling")

        for scaling in scalings:

            # incompletely defined scaling
            if {"name", "storagetype"} > scaling.attrib.keys():
                _logger.warn(
                    "Insufficiently defined scaling {} ignored".format(scaling)
                )
                continue

            name = scaling.attrib["name"]

            # duplicate scaling
            if name in xml_elems["scalings"]:
                _logger.warn("Duplicate scaling {} ignored".format(name))
                continue

            xml_elems["scalings"][name] = scaling

        # parse parents
        xml_elems["parents"] = [x.text for x in root.findall("include")]

        # parse tables into nested category->table dictionary
        xml_elems["tables"] = {
            x.attrib["category"]: {}
            for x in root.findall("table")
            if all(y in x.attrib for y in ["name", "category"])
        }
        for category in xml_elems["tables"]:
            xml_elems["tables"][category] = {
                x.attrib["name"]: x
                for x in root.findall("table")
                if (
                    all(y in x.attrib for y in ["name", "category"])
                    and x.attrib["category"] == category
                )
            }

        xml_elems["info"] = {x.tag: x.text for x in root.find("romid")}

        xml_repo[xmlid] = xml_elems
        fpaths[xmlid] = abspath

    # generate EditorDef instances
    editor_defs = EditorDefContainer(None, name="Editor Definitions")
    pending_defs = list(xml_repo.keys())

    while pending_defs:
        current_id = pending_defs.pop(0)
        current_xml = xml_repo[current_id]

        category_cont = CategoryContainer(None, name="Tables")

        # revisit this definition later after all its parents are instantiated
        if set(current_xml["parents"]) - set(editor_defs.keys()):
            pending_defs.append(current_id)
            continue

        # generate scalings
        scaling_cont = ScalingContainer(None, name="Scalings")
        scaling_xmls = current_xml["scalings"]
        for name in scaling_xmls:
            xml = scaling_xmls[name]
            kw = _scaling_from_ecuflash_xml(xml)
            scaling_cont[name] = Scaling(scaling_cont, name, **kw)

        # parents ordered from inner to outermost hierarchy level
        parent_cont = DefinitionContainer(
            None,
            data={x: editor_defs[x] for x in reversed(current_xml["parents"])},
            name="Parents",
        )

        # generate global scaling dictionaries
        all_scaling_xmls = {}
        for parent_id in current_xml["parents"]:
            parent_xml = xml_repo[parent_id]
            all_scaling_xmls[parent_id] = parent_xml["scalings"]

        all_scaling_xmls[current_id] = scaling_xmls

        # generate tables
        for category, table_xmls in current_xml["tables"].items():
            table_cont = TableContainer(category_cont, name=category)
            category_cont[category] = table_cont

            for name, table_xml in table_xmls.items():

                try:
                    kw = _extract_table_from_ecuflash_xml(
                        table_xml, all_scaling_xmls
                    )

                except InvalidDef:
                    _logger.warning(
                        f"Invalid definition, skipping table `{name}`."
                    )
                    continue

                table = TableDef(table_cont, name, **kw)
                table_cont[name] = table

        # instantiate definition
        definition = EditorDef(
            current_id,
            info=current_xml["info"],
            parents=parent_cont,
            tables=category_cont,
        )

        # update parent links for containers and store definition
        parent_cont.parent = definition
        scaling_cont.parent = definition
        category_cont.parent = definition
        editor_defs[current_id] = (definition, scaling_cont)

    _logger.info("Loaded {} ECUFlash definitions".format(len(editor_defs)))

    return editor_defs


def load_rrlogger_file(filepath):
    """Generate :class:`.LoggerDef` instances for a RomRaider logger defs file.

    Args:
        filepath (str): absolute path to the logger file to parse

    Returns:
        tuple: 2-tuple containing logger definitions and all scalings contained
        in the definition file. The tuple is of the form
        (:class:`.LoggerDefContainer` :class:`.ScalingContainer`).
    """

    _logger.info(
        "Loading RomRaider Logger definition file {}".format(filepath)
    )

    root = ET.parse(filepath)
    xml_protocols = [x for x in root.iter("protocol")]

    # load all XML elements into dictionaries
    xml_elements = {}

    for xml_protocol in xml_protocols:
        protocol = xml_protocol.attrib.get("id", None)

        if protocol not in [x.name for x in LoggerProtocol]:
            _logger.warn(
                "Skipping loading of unknown protocol {}".format(protocol)
            )
            continue

        protocol = LoggerProtocol[protocol]

        # initialize protocol container
        if protocol not in xml_elements:
            xml_elements[protocol] = {"Base": {}}

        if protocol == LoggerProtocol.SSM:
            xml_params = xml_protocol.iter("parameter")
            xml_switches = xml_protocol.iter("switch")
            xml_dtcodes = xml_protocol.iter("dtcode")
            xml_ecuparams = xml_protocol.iter("ecuparam")

            # parameter and ecuparam elements
            xml_elements[protocol]["Base"]["params"] = {}
            xml_elements[protocol]["Base"]["scalings"] = {}

            for param in list(xml_params) + list(xml_ecuparams):

                # handle calculated parameters
                if list(param.iter("depends")):
                    continue  # TODO: skip these for now...

                ident = param.attrib["id"]
                xml_conversions = param.iter("conversion")

                # extract scalings
                param_scalings = []
                for idx, conv in enumerate(xml_conversions):
                    name = (
                        conv.attrib["units"]
                        if "units" in conv.attrib
                        else "Conv{}".format(idx)
                    )
                    scaleid = f"{ident}_{name}"

                    # store scaling in global container
                    xml_elements[protocol]["Base"]["scalings"][scaleid] = conv

                    # mark scaling as used by this parameter
                    param_scalings.append(scaleid)

                # store parameter information to base definition
                xml_elements[protocol]["Base"]["params"][ident] = {
                    "param": param,
                    "scalings": param_scalings,
                }

                # create definition key for each specific ECU
                if param.tag == "ecuparam":
                    xml_ecus = param.iter("ecu")
                    for ecu in xml_ecus:
                        ids = ecu.attrib["id"].upper().split(",")
                        addrs = ecu.findall("address")

                        for ecuid in ids:
                            if ecuid not in xml_elements[protocol]:
                                xml_elements[protocol][ecuid] = {
                                    "params": {},
                                    "parents": ["Base"],
                                }

                            # store ecu-specific parameter info
                            xml_elements[protocol][ecuid]["params"][ident] = {
                                "param": param,
                                "scalings": param_scalings,
                                "addrs": addrs,
                            }

            xml_elements[protocol]["Base"]["switches"] = {
                param.attrib["id"]: param for param in xml_switches
            }

            xml_elements[protocol]["Base"]["dtcodes"] = {
                param.attrib["id"]: param for param in xml_dtcodes
            }

        else:
            _logger.warn(f"TODO: Implement logger protocol {protocol}")

    # instantiate LoggerDef instances
    logger_defs = LoggerProtocolContainer(None, name="Logger Protocols")

    for protocol in xml_elements:
        protocol_defs = LoggerDefContainer(
            logger_defs, name=f"{protocol.name} Definitions"
        )
        logger_defs[protocol] = protocol_defs

        # generate all scalings
        scaling_cont = ScalingContainer(None, name="Scalings")
        scaling_xmls = xml_elements[protocol]["Base"]["scalings"]
        for name in scaling_xmls:
            xml = scaling_xmls[name]
            kw = _scaling_from_rrlogger_xml(xml)
            scaling_cont[name] = Scaling(scaling_cont, name, **kw)

        pending_defs = list(xml_elements[protocol].keys())

        while pending_defs:
            current_id = pending_defs.pop(0)
            current_xml = xml_elements[protocol][current_id]

            # revisit this definition after all its parents are instantiated
            if set(current_xml.get("parents", [])) - set(protocol_defs.keys()):
                pending_defs.append(current_id)
                continue

            # parents ordered from inner to outermost hierarchy level
            parent_cont = LoggerDefContainer(
                None,
                data={
                    x: protocol_defs[x]
                    for x in reversed(current_xml.get("parents", []))
                },
                name="Parents",
            )

            # generate parameters
            param_cont = LogParamContainer(None, name="Logger Parameters")
            for ident, param_info in current_xml.get("params", {}).items():
                kw = _extract_param_from_rrlogger_xml(param_info, scaling_xmls)
                param = LogParamDef(param_cont, ident, **kw)
                param_cont[ident] = param

            # generate switches
            switch_cont = LogParamContainer(None, name="Logger Switches")
            for ident, xml in current_xml.get("switches", {}).items():
                kw = {
                    "name": xml.attrib["name"],
                    "description": xml.attrib["desc"],
                    "endpoint": LoggerEndpoint(int(xml.attrib["target"])),
                    "byte_idx": int(xml.attrib["ecubyteindex"]),
                    "bit_idx": int(xml.attrib["bit"]),
                    "datatype": DataType(int(xml.attrib["bit"])),
                    "addresses": [int(xml.attrib["byte"], base=16)],
                }
                switch = LogParamDef(switch_cont, ident, **kw)
                switch_cont[ident] = switch

            # generate DTCs
            code_cont = LogParamContainer(None, name="Logger DTCs")
            for ident, xml in current_xml.get("dtcodes", {}).items():
                kw = {
                    "name": xml.attrib["name"],
                    "description": xml.attrib["desc"],
                    "bit": DataType(int(xml.attrib["bit"])),
                    "temp_addr": int(xml.attrib["tmpaddr"], base=16),
                    "mem_addr": int(xml.attrib["memaddr"], base=16),
                }
                code = LogParamDef(code_cont, ident, **kw)
                code_cont[ident] = code

            logger_def = LoggerDef(
                current_id,
                parents=parent_cont,
                parameters=param_cont,
                switches=switch_cont,
                dtcodes=code_cont,
            )
            parent_cont.parent = logger_def
            param_cont.parent = logger_def
            switch_cont.parent = logger_def
            code_cont.parent = logger_def

            protocol_defs[current_id] = logger_def

        _logger.info(
            "Loaded {} RomRaider Logger {} protocol definitions".format(
                len(protocol_defs), protocol.name
            )
        )

    return logger_defs, scaling_cont
