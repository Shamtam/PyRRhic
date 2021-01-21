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
    UNDEFINED       = 0      # state unknown/uninitialized
    INITIALIZED     = auto() # endpoint init succeeded, ready for query
    HAS_QUERY       = auto() # valid query configured
    CONT_QUERY      = auto() # expecting data from endpoint
    WAIT_FOR_RESP   = auto() # non-continuous and waiting for response
    HAS_OUT_FILE    = auto() # valid output file specified
    WRITING_TO_FILE = auto() # writing data to output file

class CommsWorker(PyrrhicWorker):
    def __init__(self, interface_name, phy, protocol, **kwargs):
        super(CommsWorker, self).__init__()
        self._protocol = protocol(interface_name, phy)
        self._interface = self._protocol.Interface
        self._state = CommsState.UNDEFINED
        self._last_init_time = datetime.now() - timedelta(seconds=5)
        self._last_response_time = None
        self._current_endpoint = kwargs.pop('endpoint', LoggerEndpoint.ECU)
        self._current_query = None
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

                    elif msg == 'UpdateQuery':
                        self._set_query(data)

                # try initializing if necessary and retry time has lapsed
                if not (self._state & CommsState.INITIALIZED):
                    if (_cur_time - self._last_init_time) > timedelta(seconds=5):
                        self._init_endpoint()
                    continue

                # query has been specified
                if self._state & CommsState.HAS_QUERY:

                    # initiate query and restart loop if necessary
                    if not self._state & CommsState.WAIT_FOR_RESP:
                        self._initiate_query()
                    else:
                        self._check_query_response()

            except Exception as e:
                self._out_q.put(PyrrhicMessage('Exception', data=e))
                continue

            finally:
                # sleep worker thread to avoid excessive CPU usage
                sleep(0.01)

        # clean-up upon worker thread exit
        if self._state & (CommsState.CONT_QUERY | CommsState.WAIT_FOR_RESP):
            # interrupt continuous query
            pass

    def _init_endpoint(self):
        "Initialize and identify the endpoint, update state accordingly"

        self._last_init_time = datetime.now()

        try:
            resp = self._protocol.identify_endpoint(self._current_endpoint)
        except Exception as e:
            self._state &= ~CommsState.INITIALIZED
            return

        init_data = (self._protocol.Protocol, self._current_endpoint, *resp)
        self._out_q.put(PyrrhicMessage('Init', init_data))
        self._state |= CommsState.INITIALIZED

    def _set_endpoint(self, endpoint):
       self._current_endpoint = (
           endpoint if isinstance(endpoint, LoggerEndpoint) else None
       )

    def _set_query(self, request):
        """Set the current logging query.

        Arguments:
        - `request`: `4-tuple` (`func`, `args`, `kwargs`, `continuous`)
        """
        if not (self._state & CommsState.INITIALIZED):
            return

        if request:
            func, args, kwargs, cont = request
            if hasattr(self._protocol, func):
                self._current_query = request
                self._state |= CommsState.HAS_QUERY

                flags = CommsState.CONT_QUERY
                if cont:
                    self._state |= flags
                else:
                    self._state &= ~flags


        else:
            self._current_query = None
            self._state &= ~CommsState.HAS_QUERY
            self._state &= ~CommsState.CONT_QUERY

        self._state &= ~CommsState.WAIT_FOR_RESP

    def _initiate_query(self):
        func, args, kwargs, cont = self._current_query
        args = (self._current_endpoint, args) # add endpoint to args
        getattr(self._protocol, func)(*args, **kwargs)
        self._state |= CommsState.WAIT_FOR_RESP
        self._interface.clear_buffers()

    def _check_query_response(self):
        resp = self._protocol.check_logger_response()

        # got a response, push it to main thread to update
        if resp:
            cur_time = datetime.now()
            dt = (
                cur_time - self._last_response_time
                if self._last_response_time is not None
                else timedelta(seconds=0.0)
            )
            self._last_response_time = datetime.now()
            self._out_q.put(PyrrhicMessage('QueryResponse', data=(dt, resp)))

            # if non-continuous, reset the waiting flag
            if not (self._state & CommsState.CONT_QUERY):
                self._state &= ~CommsState.WAIT_FOR_RESP

    def _set_output_file(self, file_path):
        """Set the current output file to stream logging data to

        Arguments:
        - `file_path`: `str` containing absolute filepath to write to
        """

        # check if filepath is valid and writable

        # update state to indicate valid output file
        pass
