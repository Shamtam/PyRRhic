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

from .panelsBase import bTablePanel


class TablePanel(bTablePanel):

    def __init__(self, parent):
        super().__init__(parent)

    def initialize(self, info_list):
        """

        The first tuple in the list contains info from the selected definition.
        All other tuples contain any info from parents, from order of nearest
        inheritance, e.g. a hierarchy of BASE --> ROM1 --> ROM1a would result
        in the following list: ``[('ROM1a', {}), ('ROM1', {}), ('BASE', {})]``.

        Each ``tuple`` in the list is of the form ``(id, data)`` where ``id``
        is the unique ``str`` identifier for a definition, and ``data`` is
        a ``dict`` containing all of the info corresponding to the definition.
        """
        pass
