"""Finding a table row from a packed integer key: an open-addressing hash index a kernel can search and add to.

Why a hash and not a sorted key array (measured with `tools/measure/book_index.py`): a sorted array answers a lookup by
binary search, slower than a hash, and cannot take a new key without moving the rest, while the book adds stock slots inside
its posting kernel. A hash answers in one or two probes and a kernel can add to it, as long as Python has reserved room first
(`KeyedRows.reserve`). An agent's own slots (its holdings) are not found through the hash but through a chain kept in the
Stocks table (`next_in_agent`), which also keeps them in the order they were made.

An index is an int64 array whose length is a power of two, at least twice the table's capacity, holding row numbers (`EMPTY`
where nothing is). The key of row r is `keys[r]`. Probing is linear. Nothing is ever removed from an index: a table that
drops keys rebuilds (`KeyedRows.rebuild`). A key is a non-negative whole number below 2**63 built by `pack_key`."""
import numpy

from sim.compiled_tables.growth import reserve_rows
from sim.jit import njit

EMPTY = -1                     # an index entry with no row; also what a lookup answers for an absent key
HASH_MULTIPLIER = 2685821657736338717
HASH_MASK = 0x7FFFFFFFFFFFFFFF
FIRST_FIELD_BITS = 22          # agents: up to about four million
SECOND_FIELD_BITS = 20         # goods: up to about a million
THIRD_FIELD_BITS = 21          # tiles (or a purpose reference): up to about two million
SECOND_SHIFT = THIRD_FIELD_BITS
FIRST_SHIFT = SECOND_FIELD_BITS + THIRD_FIELD_BITS


@njit
def pack_key(first, second, third=0):
    """One non-negative whole number from three ids, each within its field (the caller checks the bounds on admission)."""
    return (first << FIRST_SHIFT) | (second << SECOND_SHIFT) | third


@njit
def unpack_key(key):
    """(first, second, third) of a packed key."""
    return (key >> FIRST_SHIFT, (key >> SECOND_SHIFT) & ((1 << SECOND_FIELD_BITS) - 1),
            key & ((1 << THIRD_FIELD_BITS) - 1))


@njit
def start_position(key, index_length):
    """Where probing for the key begins (the length is a power of two). Every bit of the key reaches the low bits that pick the
    place: a product's low bits depend only on the key's low bits, so the high fields (the agent) are folded down between two
    multiplications, or keys that differ only in them would all start at one place."""
    mixed = (int(key) * HASH_MULTIPLIER) & HASH_MASK
    mixed ^= mixed >> 31
    mixed = (mixed * HASH_MULTIPLIER) & HASH_MASK
    mixed ^= mixed >> 29
    return mixed & (index_length - 1)


@njit
def index_find(keys, index, key):
    """The row holding the key, or EMPTY when it is absent."""
    position = start_position(key, len(index))
    mask = len(index) - 1
    while True:
        row = index[position]
        if row == EMPTY:
            return EMPTY
        if keys[row] == key:
            return row
        position = (position + 1) & mask


@njit
def index_add(keys, index, row):
    """Point the index at a row whose key is already written (the key must not be in the index yet)."""
    mask = len(index) - 1
    position = start_position(keys[row], len(index))
    while index[position] != EMPTY:
        position = (position + 1) & mask
    index[position] = row


@njit
def index_build(keys, live, row_count, index):
    """Fill an emptied index with every row below row_count whose live entry is not zero, in row order."""
    for row in range(row_count):
        if live[row] != 0:
            index_add(keys, index, row)


def index_size_for(capacity: int) -> int:
    """The smallest power of two at least twice the capacity."""
    size = 16
    while size < 2 * capacity:
        size *= 2
    return size


class KeyedRows:
    """A table with a `key` column (and a `live` column: 1 for a row in use) and the hash index over it.

    The table is replaced by a bigger one when `reserve` needs room, so callers read `.table` afresh for each kernel call."""

    def __init__(self, spec, table_type, capacity: int = 64):
        self.spec = spec
        self.table_type = table_type
        self.table = spec.new_table(table_type, capacity)
        self.index = numpy.full(index_size_for(capacity), EMPTY, dtype=numpy.int64)

    def reserve(self, extra: int) -> None:
        """Room for `extra` more rows and keys; a kernel adds that many without growing anything."""
        grown = reserve_rows(self.table, extra)
        if grown is not self.table:
            self.table = grown
            self.rebuild()

    def rebuild(self) -> None:
        """Make the index again from the live rows (after a row stops being live, or the table grew)."""
        self.index = numpy.full(index_size_for(int(self.table.capacity[0])), EMPTY, dtype=numpy.int64)
        index_build(self.table.key, self.table.live, int(self.table.row_count[0]), self.index)

    def clear(self) -> None:
        """Drop every row (the table keeps its room)."""
        self.table.row_count[0] = 0
        self.index[:] = EMPTY

    def find(self, key: int) -> int:
        """The row for the key, or EMPTY."""
        return int(index_find(self.table.key, self.index, key))

    @property
    def rows(self) -> int:
        return int(self.table.row_count[0])
