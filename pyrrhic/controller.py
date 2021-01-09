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

import json
import logging
import os
import threading

from .common import _prefs_file
from .common.definitions import DefinitionManager, ROMDefinition
from .common.helpers import PyrrhicJSONEncoder
from .common.preferences import PreferenceManager
from .common.rom import Rom

_logger = logging.getLogger(__name__)

class DefinitionFound(Exception):
    pass

class PyrrhicController(object):
    "Top-level application controller"

    def __init__(self, frame):
        self._frame = frame
        self._prefs = PreferenceManager(_prefs_file)

        # create default preference file if it doesn't already exist
        if not os.path.isfile(_prefs_file):
            self.save_prefs()

        self._defmgr = DefinitionManager(
            ecuflashRoot=self._prefs['ECUFlashRepo'].Value,
            rrlogger_path=self._prefs['RRLoggerDef'].Value
        )

        self._roms = {}

    def open_rom(self, fpath):
        "Load the given filepath as a ROM image"

        if fpath in self._roms:
            # TODO: push status notification indicating ROM already loaded
            return

        defn = None

        _logger.debug('Loading ROM image {}'.format(fpath))

        # load raw image bytes
        with open(fpath, 'rb') as fp:
            rom_bytes = memoryview(fp.read())

        # inspect bytes at all internal ID addresses specified in definitions
        try:
            for addr in self._defmgr.ECUFlashSearchTree:
                len_tree = self._defmgr.ECUFlashSearchTree[addr]

                for nbytes in len_tree:
                    vals = len_tree[nbytes]

                    id_bytes = rom_bytes[addr:addr + nbytes].tobytes()
                    if id_bytes in vals:
                        defn = vals[id_bytes]
                        raise DefinitionFound

        except DefinitionFound:
            defn.resolve_dependencies(self._defmgr.ECUFlashDefs)
            d = ROMDefinition(EditorDef=defn)
            self._roms[fpath] = Rom(fpath, rom_bytes, d)
            return

        except Exception as e:
            raise

        self._frame.error_box(
            'Undefined ROM',
            'Unable to find matching definition for ROM'
        )

    def process_preferences(self):
        "Resolve state after any preference changes"

        ecuflash_repo_dir = self._prefs['ECUFlashRepo'].Value
        if ecuflash_repo_dir:
            self._defmgr.load_ecuflash_repository(ecuflash_repo_dir)

        self._frame.refresh_tree()

    def save_prefs(self):

        with open(_prefs_file, 'w') as fp:
            _logger.info('Saving preferences to {}'.format(_prefs_file))
            json.dump(self._prefs, fp, cls=PyrrhicJSONEncoder, indent=4)

    @property
    def LoadedROMs(self):
        return self._roms

    @property
    def Preferences(self):
        return self._prefs

    @property
    def DefsValid(self):
        return self._defmgr.IsValid
