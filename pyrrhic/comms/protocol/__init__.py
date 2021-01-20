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

from ... import _debug
from .ssm import protocols as ssm_protocols

def get_all_protocols():
    """Get all configured protocols.

    Returns a `dict` with {`str`: (`EndpointProtocol`, `LogQuery`)}
    key-val pairs, where the keys are the display name of the protocol,
    and the values are a 2-tuple containing the appropriate subclasses
    of `EndpointProtocol` and `LogQuery`.
    """
    protocols = {}

    protocols.update(ssm_protocols)

    if _debug:
        from ...tests.comms.protocol import _protocols as test_protocols
        protocols.update(test_protocols)

    return protocols
