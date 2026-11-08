"""The book's stocks read as one block: many (agent, good, tile) cells in one kernel call, the year loop's replacement for a loop of
`book.stock(agent, good, tile)` (one name lookup, one index probe and one Python call per cell).

`numbers_of` turns names into the book's ids (-1 for a name the book never admitted: it reads as nothing held, as `Book.stock`
does); `stock_block` reads the cells. A caller that reads the same names every year keeps the ids until the book admits more
(`book.agent_ids`, `book.tile_ids` and `book.good_ids` only grow within a game, so a number never changes)."""
from typing import Sequence

import numpy

from sim.book_index import EMPTY, index_find, pack_key
from sim.jit import njit


def numbers_of(ids, names: Sequence[str]) -> numpy.ndarray:
    """The ids of the names in an `IdTable`, -1 where a name is not admitted."""
    found = ids.numbers.get
    return numpy.fromiter((-1 if (number := found(name)) is None else number for name in names), numpy.int64, len(names))


@njit
def read_stocks_by_cell(stocks, stock_index, agent_numbers, good_numbers, tile_numbers):
    """The quantity held at each cell (agent number, good number, tile number); a cell with a number below zero, or one the book
    never held, reads 0.0. Reads the book's tables, writes nothing."""
    found = numpy.zeros(len(agent_numbers))
    for cell in range(len(agent_numbers)):
        if agent_numbers[cell] >= 0 and good_numbers[cell] >= 0 and tile_numbers[cell] >= 0:
            slot = index_find(stocks.key, stock_index, pack_key(agent_numbers[cell], good_numbers[cell], tile_numbers[cell]))
            if slot != EMPTY:
                found[cell] = stocks.quantity[slot]
    return found


def stock_block(book, agent_numbers, good_numbers, tile_numbers) -> numpy.ndarray:
    """The stock at each cell given as three equally long id arrays (see `numbers_of`), 0.0 where nothing is held."""
    return read_stocks_by_cell(book.stock_rows.table, book.stock_rows.index, numpy.asarray(agent_numbers, dtype=numpy.int64),
                               numpy.asarray(good_numbers, dtype=numpy.int64), numpy.asarray(tile_numbers, dtype=numpy.int64))
