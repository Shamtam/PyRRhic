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

import natsort

from .panelsBase import bInfoPanel


class InfoPanel(bInfoPanel):
    def __init__(self, parent, def_mgr):
        super().__init__(parent)
        self._defmgr = def_mgr

        self._box_map = {
            "id": self._id_box,
            "ecuid": self._ecuid_box,
            "internalidaddress": self._address_box,
            "internalid": self._calid_box,
        }
        self._cbox_map = {
            "year": self._year_cbox,
            "market": self._market_cbox,
            "make": self._make_cbox,
            "transmission": self._trans_cbox,
            "model": self._model_cbox,
            "submodel": self._submodel_cbox,
        }

        self._label_map = {
            "id": self._id_label,
            "ecuid": self._ecuid_label,
            "internalidaddress": self._address_label,
            "internalid": self._calid_label,
            "year": self._year_label,
            "market": self._market_label,
            "make": self._make_label,
            "transmission": self._trans_label,
            "model": self._model_label,
            "submodel": self._submodel_label,
        }

    def initialize(self):

        for box in self._box_map.values():
            box.Clear()

        vals = {k: set() for k in self._cbox_map}
        for defn in self._defmgr.Definitions.values():

            if not defn.editor_def:
                continue

            info = defn.editor_def.Info

            for key in self._cbox_map:
                box = self._cbox_map[key]
                val = info[key]

                if val is not None:
                    vals[key].add(val)

        for key in self._cbox_map:
            box = self._cbox_map[key]
            sorted_vals = natsort.natsorted(list(vals[key]))
            box.Clear()
            box.AppendItems(sorted_vals)

    def populate(self, editor_def):
        """Initialize the panel from the given :class:`.ROMDefinition`."""

        self.Freeze()
        self.initialize()

        info = editor_def.Info

        # populate plain textboxes
        for key in self._box_map:
            if key == "id":
                val = editor_def.Identifier
            else:
                val = info.get(key, None)

            if val is not None:
                box = self._box_map[key]

                if key == "internalid":
                    try:
                        val = val.decode("ascii")
                        self._calid_str_radio.SetValue(True)
                        self._calid_str_radio.Enable()
                    except UnicodeDecodeError:
                        val = val.hex(' ', 2)
                        self._calid_hex_radio.SetValue(True)
                        self._calid_str_radio.Disable()

                box.SetValue(val)

        # populate comboboxes
        for key in self._cbox_map:
            val = info.get(key, None)
            if val is not None:
                box = self._cbox_map[key]

                idx = box.FindString(val)
                if idx < len(box.Items):
                    box.Select(idx)

        parents = editor_def.Parents.keys()
        all_defs = list(set(self._defmgr.Definitions.keys()) - set(parents))
        all_defs = natsort.natsorted(list(all_defs))

        self._parents_lbox.Clear()
        self._defs_lbox.Clear()

        self._parents_lbox.Append(list(parents))
        self._defs_lbox.Append(all_defs)

        self.Thaw()
