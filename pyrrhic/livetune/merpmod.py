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

import struct

from .base import LiveTuneData, LiveTuneState

class MerpModLiveTune(LiveTuneData):

    @staticmethod
    def check_livetune_support(rom_def):
        params = rom_def.LoggerDef.AllParameters.values()

        try:
            begin_param = next(filter(
                lambda x: x.Name=='MerpMod RAM Tune Max Tables', params
            ))
            end_param = next(filter(
                lambda x: x.Name=='MerpMod RAM Tune End', params
            ))
        except StopIteration:
            return False

        if begin_param.Valid and end_param.Valid:
            return (
                0xFF000000 | begin_param.Addresses[0],
                0xFF000000 | end_param.Addresses[0]
            )
        else:
            return False

    def __init__(self, rom, start_addr, end_addr):
        ram_size = end_addr - start_addr
        super().__init__(rom, ram_size)
        self._start_addr = start_addr
        self._end_addr = end_addr
        self._temp_allocations = {}
        self._temp_activations = {}
        self.initialize()

    def check_allocatable(self, table):
        return (self.PendingSize + table.NumBytes + 8) <= self.TotalSize

    def _refresh_bytes(self):
        """Regenerate the mutable bytes based off the current state"""

        if not self.State & LiveTuneState.INITIALIZED:
            return

        current_allocations = self.AllocatedTables
        pending_allocations = self._temp_allocations

        # current tables to remain in RAM
        allocations = {
            k: v for k, v in current_allocations.items()
            if k not in pending_allocations
        }

        # add currently unallocated tables to be updated
        allocations.update({
            k: v for k, v in pending_allocations.items()
            if k not in current_allocations
        })

        # sort by ROM address
        allocations = {
            k: v for k, v in sorted(allocations.items(), key=lambda x: x[0])
        }

        # generate new byte array
        new_bytes = bytearray(b'\x00'*self._ram_size)

        # generate offset and table count bytes
        num_tables = len(allocations)
        offs = (num_tables - 1)*4 if num_tables > 0 else 0
        new_bytes[0:4] = struct.pack('>L', offs)
        new_bytes[4:8] = struct.pack('>L', num_tables)

        # generate ROM headers
        header_fmt = '>{:d}L'.format(num_tables)
        start = 8
        end = start + 4*num_tables
        new_bytes[start:end] = struct.pack(header_fmt, *allocations.keys())

        # generate RAM headers
        header_ptr = end
        data_ptr = header_ptr + 4*num_tables

        for table in allocations.values():
            addr = self.StartAddress + data_ptr
            table_data = table.Bytes.tobytes()
            data_len = table.NumBytes

            # set table RAM address
            addr = (0xFF000000 | addr) if table.Active else (0xFFFFFF & addr)
            table.RamAddress = addr

            # update table header and data
            new_bytes[header_ptr:header_ptr + 4] = struct.pack('>L', addr)
            new_bytes[data_ptr:data_ptr + data_len] = table_data

            # point table to new byte array
            table.initialize_bytes(
                memoryview(new_bytes)[data_ptr:data_ptr + data_len]
            )

            header_ptr += 4
            data_ptr += data_len

        self._bytes = new_bytes

    def stage_allocation(self, table):

        can_allocate = self.check_allocatable(table)
        pending = table.RomAddress in self._temp_allocations
        allocated = table.RomAddress in self.AllocatedTables

        # veto (un)allocation of active/pending active tables
        if table.Active or table.RomAddress in self.PendingActivations:
            return

        if not pending:

            if (not allocated and can_allocate) or allocated:

                # mark table for (un)allocation
                self._temp_allocations[table.RomAddress] = table

                # marking table for unallocation, need to clear the RAM
                # address and freeze any modified data
                if allocated:
                    table.RamAddress = None
                    table_data = table.Bytes.tobytes()
                    table.initialize_bytes(memoryview(table_data))

        else:
            # clear RAM address for pending tables to be removed
            table.RamAddress = None
            del self._temp_allocations[table.RomAddress]

        self._refresh_bytes()

    def stage_activation(self, table):

        allocated = table.RomAddress in self.AllocatedTables
        pending_unalloc = table.RomAddress in self._temp_allocations
        pending = table.RomAddress in self._temp_activations

        # veto activation of unallocated tables
        if not allocated or pending_unalloc:
            return

        if not pending:
            self._temp_activations[table.RomAddress] = table
            table.activate(True)
        else:
            del self._temp_activations[table.RomAddress]
            table.activate(False)

        self._refresh_bytes()

    def get_modified_bytes(self, force_deactivate=True):
        """Returns a `dict` of modified bytes keyed by address.

        The `force_deactivate` keyword, when `True`, will return all
        modified bytes with all tables deactivated regardless of their
        actual state, to ensure the ECU doesn't pull from RAM while
        writes are occurring.
        """
        if self._ram_bytes == self._bytes:
            return {}

        mod_bytes = self._bytes[:]

        if force_deactivate:
            num = struct.unpack('>L', mod_bytes[4:8])[0]

            if num > 0:
                start = 8 + num*4
                end = start + num*4
                addr = start
                while addr < end:
                    mod_bytes[addr] = 0
                    addr += 4

        out_bytes = {}

        for idx, (orig, mod) in enumerate(zip(self._ram_bytes, mod_bytes)):
            addr = 0xFFFFFF & (self.StartAddress + idx)
            if orig != mod:
                out_bytes[addr] = bytes([mod])

        return out_bytes

    def verify_write(self, bytes_dict):
        for addr, b in bytes_dict.items():
            offs = addr - (0xFFFFFF & self.StartAddress)
            self._ram_bytes[offs] = b

        if not self.State & LiveTuneState.WRITE_PENDING:
            self._temp_allocations = {}
            self._refresh_bytes()

    @property
    def StartAddress(self):
        """`int`"""
        return self._start_addr

    @property
    def EndAddress(self):
        """`int`"""
        return self._end_addr

    @property
    def RomAddresses(self):
        """`tuple` of `int`, ROM headers of currently allocated tables"""

        if self.State & LiveTuneState.INITIALIZED:
            num = self.NumTables

            if num == 0:
                return []

            start = 8
            end = start + 4*num
            fmt_str = '>{:d}L'.format(num)
            return struct.unpack(fmt_str, self._ram_bytes[start:end])

        else:
            return []

    @property
    def RamAddresses(self):
        """`tuple` of `int`, RAM headers of currently allocated tables"""

        if self.State & LiveTuneState.INITIALIZED:
            num = self.NumTables

            if num == 0:
                return []

            start = 8 + 4*num
            end = start + 4*num
            fmt_str = '>{:d}L'.format(num)
            return struct.unpack(fmt_str, self._ram_bytes[start:end])

        else:
            return []

    @property
    def NumTables(self):
        """Number of currently allocated tables"""
        return (
            struct.unpack('>L', self._ram_bytes[4:8])[0]
            if self.State & LiveTuneState.INITIALIZED
            else None
        )

    @property
    def AllocatedTables(self):
        if self.State & LiveTuneState.INITIALIZED:
            return {
                x: self._rom.get_ram_table_by_address(x)
                for x in self.RomAddresses
            }
        else:
            return {}

    @property
    def ActiveTables(self):
        if self.State & LiveTuneState.INITIALIZED:
            return {
                x: self._rom.get_ram_table_by_address(x)
                for x, y in zip(self.RomAddresses, self.RamAddresses)
                if bool(0xFF000000 & y)
            }
        else:
            return {}

    @property
    def AllocatedSize(self):
        if self.State & LiveTuneState.INITIALIZED:

            table_size = sum(x.NumBytes for x in self.AllocatedTables.values())
            num_tables = len(self.AllocatedTables)

            return (
                8 # offset and number of tables (2 unsigned longs)
                + 8*num_tables # headers (2 unsigned longs per table)
                + table_size # aggregate number of bytes of all allocated tables
            )
        else:
            return None

    @property
    def PendingAllocations(self):

        if not self.State & LiveTuneState.WRITE_PENDING:
            return {}

        current_allocations = set(self.RomAddresses)

        pending_num = struct.unpack('>L', self._bytes[4:8])[0]
        fmt = '>{:d}L'.format(pending_num)
        rom_headers = set(
            struct.unpack(fmt, self._bytes[8:8 + 4*pending_num])
        )

        add = rom_headers - current_allocations
        remove = current_allocations - rom_headers

        pending_addrs = sorted(list(add.union(remove)))

        return {k: self.ROM.get_ram_table_by_address(k) for k in pending_addrs}

    @property
    def PendingActivations(self):
        if not self.State & LiveTuneState.WRITE_PENDING:
            return {}

        current_activations = set([
            k for k, v in zip(self.RomAddresses, self.RamAddresses)
            if bool(0xFF000000 & v)
        ])

        pending_num = struct.unpack('>L', self._bytes[4:8])[0]
        fmt = '>{:d}L'.format(pending_num)
        start = 8 + 4*pending_num
        end = start + 4*pending_num
        rom_headers = struct.unpack(fmt, self._bytes[8:start])
        ram_headers = struct.unpack(fmt, self._bytes[start:end])
        pending_activations = set([
            k for k, v in zip(rom_headers, ram_headers)
            if bool(0xFF000000 & v)
        ])

        add = pending_activations - current_activations
        remove = current_activations - pending_activations
        pending_addrs = sorted(list(add.union(remove)))

        return {k: self.ROM.get_ram_table_by_address(k) for k in pending_addrs}

    @property
    def PendingSize(self):
        if self.State & LiveTuneState.INITIALIZED:
            table_delta = sum([
                1 if x.RamAddress else -1
                for x in self.PendingAllocations.values()
            ])

            header_offs = 8*table_delta

            table_offs = []

            for table in self.PendingAllocations.values():
                table_offs.append(table.NumBytes)

                # for tables being unallocated, subtract their size
                if table.RamAddress is None:
                    table_offs[-1] *= -1

            return self.AllocatedSize + header_offs + sum(table_offs)

        else:
            return 0

    @property
    def State(self):
        state = LiveTuneState.UNINITIALIZED

        if self._ram_bytes is not None:
            state |= LiveTuneState.INITIALIZED

        if self._bytes != self._ram_bytes:
            state |= LiveTuneState.WRITE_PENDING

            # check if the only difference between RAM and PC raw data
            # is table activations, if so, set the finalize write flag
            num = struct.unpack('>L', self._bytes[4:8])[0]
            start = 8 + num*4
            end = start + num*4
            fmt = '>{:d}L'.format(num)
            ram_headers = struct.unpack(fmt, self._ram_bytes[start:end])
            mod_ram_headers = struct.unpack(fmt, self._bytes[start:end])
            mod_activations = [bool(0xFF000000 & x) for x in mod_ram_headers]
            mod_addrs = [0xFFFFFF & x for x in mod_ram_headers]
            ram_activations = [bool(0xFF000000 & x) for x in ram_headers]
            ram_addrs = [0xFFFFFF & x for x in ram_headers]

            if (
                mod_addrs == ram_addrs # tables are the same

                # all other data is the same
                and self._ram_bytes[:start] == self._bytes[:start]
                and self._ram_bytes[end:] == self._bytes[end:]

                and mod_activations != ram_activations # activations differ
            ):
                state |= LiveTuneState.FINALIZE_WRITE

        return state
