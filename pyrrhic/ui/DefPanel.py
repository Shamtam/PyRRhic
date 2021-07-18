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

from pyrrhic.ui.ScalingPanel import ScalingPanel
from pyrrhic.common.structures import Scaling
from pubsub import pub

from .panelsBase import bDefPanel
from .InfoPanel import InfoPanel
from ..common.definitions import EditorDef, LoggerDef, ROMDefinition
from .ViewModels import DefViewModel


class DefPanel(bDefPanel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._def_mgr = None

        pub.subscribe(self._register_defs, "definitions.init")
        pub.subscribe(self._switch_page, "definitions.select")

    def _register_defs(self, mgr):
        self._def_mgr = mgr
        self._initialize_panels()

        self._dvc.ClearColumns()

        self._model = DefViewModel(mgr.Definitions)
        self._dvc.AssociateModel(self._model)
        self._model.DecRef()

        self._dvc.AppendTextColumn("Name", 0)

        self._model.Cleared()

    def _initialize_panels(self):
        if not self._def_mgr:
            return

        self._notebook.DeleteAllPages()
        self._info_panel = InfoPanel(self._notebook, self._def_mgr)
        self._scaling_panel = ScalingPanel(self._notebook)

        self._notebook.AddPage(self._info_panel, "Info")
        self._notebook.AddPage(self._scaling_panel, "Scaling")

    def _switch_page(self, item):
        if isinstance(item, EditorDef):
            panel = self._info_panel
        elif isinstance(item, Scaling):
            panel = self._scaling_panel

        if panel:
            panel.populate(item)
            self._notebook.ChangeSelection(self._notebook.FindPage(panel))

    def OnItemSelection(self, event):
        node = self._model.ItemToObject(event.GetItem())
        self._switch_page(node)
