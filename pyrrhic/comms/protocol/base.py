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

from collections import deque
from datetime import datetime

from ...common.definitions import ROMDefinition

class TranslatorParseError(Exception):
    pass

class EndpointProtocol(object):

    # tuple of phy classes supported by this protocol
    _supported_phy = ()

    # display name of this protocol in the UI
    _display_name = ''

    def __init__(self, interface_name, phy_cls, **kwargs):
        """Base initializer for ECU protocol encapsulations

        Keywords are specific to the particular `EndpointProtocol` subclass

        Arguments:
        - `interface_name`: `str` containing the `CommunicationDevice`
            specific name used to open the underlying device
        - `phy_class`: `CommunicationDevice` subclass to be used to
            handle comms with the ECU
        """
        self._phy = None
        self._protocol = None

    def check_receive_buffer(self):
        """Checks receive buffer for a response to a logging query.

        Returns a `bytes` containing the raw query data from the
        endpoint if there is a pending response in the receive buffer,
        otherwise returns `None`.
        """
        raise NotImplementedError

    def identify_endpoint(self, endpoint):
        """Attempt to identify the endpoint.

        If successful, returns a 2-tuple `(identifier, raw_data)` where
        - `identifier` is a `str` that maps to the unique ID that is
            used as the key for this endpoint in the logger definitions.
        - `raw_data` is the raw `bytes` response from the endpoint

        If unsuccessful, returns `None`

        Arguments:
        - `endpoint`: `LoggerEndpoint` specifying the endpoint to identify
        """
        raise NotImplementedError

    def interrupt_endpoint(self):
        """Interrupt an endpoint currently in a state of transmitting
        continuous query data.
        """
        raise NotImplementedError

    @property
    def Interface(self):
        "Returns the underlying `CommunicationDevice` subclass"
        return self._phy

    @property
    def Protocol(self):
        "Returns the `LoggerProtocol` implemented by this instance"
        return self._protocol

class EndpointTranslator(object):
    """Translation layer base class that handles implementation
    details of translating raw byte data to/from an `EndpointProtocol`"""

    _max_request = None

    def __init__(self):
        self._def = None
        self._reset_freq_avg()

    def _check_def(self):
        if not self._def:
            raise RuntimeError(
                'Translator error, Unspecified logger definition'
            )

    def generate_log_request(self):
        """Return a `3-tuple` used to request a query from the endpoint.

        The returned `tuple` looks like `(func, args, kwargs)`, where
        `func` is the name of the `EndpointProtocol` callable that is
        called to send the request to the endpoint, and `args` and
        `kwargs` are arguments and keywords to pass to the callable.
        """
        raise NotImplementedError

    def generate_ramtune_state_request(self, tables=None):
        """Return a `3-tuple` used to request the current RAM tune state
        from the endpoint.

        See `generate_log_request` for more information.

        Keywords [Default]:
        - `tables` [`None`]: `list` of `RamTable`s to request. If no
        tables are passed in, this only requests the RAM tune header
        information to determine the RAM-tune state of the endpoint.
        """
        raise NotImplementedError

    def generate_ramtune_state_update(self, tables=None):
        """Return a `3-tuple` used to send any updates of the RAM tune
        state to the endpoint.

        See `generate_log_request` for more information.

        Keywords [Default]:
        - `tables` [`None`]: `list` of `RamTable`s to request. If no
        tables are passed in, this only updates the RAM tune header
        information.
        """
        raise NotImplementedError

    def extract_parameters(self, resp):
        """Update the current param values from the given byte string.

        Arguments:
        - `resp`: `bytes` containing the raw data from the endpoint
        """
        raise NotImplementedError

    def extract_ramtune_state(self, tables=None):
        """Update the current RAM tune state from the given byte string.

        Keywords [Default]:
        - `tables` [`None`]: `list` of `RamTable`s corresponding to the
            byte string passed in. If no tables are passed in, the byte
            string passed in corresponds to the RAM tune header info.
        """

    def _reset_freq_avg(self):
        self._resp_times = deque([], maxlen=10)
        self._last_resp_time = datetime.now()
        self._avg_freq = 0.0

    def _update_freq_avg(self):
        cur_time = datetime.now()
        dt = cur_time - self._last_resp_time
        self._resp_times.append(dt)
        self._last_resp_time = cur_time

        if len(self._resp_times) == self._resp_times.maxlen:
            deltas = [x.total_seconds() for x in self._resp_times]
            self._avg_freq = 1/(sum(deltas)/len(deltas))

    @property
    def MaxRequestSize(self):
        """Max number of bytes allowed in a request"""
        return self._max_request

    @property
    def Definition(self):
        return self._def

    @Definition.setter
    def Definition(self, d):
        if isinstance(d, ROMDefinition):
            self._def = d

    @property
    def EnabledParams(self):
        if self._def:
            return [
                x for x in self._def.LoggerDef.AllParameters.values()
                if x.Enabled
            ]
        else:
            return []

    @property
    def EnabledSwitches(self):
        if self._def:
            return [
                x for x in self._def.LoggerDef.AllSwitches.values()
                if x.Enabled
            ]
        else:
            return []

    @property
    def SupportsLiveTune(self):
        """Return whether or not it is possible to live tune this endpoint."""
        raise NotImplementedError

    @property
    def LiveTuneData(self):
        """`LiveTune` instance."""
        raise NotImplementedError

    @property
    def AverageFreq(self):
        "Average frequency of response updates, in Hz"
        return self._avg_freq
