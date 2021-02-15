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

from pubsub import pub

from queue import Empty

from .common import _prefs_file
from .common.definitions import DefinitionManager, ROMDefinition
from .common.helpers import PyrrhicJSONEncoder, PyrrhicMessage
from .common.preferences import PreferenceManager
from .common.rom import Rom

from .comms.phy import get_all_interfaces
from .comms.protocol import get_all_protocols, TranslatorParseError
from .comms.worker import CommsWorker

_logger = logging.getLogger(__name__)

class DefinitionFound(Exception):
    pass

class PyrrhicController(object):
    "Top-level application controller"

    def __init__(self, editor_frame=None, logger_frame=None):

        self._prefs = PreferenceManager(_prefs_file)
        # create default preference file if it doesn't already exist
        if not os.path.isfile(_prefs_file):
            self.save_prefs()

        # editor-related
        self._editor_frame = editor_frame
        self._roms = {}

        # logger-related
        self._available_interfaces = {}
        self._logger_frame = logger_frame
        self._comms_worker = None
        self._comms_translator = None

        self._defmgr = DefinitionManager(
            ecuflashRoot=self._prefs['ECUFlashRepo'].Value,
            rrlogger_path=self._prefs['RRLoggerDef'].Value
        )

        pub.subscribe(self.live_tune_pull, 'livetune.state.pull.init')
        pub.subscribe(self.live_tune_push, 'livetune.state.push.init')
        pub.subscribe(self.toggle_table, 'editor.table.toggle')

        self.refresh_interfaces()

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
            self._editor_frame.push_status(
                'ROM {} already opened'.format(os.path.basename(fpath))
            )
            return

        defn = None

        _logger.debug('Loading ROM image {}'.format(fpath))

        # load raw image bytes
        with open(fpath, 'rb') as fp:
            rom_bytes = fp.read()

        # inspect bytes at all internal ID addresses specified in definitions
        try:
            for addr in self._defmgr.ECUFlashEditorSearchTree:
                len_tree = self._defmgr.ECUFlashEditorSearchTree[addr]

                for nbytes in len_tree:
                    vals = len_tree[nbytes]

                    id_bytes = rom_bytes[addr:addr + nbytes]
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

    def toggle_table(self, table):
        self.EditorFrame.toggle_table(table)

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
        protocol, translator = get_all_protocols()[protocol_name]

        # get specific `CommunicationDevice` subclass for this protocol
        phy = list(protocol._supported_phy.intersection(iface_phys))[0]

        # create the worker and spawn the new thread
        self._comms_worker= CommsWorker(interface_name, phy, protocol)
        self._comms_worker.start()

        # instantiate the appropriate `EndpointTranslator`
        self._comms_translator = translator()

    def kill_logger(self):
        if self._comms_worker:
            _logger.debug('Killing communication thread')

            # signal comms thread to stop
            self._comms_worker.join()

            _logger.info('Logger disconnected')
            self._comms_worker = None

        self._logger_frame.on_connection(connected=False)

        # remove all parameters from UI
        pub.sendMessage('logger.query.updated', params=[])
        if self._comms_translator:
            for p in (
                self._comms_translator.EnabledParams
                + self._comms_translator.EnabledSwitches
            ):
                p.disable()

        self._comms_translator = None

    def check_comms(self):
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
                elif msg == 'LogQueryResponse':

                    try:
                        self._comms_translator.extract_values(data)
                    except TranslatorParseError as e:
                        pub.sendMessage('logger.status',
                            center=e.message, temporary=True
                        )
                        return

                    pub.sendMessage('logger.freq.updated',
                        avg_freq=self._comms_translator.AverageFreq
                    )
                    pub.sendMessage('logger.params.updated')

                elif msg == 'LiveTuneResponse':

                    try:
                        self._comms_translator.extract_livetune_state(data)

                    except TranslatorParseError as e:
                        _logger.warning(e.message)

                    else:
                        req = self._comms_translator.generate_livetune_query()

                        # send next (or blank) query to worker
                        self._comms_worker.InQueue.put(
                            PyrrhicMessage('LiveTuneQuery', req)
                        )

                        if not req:
                            pub.sendMessage('livetune.state.pull.complete')

                elif msg == 'LiveTuneVerify':
                    self._comms_translator.validate_livetune_write()
                    req = self._comms_translator.generate_livetune_write()
                    self._comms_worker.InQueue.put(
                        PyrrhicMessage('LiveTuneWrite', req)
                    )

                    if not req:
                        pub.sendMessage('livetune.state.push.complete')

                elif msg == 'Exception':
                    raise data

    def update_log_params(self):
        if self._comms_worker is not None:

            # get new request and push it to worker thread
            req = self._comms_translator.generate_log_request()
            self._comms_worker.InQueue.put(
                PyrrhicMessage('LogQuery', req)
            )

            # send enabled parameters to logger frame for gauge updates
            params = self._comms_translator.EnabledParams
            switches = self._comms_translator.EnabledSwitches
            pub.sendMessage('logger.query.updated', params=(params + switches))

    def live_tune_pull(self):
        if self._comms_worker is not None:

            req = self._comms_translator.generate_livetune_query()
            if req:
                self._comms_worker.InQueue.put(
                    PyrrhicMessage('LiveTuneQuery', req)
                )
                pub.sendMessage('livetune.state.pending')

    def live_tune_push(self):
        if self._comms_worker is not None:

            req = self._comms_translator.generate_livetune_write()
            if req:
                self._comms_worker.InQueue.put(
                    PyrrhicMessage('LiveTuneWrite', req)
                )
                pub.sendMessage('livetune.state.pending')

    def sync_live_tune(self):
        if self._comms_worker is not None:

            self._comms_translator.generate_livetune

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

        defs = self._defmgr.Definitions[protocol].get(identifier, None)
        if defs is not None:

            # for logger init, CALID unimportant, so just pick first definition
            definition = next(iter(defs.values()))
            logger_def = definition.LoggerDef
            logger_def.resolve_dependencies(self._defmgr.RRLoggerDefs[protocol])
            logger_def.resolve_valid_params(capabilities)
            _logger.info(
                'Connected to {}: {}'.format(endpoint.name, identifier)
            )

            self._comms_translator.Definition = definition
            self._logger_frame.on_connection(translator=self._comms_translator)

            # check if a ROM corresponding to the initialized ECU has been loaded
            if self._roms:
                loaded_roms = set([
                    x.Definition.EditorID for x in self._roms.values()
                ])
                compatible_roms = set(defs.keys())
                matching_roms = loaded_roms.intersection(compatible_roms)

                # for any matching loaded roms, if the definition for this
                # loaded ROM is a ROMDefinition only containing editor defs
                for editor_id in matching_roms:
                    roms = filter(
                        lambda x: (
                            x.Definition.EditorID == editor_id
                            and x.Definition.LoggerDef is None
                        ),
                        self._roms.values()
                    )
                    for rom in roms:
                        rom.Definition = defs[editor_id]

                rom = None

                if len(matching_roms) == 1:
                    editor_id = next(iter(matching_roms))
                    rom = next(filter(
                        lambda x: x.Definition.EditorID == editor_id,
                        self._roms.values()
                    ))
                    self._comms_translator.initialize_livetune(rom)

                    if self._comms_translator.SupportsLiveTune:
                        pub.sendMessage(
                            'editor.livetune.enable',
                            livetune=self._comms_translator.LiveTuneData
                        )

        else:
            _logger.info(
                'Unable to find logger definition for endpoint {}'.format(
                    identifier
                )
            )
            self.kill_logger()

# Properties
    @property
    def LoadedROMs(self):
        return self._roms

    @property
    def ModifiedROMs(self):
        return {k: v for k, v in self._roms.items() if v.IsModified}

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
