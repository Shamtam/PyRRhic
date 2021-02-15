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

    LOG_QUERY       = auto() # valid logger query configured
    CONT_LOG_QUERY  = auto() # endpoint is continuously supplying data

    LIVETUNE_QUERY  = auto() # requesting RAM tune header/table info
    LIVETUNE_WRITE  = auto() # writing RAM tune data
    LIVETUNE_VERIFY = auto() # verifying the last RAM data write

    WAIT_FOR_RESP   = auto() # waiting for query response

    HAS_OUT_FILE    = auto() # valid output file specified
    WRITING_TO_FILE = auto() # writing data to output file

class CommsWorker(PyrrhicWorker):
    def __init__(self, interface_name, phy, protocol, **kwargs):
        super(CommsWorker, self).__init__()
        self._protocol = protocol(interface_name, phy)
        self._interface = self._protocol.Interface
        self._state = CommsState.UNDEFINED
        self._last_init_time = datetime.now() - timedelta(seconds=5)
        self._current_endpoint = kwargs.pop('endpoint', LoggerEndpoint.ECU)
        self._current_log_query = None
        self._current_livetune_query = None
        self._current_livetune_write = None
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

                    elif msg == 'LogQuery':
                        self._set_logger_query(data)

                    elif msg == 'LiveTuneQuery':
                        self._set_live_tune_query(data)

                    elif msg == 'LiveTuneWrite':
                        self._set_live_tune_write(data)

                # try initializing if necessary and retry time has lapsed
                if not (self._state & CommsState.INITIALIZED):
                    if (_cur_time - self._last_init_time) > timedelta(seconds=5):
                        self._init_endpoint()
                    continue

                # write has been specified
                if self._state & (CommsState.LIVETUNE_WRITE):
                    if self._state & CommsState.LIVETUNE_VERIFY:
                        if not self._state & CommsState.WAIT_FOR_RESP:
                            self._initiate_query()
                        else:
                            self._check_query_response()
                    else:
                        self._initiate_write()

                # query has been specified
                elif self._state & (CommsState.LOG_QUERY | CommsState.LIVETUNE_QUERY):

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
        if self._state & (CommsState.CONT_LOG_QUERY | CommsState.WAIT_FOR_RESP):
            # interrupt continuous query
            self._protocol.interrupt_endpoint(self._current_endpoint)

        # call the destructor for the protocol, to ensure the physical
        # device layer is released
        del self._protocol

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

    def _set_logger_query(self, request):
        """Set the current logging query.

        Arguments:
        - `request`: `4-tuple` (`func`, `args`, `kwargs`, `continuous`)
        """
        if not (self._state & CommsState.INITIALIZED):
            return

        if request:

            # update the current query
            func, args, kwargs, cont = request
            if hasattr(self._protocol, func):
                self._current_log_query = request
                self._state |= CommsState.LOG_QUERY

                flags = CommsState.CONT_LOG_QUERY
                if cont:
                    self._state |= flags
                else:
                    self._state &= ~flags

            # interrupt continuous query and clear waiting flag if not
            # currently reading/writing live tuning status
            if (
                not self._state & (
                    CommsState.LIVETUNE_QUERY | CommsState.LIVETUNE_WRITE
                ) and
                self._state & (
                    CommsState.CONT_LOG_QUERY | CommsState.WAIT_FOR_RESP
                )
            ):
                self._protocol.interrupt_endpoint(self._current_endpoint)
                self._interface.clear_buffers()
                self._state &= ~CommsState.WAIT_FOR_RESP

        # clear logging query
        else:
            self._current_log_query = None
            self._state &= ~CommsState.LOG_QUERY
            self._state &= ~CommsState.CONT_LOG_QUERY

        self._state &= ~CommsState.WAIT_FOR_RESP

    def _set_live_tune_query(self, request):
        """Sets the current live-tune state query.

        Sets the `LIVETUNE_QUERY` status flag, which will pause all
        logging until it is reset.

        Arguments:
        - `request`: `4-tuple` (`func`, `args`, `kwargs`, `False`) or
            `None` to clear the stored query
        """

        if not self._state & CommsState.INITIALIZED:
            return

        # update current livetune query
        if request:

            # only modify livetune query if currently not reading/writing
            if self._state & (CommsState.LIVETUNE_QUERY | CommsState.LIVETUNE_WRITE):
                return

            func, args, kwargs, cont = request
            if hasattr(self._protocol, func):
                self._current_livetune_query = request
                self._state |= CommsState.LIVETUNE_QUERY

        # clear current livetune query
        else:
            self._current_livetune_query = None
            self._state &= ~CommsState.LIVETUNE_QUERY

    def _set_live_tune_write(self, payload):
        """Sets the current live-tune payload to be written

        Sets the `LIVETUNE_WRITE` status flag

        Arguments:
        - `payload`: `2-tuple` of `3-tuple`s containing write and verify
            function calls and args/keywords
        """

        if not self._state & CommsState.INITIALIZED:
            return

        # update current livetune write
        if payload:

            # only modify livetune write if currently not reading/writing
            if self._state & (CommsState.LIVETUNE_QUERY | CommsState.LIVETUNE_WRITE):
                return

            write, verify, check = payload
            func, args, kwargs = write
            if hasattr(self._protocol, func):
                self._current_livetune_write = payload
                self._state |= CommsState.LIVETUNE_WRITE

        # clear the current write
        else:
            self._current_livetune_write = None
            self._state &= ~CommsState.LIVETUNE_WRITE

    def _initiate_query(self):
        # TODO: fix state changes, shouldn't need to check query here
        if self._state & CommsState.LIVETUNE_VERIFY and self._current_livetune_write:
            write, verify, check = self._current_livetune_write
            func, args, kwargs = verify
        elif self._state & CommsState.LIVETUNE_QUERY and self._current_livetune_query:
            func, args, kwargs, cont = self._current_livetune_query
        elif self._state & CommsState.LOG_QUERY and self._current_log_query:
            func, args, kwargs, cont = self._current_log_query
        else:
            return

        # send query request to endpoint
        args = (self._current_endpoint, *args)
        getattr(self._protocol, func)(*args, **kwargs)

        # set state
        self._state |= CommsState.WAIT_FOR_RESP

    def _initiate_write(self):
        if self._current_livetune_write:
            write, verify, check = self._current_livetune_write
            func, args, kwargs = write

        args = (self._current_endpoint, *args)
        getattr(self._protocol, func)(*args, **kwargs)
        self._state |= CommsState.LIVETUNE_VERIFY

    def _check_query_response(self):

        if self._state & CommsState.LIVETUNE_VERIFY:
            msg = 'LiveTuneVerify'
        elif self._state & CommsState.LIVETUNE_QUERY:
            msg = 'LiveTuneResponse'
        elif self._state & CommsState.LOG_QUERY:
            msg = 'LogQueryResponse'
        else:
            return

        resp = self._protocol.check_receive_buffer()

        # got a response, handle and clear state/flag variables
        if resp:

            if msg == 'LiveTuneVerify':
                write, verify, check = self._current_livetune_write

                # write successful, clear current write and write/verify flags
                if check(resp):
                    self._current_livetune_write = None
                    self._state &= ~(
                        CommsState.LIVETUNE_WRITE | CommsState.LIVETUNE_VERIFY
                    )
                # write unsuccessful, clear verify and waiting flag to retry write
                else:
                    self._state &= ~(
                        CommsState.LIVETUNE_VERIFY | CommsState.WAIT_FOR_RESP
                    )
                    return

            elif msg == 'LiveTuneResponse':
                self._current_livetune_query = None
                self._state &= ~CommsState.LIVETUNE_QUERY

            elif msg == 'LogQueryResponse':
                self._current_log_query = None
                self._state &= ~CommsState.LOG_QUERY

            self._out_q.put(PyrrhicMessage(msg, data=resp))

            # if non-continuous, reset the waiting flag
            if not (self._state & CommsState.CONT_LOG_QUERY):
                self._state &= ~CommsState.WAIT_FOR_RESP

    def _set_output_file(self, file_path):
        """Set the current output file to stream logging data to

        Arguments:
        - `file_path`: `str` containing absolute filepath to write to
        """

        # check if filepath is valid and writable

        # update state to indicate valid output file
        pass
