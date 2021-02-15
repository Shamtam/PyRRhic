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
        super(MerpModLiveTune, self).__init__(rom, ram_size)

        self._start_addr = start_addr
        self._end_addr = end_addr
        self.initialize()

    def initialize(self):
        self._allocated_tables = []
        self._rom_headers = None
        self._ram_headers = None
        self._pending_allocations = {}
        self._pending_activations = {}

    def init_table_count(self, num_tables):
        self._allocated_tables = [None]*num_tables
        self._rom_headers = [None]*num_tables
        self._ram_headers = [None]*num_tables

    def init_headers(self, rom_headers, ram_headers):
        if (
            len(rom_headers) != len(self._rom_headers) or
            len(ram_headers) != len(self._ram_headers)
        ):
            raise ValueError(
                'Mismatch between expected table count and number of headers'
            )

        tables = {}
        self._rom_headers = rom_headers
        self._ram_headers = ram_headers
        num_tables = len(rom_headers)

        for rom_addr, ram_addr in zip(rom_headers, ram_headers):
            table = self.ROM.get_ram_table_by_address(rom_addr)
            tables_start = self.StartAddress + 8*(1 + num_tables)
            tables_end = self.EndAddress
            table.RamAddress = (
                0x00FFFFFF & ram_addr
                if(
                    (ram_addr | 0xFF000000) in
                    range(tables_start, tables_end)
                )
                else None
            )
            tables[rom_addr] = table

            if table.RamAddress is not None:
                table.activate(bool(ram_addr & 0xFF000000))

        self.init_tables(tables)

    def init_tables(self, tables):
        if len(tables) != self.NumTables:
            raise ValueError(
                'Mismatch between number of tables to initialize and expected '
                'number of allocated tables'
            )

        # sort allocated tables by ROM address and generate expected
        # RAM address for each
        num_tables = len(tables)
        sorted_tables = {k: tables[k] for k in sorted(tables)}
        ram_addrs = [None]*num_tables
        current_addr = self._start_addr + 8*(1 + num_tables)
        for idx, table in enumerate(sorted_tables.values()):

            self._allocated_tables[idx] = table

            num_bytes = table.NumBytes
            ram_addrs[idx] = current_addr & 0x00FFFFFF
            current_addr += num_bytes

        # check/set RAM addresses
        for table, gen_addr in zip(self._allocated_tables, ram_addrs):
            stored_addr = table.RamAddress

            # TODO: handle this case smoothly
            if stored_addr is not None and stored_addr != gen_addr:
                raise ValueError('Indeterminate RAM state, need to reinitialize RAM tuning')
            elif stored_addr is None:
                table.RamAddress = gen_addr

    def process_allocation(self):
        current = set([x.RomAddress for x in self._allocated_tables])
        pending = set(self._pending_allocations)

        add = pending - current
        remove = current.intersection(pending)
        keep_addrs = [
            t.RomAddress for t in self._allocated_tables
            if t.RomAddress in current - remove
        ]
        remove_addrs = [
            t.RomAddress for t in self._allocated_tables
            if t.RomAddress in remove
        ]
        add_addrs = [
            a for a in self._pending_allocations
            if a in add
        ]

        # initialize tables and clear RAM address of tables to remove
        for addr in remove_addrs:
            t = self.ROM.get_ram_table_by_address(addr)
            t.initialize_bytes()
            t.activate(False)
            t.RamAddress = None

        # generate sorted list of tables to be allocated
        table_addrs = sorted(keep_addrs + add_addrs)
        tables = [self.ROM.get_ram_table_by_address(a) for a in table_addrs]

        num_tables = len(tables)
        rom_addrs = [None]*num_tables
        ram_addrs = [None]*num_tables
        out_bytes = bytearray(b'\x00'*self.TotalSize)
        tables_start = self.StartAddress + 8*(1 + num_tables)
        tables_end = self.EndAddress
        current_addr = tables_start

        for idx, t in enumerate(tables):

            # initialize bytes for newly added tables
            if t.RomAddress in add:
                t.initialize_bytes()

            if current_addr not in range(tables_start, tables_end):
                raise ValueError('Allocation size exceeds total RAM capacity!')

            # populate table data in output byte array
            start_idx = current_addr - self.StartAddress
            end_idx = start_idx + t.NumBytes
            out_bytes[start_idx:end_idx] = (
                t.Bytes
            )

            # generate ROM/RAM headers
            rom_addrs[idx] = t.RomAddress
            ram_addrs[idx] = current_addr & 0x00FFFFFF

            # set table RAM address and increment address pointer
            t.RamAddress = current_addr & 0x00FFFFFF
            current_addr += t.NumBytes

            # mark table inactive
            t.activate(False)

        if num_tables > 0:
            offs_bytes = struct.pack('>L', num_tables - 1)
            count_bytes = struct.pack('>L', num_tables)
            header_size = len(rom_addrs + ram_addrs)
            header_bytes = struct.pack(
                '>{:d}L'.format(header_size),
                *(rom_addrs + ram_addrs)
            )

            out_bytes[0:8*(1 + num_tables)] = b''.join(
                [offs_bytes, count_bytes, header_bytes]
            )

        # clear livetune state to force re-initialization from RAM
        # after allocation for verification
        self.initialize()

        ret = {}
        for idx, b in enumerate(out_bytes):
            ret[(self._start_addr & 0xFFFFFF) + idx] = bytes([b])
        return ret

    def process_modification(self):
        tables = [t for t in self._allocated_tables if t.IsModified]

        modified_bytes = {}
        for t in tables:
            orig_data = t.OriginalBytes
            data = t.Bytes
            offsets = range(t.NumBytes)
            modified_bytes.update(
                {
                    (0xFFFFFF & t.RamAddress) + offset: bytes([data[offset]])
                    for offset in offsets
                    if data[offset] != orig_data[offset]
                }
            )

        return modified_bytes if modified_bytes else None

    def process_activation(self):
        num_tables = len(self._allocated_tables)
        out_bytes = {}

        for table in self._pending_activations.values():
            table.activate(not table.Active)

        for idx, t in enumerate(self._allocated_tables):
            mask = 0xFFFFFFFF if t.Active else 0x00FFFFFF
            ram_addr = (t.RamAddress | 0xFF000000) & mask
            t.RamAddress = ram_addr

            start_addr = 0xFFFFFF & (self._start_addr + 8 + 4*num_tables + 4*idx)
            for b_idx, b in enumerate(struct.pack('>L', ram_addr)):
                out_bytes[start_addr + b_idx] = bytes([b])

        # clear livetune RAM headers to force re-initialization from RAM
        # after activation for verification
        self._ram_headers = None
        return out_bytes

    def stage_allocation(self, table):

        can_allocate = self.PendingSize + table.NumBytes <= self.TotalSize
        pending = table.RomAddress in self._pending_allocations
        allocated = table.RamAddress is not None

        # veto (un)allocation of active/pending active tables
        if table.Active or table.RomAddress in self._pending_activations:
            return

        if not pending:
            if (not allocated and can_allocate) or allocated:
                self._pending_allocations[table.RomAddress] = table
        else:
            del self._pending_allocations[table.RomAddress]


    def stage_activation(self, table):

        allocated = table.RamAddress
        pending = table.RomAddress in self._pending_activations

        # veto activation of unallocated tables
        if not allocated:
            return

        if not pending:
            self._pending_activations[table.RomAddress] = table
        else:
            del self._pending_activations[table.RomAddress]

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
        if all([x is not None for x in self._allocated_tables]):
            return [x.RomAddress for x in self._allocated_tables]
        else:
            return None

    @property
    def RamAddresses(self):
        if all([x is not None for x in self._allocated_tables]):
            return [x.RamAddress for x in self._allocated_tables]
        else:
            return None

    @property
    def NumTables(self):
        return (
            len(self._allocated_tables)
            if self._allocated_tables is not None
            else 0
        )

    @property
    def AllocatedSize(self):
        table_size = super(MerpModLiveTune, self).AllocatedSize
        num_tables = len(self.Tables)

        return (
            8 # offset and number of tables (2 unsigned longs)
            + 8*num_tables # headers (2 unsigned longs per table)
            + table_size # aggregate number of bytes of all allocated tables
        )

    @property
    def PendingAllocations(self):
        return self._pending_allocations

    @property
    def PendingActivations(self):
        return self._pending_activations

    @property
    def PendingSize(self):

        table_delta = sum([
            -1 if x.RamAddress else 1
            for x in self._pending_allocations.values()
        ])

        header_offs = 8*table_delta

        table_offs = []
        for table in self._pending_allocations.values():
            table_offs.append(table.NumBytes)
            if table.RamAddress is not None:
                table_offs[-1] *= -1

        return self.AllocatedSize + header_offs + sum(table_offs)

    @property
    def State(self):
        state = LiveTuneState.UNINITIALIZED

        # table count has been determined
        if all([x is not None for x in (self._rom_headers, self._ram_headers)]):
            state |= LiveTuneState.COUNT

        # headers have been determined
        if (
            all([x is not None for x in (self._rom_headers, self._ram_headers)])
            and
            all([x is not None for x in self._rom_headers]) and
            all([x is not None for x in self._ram_headers]) and
            (
                all([x is not None for x in self._allocated_tables]) or
                all([x.RamAddress is not None for x in self._allocated_tables if x is not None])
            )
        ):
            state |= LiveTuneState.HEADERS

        # tables are all up-to-date
        if (
            self._rom_headers and self._ram_headers and
            all([x is not None for x in self._allocated_tables]) and
            all([x.RamAddress is not None for x in self._allocated_tables]) and
            all([not x.IsModified for x in self._allocated_tables if x is not None])
        ):
            state |= LiveTuneState.TABLES

        # table allocation pending
        if self._pending_allocations:
            state |= LiveTuneState.PEND_ALLOCATE

        # table activation pending
        if self._pending_activations:
            state |= LiveTuneState.PEND_ACTIVATE

        return state
