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

import struct

from queue import Empty

from .common import _prefs_file
from .common.definitions import DefinitionManager, ROMDefinition
from .common.helpers import PyrrhicJSONEncoder, PyrrhicMessage
from .common.preferences import PreferenceManager
from .common.rom import Rom

from .comms.phy import get_all_interfaces
from .comms.protocol import get_all_protocols, LogQueryParseError
from .comms.worker import CommsWorker

_logger = logging.getLogger(__name__)

class DefinitionFound(Exception):
    pass

class PyrrhicController(object):
    "Top-level application controller"

    def __init__(self, editor_frame=None, logger_frame=None):
        self._available_interfaces = {}
        self._editor_frame = editor_frame
        self._logger_frame = logger_frame
        self._comms_worker = None
        self._query = None
        self._prefs = PreferenceManager(_prefs_file)

        # create default preference file if it doesn't already exist
        if not os.path.isfile(_prefs_file):
            self.save_prefs()

        self._defmgr = DefinitionManager(
            ecuflashRoot=self._prefs['ECUFlashRepo'].Value,
            rrlogger_path=self._prefs['RRLoggerDef'].Value
        )

        self.refresh_interfaces()
        self._roms = {}

# Preferences
    def process_preferences(self):
        "Resolve state after any preference changes"

        ecuflash_repo_dir = self._prefs['ECUFlashRepo'].Value
        rrlogger_file = self._prefs['RRLoggerDef'].Value

        if ecuflash_repo_dir:
            self._defmgr.load_ecuflash_repository(ecuflash_repo_dir)
        if rrlogger_file:
            self._defmgr.load_rrlogger_file(rrlogger_file)

        self._editor_frame.refresh_tree()

    def save_prefs(self):

        with open(_prefs_file, 'w') as fp:
            _logger.info('Saving preferences to {}'.format(_prefs_file))
            json.dump(self._prefs, fp, cls=PyrrhicJSONEncoder, indent=4)

# Editor
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

        self._editor_frame.error_box(
            'Undefined ROM',
            'Unable to find matching definition for ROM'
        )

# Logger
    def refresh_interfaces(self):
        self._available_interfaces = get_all_interfaces()

    def get_supported_protocols(self, interface_name):
        "`list` of `str` indicating protocols supported by the given interface"
        ret = []

        iface_phys = self._available_interfaces.get(interface_name, None)
        if iface_phys is None:
            _logger.warn(('Selected interface "{}" no longer available, try'
                ' refreshing available interfaces and try again').format(
                    interface_name
                )
            )
            return []

        protocols = get_all_protocols()
        for protocol_name in protocols:
            protocol, query = protocols[protocol_name]
            if protocol._supported_phy <= iface_phys:
                ret.append(protocol_name)

        return ret

    def spawn_logger(self, interface_name, protocol_name):
        iface_phys = self._available_interfaces[interface_name]
        protocol, query = get_all_protocols()[protocol_name]

        # get specific `CommunicationDevice` subclass for this protocol
        phy = list(protocol._supported_phy.intersection(iface_phys))[0]

        # store the query class
        self._query_cls = query

        # create the worker and spawn the new thread
        self._comms_worker= CommsWorker(interface_name, phy, protocol)
        self._comms_worker.start()

    def kill_logger(self):
        if self._comms_worker:
            _logger.debug('Killing communication thread')

            # signal comms thread to stop
            self._comms_worker.join()

            _logger.info('Logger disconnected')
            self._comms_worker = None
            self._logger_frame.on_connection(connected=False)

            # remove all parameters from UI
            params = self._query.Parameters
            for p in params:
                self.LoggerFrame.remove_gauge(p)
                p.disable()

            self._query_cls = None
            self._query = None

    def check_logger(self):
        "Idle event handler that checks logging thread for updates."
        if self._comms_worker is not None:
            try:
                item = self._comms_worker.OutQueue.get(False)
            except Empty as e:
                item = None

            if item:
                msg = item.Message
                time = item.RawTimestamp
                data = item.Data
                if msg == 'Init':
                    self._logger_init(data)
                elif msg == 'QueryResponse':

                    try:
                        self._query.extract_values(data)
                    except LogQueryParseError as e:
                        _logger.exception(e.message)

                    self._logger_frame.update_gauges()
                elif msg == 'Exception':
                    raise data

    def add_log_params(self, params):
        if self._comms_worker is not None:
            new_params = self._query.Parameters + params if self._query else params
            self._query = self._query_cls(new_params)
            req = self._query.generate_request() # TODO: runtime endpoint selection
            self._comms_worker.InQueue.put(
                PyrrhicMessage('UpdateQuery', req)
            )
        for param in params:
            self.LoggerFrame.add_gauge(param)
            param.enable()

    def remove_log_params(self, params):
        if not self._query:
            return

        if self._comms_worker is not None:
            new_params = [x for x in self._query.Parameters if x not in params]
            self._query = self._query_cls(new_params)
            if new_params:
                req = self._query.generate_request()
            else:
                req = None
            self._comms_worker.InQueue.put(
                PyrrhicMessage('UpdateQuery', req)
            )
        for param in params:
            self.LoggerFrame.remove_gauge(param)
            param.disable()

    def _logger_init(self, init_data):
        """
        Arguments:
        - `init_data`: 4-tuple containing logging initialization data:
            `(LoggerProtocol, LoggerEndpoint, identifier, raw_data)`
        """
        protocol, endpoint, identifier, capabilities = init_data
        _logger.debug('Received {} {} init'.format(protocol.name, endpoint.name))
        _logger.debug('Identifier: {}'.format(identifier))
        _logger.debug('Raw Bytes: {}'.format(capabilities.hex()))

        d = self._defmgr.RRLoggerDefs[protocol].get(identifier, None)
        if d is not None:
            d.resolve_dependencies(self._defmgr.RRLoggerDefs[protocol])
            d.resolve_valid_params(capabilities)
            _logger.info(
                'Connected to {}: {}'.format(endpoint.name, identifier)
            )
            self._logger_frame.on_connection(log_def=d)
        else:
            _logger.info(
                'Unable to find logger definition for endpoint {}'.format(
                    identifier
                )
            )

# Properties
    @property
    def LoadedROMs(self):
        return self._roms

    @property
    def Preferences(self):
        return self._prefs

    @property
    def DefsValid(self):
        return self._defmgr.IsValid

    @property
    def EditorFrame(self):
        return self._editor_frame

    @EditorFrame.setter
    def EditorFrame(self, frame):
        self._editor_frame = frame

    @property
    def LoggerFrame(self):
        return self._logger_frame

    @LoggerFrame.setter
    def LoggerFrame(self, frame):
        self._logger_frame = frame

    @property
    def AvailableInterfaces(self):
        return self._available_interfaces

    @property
    def CommsWorker(self):
        return self._comms_worker
