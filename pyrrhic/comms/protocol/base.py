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

class ECUProtocol(object):

    # tuple of phy classes supported by this protocol
    _supported_phy = ()

    # display name of this protocol in the UI
    _display_name = ''

    def __init__(self, interface_name, phy_cls, **kwargs):
        """Base initializer for ECU protocol encapsulations

        Keywords are specific to the particular `ECUProtocol` subclass

        Arguments:
        - `interface_name`: `str` containing the `CommunicationDevice`
            specific name used to open the underlying device
        - `phy_class`: `CommunicationDevice` subclass to be used to
            handle comms with the ECU
        """
        self._phy = None
        self._protocol = None

    def identify_target(self, target):
        """Returns endpoint identification information

        Arguments:
        - `target`: `LoggerTarget` specifying the target to init/identify
        """
        raise NotImplementedError

    @property
    def Protocol(self):
        "Returns the `LoggerProtocol` implemented by this instance"
        return self._protocol

    @property
    def Interface(self):
        "Returns the underlying `CommunicationDevice` subclass"
        return self._phy
