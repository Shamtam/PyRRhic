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

from collections import UserDict
from datetime import datetime
from json import JSONEncoder
from queue import Queue
from threading import Thread, Event


class Container(UserDict):
    """Dictionary that stores a pointer to its containing parent"""

    def __init__(self, parent, data={}, name=""):
        super().__init__(data)
        self.parent = parent
        self.name = name

    def __repr__(self):
        return '<{}: "{}" [{}]>'.format(
            type(self).__name__, self.name, len(self.data)
        )


class DefinitionContainer(Container):
    pass


class LoggerProtocolContainer(Container):
    pass


class InfoContainer(Container):
    pass


class ScalingContainer(Container):
    pass


class CategoryContainer(Container):
    pass


class TableContainer(Container):
    pass


class LogParamContainer(Container):
    pass


class ECUFlashSearchTree(Container):
    pass


class PyrrhicJSONSerializable(object):
    """Interface to be implemented by JSON-serializable objects"""

    def to_json(self):
        return NotImplementedError

    def from_json(self):
        return NotImplementedError


class PyrrhicJSONEncoder(JSONEncoder):
    def default(self, obj):

        if isinstance(obj, PyrrhicJSONSerializable):
            return obj.to_json()

        return JSONEncoder.default(self, obj)


class PyrrhicMessage(object):
    def __init__(self, msg, data=None):
        self._msg = msg
        self._data = data
        self._timestamp = datetime.now()

    @property
    def Message(self):
        return self._msg

    @property
    def Data(self):
        return self._data

    @property
    def RawTimestamp(self):
        "`datetime` containing message time"
        return self._timestamp

    @property
    def TimeStr(self):
        "`str` with message time in HH:MM:SS format"
        return self._timestamp.strftime("%H:%M:%S")

    @property
    def DateStr(self):
        "`str` with message date in YYYY-MM-DD format"
        return self._timestamp.strftime("%Y-%m-%d")


class PyrrhicWorker(Thread):
    "Generalized worker thread base class."

    def __init__(self, *args, **kwargs):
        """Initializer"""

        # check for target/args keywords, and add self to positional
        # arguments if both keys were specified
        if all([x in kwargs for x in ["target", "args"]]):
            kwargs["args"] = (self, *kwargs["args"])
            self.run_loop = kwargs["target"]

        super().__init__(*args, **kwargs)
        self._in_q = Queue()
        self._out_q = Queue()
        self._stoprequest = Event()

        # override run method during initialization
        if "target" in kwargs:
            self.run_loop = kwargs["target"]

    def run(self):
        """Top-level worker routine loop.

        Loops the `self.run_loop` while `self._stoprequest` is not set or no
        unhandled exceptions occur. After the loop is run, `self.post_run` is
        called.
        """
        while not self._stoprequest.is_set():
            try:
                self.run_inner()
            except Exception as e:  # noqa: F841
                break

        self.post_run()

    def run_loop(self):
        """Main worker routine loop, to be implemented in subclasses."""
        raise NotImplementedError

    def post_run(self):
        """Function to be run before worker exit, override in subclasses."""
        pass

    def join(self, timeout=None):
        self._stoprequest.set()
        super().join(timeout)

    @property
    def InQueue(self):
        "`Queue` used to send messages to the worker thread"
        return self._in_q

    @property
    def OutQueue(self):
        "`Queue` used by the worker thread to send messages"
        return self._out_q
