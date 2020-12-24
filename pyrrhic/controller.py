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
import threading

_logger = logging.getLogger(__name__)

from .common.rom import Rom
from .common.preferences import PreferenceManager
from .common.definitions import DefinitionManager

class DefinitionFound(Exception):
    pass

class PyrrhicController(object):
    "Top-level application controller"

    def __init__(self, frame):
        self._frame = frame
        self._prefs = PreferenceManager()
        self._defmgr = DefinitionManager()

        self._roms = {}

    def open_rom(self, fpath):
        "Load the given filepath as a ROM image"

        if fpath in self._roms:
            # TODO: push status notification indicating ROM already loaded
            return

        rom, defn = None, None

        # load raw image bytes
        with open(fpath, 'rb') as fp:
            rom_bytes = fp.read()

        # inspect bytes at all internal ID addresses specified in definitions
        for addr in self._defmgr.UniqueInternalIDAddrs:

            try:

                # check for a matching hex ID
                for id_length in self._defmgr.UniqueHexIDLengths:
                    id_bytes = rom_bytes[addr:addr+id_length]
                    id_str = id_bytes.hex().upper()

                    if id_str in self._defmgr.ECUFlashDefsByHex:
                        defn = self._defmgr.ECUFlashDefsByHex[id_str]
                        raise DefinitionFound

                # check for matching string ID
                for id_length in self._defmgr.UniqueStringIDLengths:

                    try:
                        id_str = rom_bytes[addr:addr+id_length].decode('ascii').upper()
                    except UnicodeDecodeError:
                        continue

                    if id_str in self._defmgr.ECUFlashDefsByString:
                        defn = self._defmgr.ECUFlashDefsByString[id_str]
                        raise DefinitionFound

            except DefinitionFound:
                self._roms[fpath] = Rom(fpath, rom_bytes, defn)
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

    @property
    def Preferences(self):
        return self._prefs

    @property
    def DefsValid(self):
        return self._defmgr.IsValid