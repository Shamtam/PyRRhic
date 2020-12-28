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

from logging import Formatter, CRITICAL, ERROR, WARNING, INFO, DEBUG

_console_formatter = Formatter(
    '[{asctime}] {message}',
    '%H:%M:%S',
    style='{'
)

_file_formatter = Formatter(
    '[{levelname:<8}] {module}/{funcName} ({filename}:{lineno}): {message}',
    '%H:%M:%S',
    style='{'
)

_lvl_map = {
    CRITICAL: 0,
    ERROR   : 1,
    WARNING : 2,
    INFO    : 3,
    DEBUG   : 4,
}
