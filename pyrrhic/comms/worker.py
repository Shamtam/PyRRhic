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

from datetime import datetime, timedelta
from enum import IntFlag, auto
from queue import Empty
from time import sleep

from ..common.enums import LoggerEndpoint
from ..common.helpers import PyrrhicMessage, PyrrhicWorker

class CommsState(IntFlag):
    NOT_INITALIZED  = auto() # Comms device open, endpoint not initialized
    INITIALIZED     = auto() # endpoint init succeeded, ready for query
    NO_QUERY        = auto() # no query configured
    VALID_QUERY     = auto() # valid query configured
    NO_OUT_FILE     = auto() # no output file specified
    VALID_OUT_FILE  = auto() # valid output file specified
    WRITING_TO_FILE = auto() # writing data to output file

class CommsWorker(PyrrhicWorker):
    def __init__(self, interface_name, phy, protocol, **kwargs):
        super(CommsWorker, self).__init__()
        self._protocol = protocol(interface_name, phy)
        self._interface = self._protocol.Interface
        self._state = CommsState.NOT_INITALIZED
        self._last_init_time = datetime.now() - timedelta(seconds=5)
        self._current_endpoint = kwargs.pop('endpoint', LoggerEndpoint.ECU)
        self._current_query = {}
        self._current_filepath = None

    def run(self):
        "Main communication working loop"

        while not self._stoprequest.is_set():
            _cur_time = datetime.now()

            # check for any messages from UI queue
            try:
                m = self._in_q.get(None)
            except Empty:
                m = None

            try:
                # handle messages from UI
                if m:
                    msg = m.Message
                    data = m.Data

                    if msg == 'SetEndpoint':
                        self._init_endpoint(data)

                # do stuff

                # try initializing if necessary and retry time has lapsed
                if(
                    self._state == CommsState.NOT_INITALIZED and
                    (_cur_time - self._last_init_time) > timedelta(seconds=5)
                ):
                    self._init_endpoint()
                    continue

                # A2UI001L - log throttle position 4-byte
                # self._protocol.read_block(LoggerTarget.ECU, 0xff69b0, 4, continuous=True)

                # check if endpoint has provided any data
                resp = self._interface.read()
                if resp:
                    self._out_q.put(
                        PyrrhicMessage(
                            'ECUMessage',
                            data=self._protocol.strip_response(resp)
                        )
                    )
            except Exception as e:
                self._out_q.put(PyrrhicMessage('Exception', data=e))
                continue

            finally:
                # sleep to avoid excessive CPU usage
                sleep(0.01)

        # clean-up upon worker thread exit
        return

    def _init_endpoint(self):
        "Initialize and identify the endpoint, update state accordingly"
        resp = self._protocol.identify_endpoint(self._current_endpoint)
        self._last_init_time = datetime.now()
        if resp:
            self._out_q.put(
                PyrrhicMessage('Init', resp)
            )
            self._state = CommsState.INITIALIZED
        else:
            self._state = CommsState.NOT_INITALIZED

    def _set_endpoint(self, endpoint):
       self._current_endpoint = (
           endpoint if isinstance(endpoint, LoggerEndpoint) else None
       )

    def _set_query(self, param_list):
        """Set the current logging query.

        Arguments:
        - `param_list`: `list` of `LogParam`s specifying all parameters
            the worker should requesting from the target
        """

        # store param list local to this thread

        # determine most efficient parameter packing for request

        # determine expected response signature from protocol

        # update current worker state

        pass

    def _set_output_file(self, file_path):
        """Set the current output file to stream logging data to

        Arguments:
        - `file_path`: `str` containing absolute filepath to write to
        """

        # check if filepath is valid and writable

        # update state to indicate valid output file
        pass
