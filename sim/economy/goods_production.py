"""The producers' turn in a good's clearing, over the book's tables: stocks, purses and costs read in blocks, the production moves posted
as one `GoodsMovePostings` batch.

`produce` makes what every planned producer of the turn can make (`producers.production_lines`, the Leontief rule) and books all
the moves together, the producers not touching one another's holdings; `read_stocks` and `turn_figures` give the cells the offers
are priced from as arrays. A name the book has not numbered reads as nothing held; when a move names one the book has not met
(a good or a tile first held now), the moves are posted through `Book.move_many`, which numbers it."""
from typing import Dict, List, Sequence

import numpy

from sim.book_index import index_find, pack_key
from sim.book_post import table_from
from sim.book_tables import GOODS_MOVE_POSTINGS, TRANSFER_POSTINGS, GoodsMovePostings, TransferPostings
from sim.compiled_tables.causes import OK
from sim.jit import njit

from . import producers
from .types import GoodsMove


@njit
def stocks_of_cells(stock_keys, stock_quantity, stock_index, agents, goods, tiles):
    """The quantity held in each (agent, good, tile) cell (zero where nothing was ever held; a number below zero is a name the book
    has not met)."""
    found = numpy.zeros(len(agents))
    for place in range(len(agents)):
        if agents[place] >= 0 and goods[place] >= 0 and tiles[place] >= 0:
            slot = index_find(stock_keys, stock_index, pack_key(agents[place], goods[place], tiles[place]))
            if slot >= 0:
                found[place] = stock_quantity[slot]
    return found


def read_stocks(book, cells: Sequence[tuple]) -> List[float]:
    """The stock of each (agent, good, tile) cell given by name, in order: `Book.stock` of each, as one array read."""
    if not cells:
        return []
    agents, goods, tiles = book.agent_ids.numbers.get, book.good_ids.numbers.get, book.tile_ids.numbers.get
    table = book.stock_rows.table
    return stocks_of_cells(table.key, table.quantity, book.stock_rows.index,
                           numpy.array([-1 if (found := agents(cell[0])) is None else found for cell in cells], dtype=numpy.int64),
                           numpy.array([-1 if (found := goods(cell[1])) is None else found for cell in cells], dtype=numpy.int64),
                           numpy.array([-1 if (found := tiles(cell[2])) is None else found for cell in cells], dtype=numpy.int64)).tolist()


def produce(setup, record, producer_ids: Sequence[str], plans: dict, ledger) -> List[str]:
    """The producers of the turn with planned runs make their output: moves worked out from the stocks they hold and the hours they
    hired, booked as one batch, their output noted in the ledger. Returns the ids of those that made something runnable."""
    book = record.book
    planned = []
    for producer_id in producer_ids:
        plan = plans.get(producer_id)
        if plan is not None and plan.runs > 0.0:
            producer = record.producers[producer_id]
            planned.append((producer_id, producer, setup.recipes[producer.recipe_id], plan.runs))
    cells = [(producer_id, good, producer.tile) for producer_id, producer, recipe, _runs in planned for good in recipe.inputs]
    stocks = iter(read_stocks(book, cells))
    lines = []
    for producer_id, producer, recipe, runs in planned:
        held = {good: next(stocks) for good in recipe.inputs}
        _runs, made = producers.production_lines(producer, recipe, held, ledger.hours_hired.get(producer_id, {}), runs)
        lines.extend(made)
    note_output(ledger, book, lines)
    post_lines(book, lines)
    return [each[0] for each in planned]


def note_output(ledger, book, lines: Sequence[tuple]) -> None:
    """The goods the lines make, added to the ledger's output of the producer that receives them (`YearLedger.note_output`)."""
    made = [line for line in lines if line[0] != line[1] and line[5] == "output"]
    if not made:
        return
    tables = ledger.tables
    ledger.add_pair_amounts("output", tables.agent_numbers([line[1] for line in made]), tables.good_numbers([line[2] for line in made]),
                            numpy.array([line[4] for line in made], dtype=float))


def post_lines(book, lines: Sequence[tuple]) -> None:
    """Book the moves, all or none, as one batch of posting rows when the book has numbered every name in them."""
    if not lines:
        return
    agents, goods, tiles = book.agent_ids.numbers, book.good_ids.numbers, book.tile_ids.numbers
    givers = [agents.get(line[0]) for line in lines]
    receivers = [agents.get(line[1]) for line in lines]
    good_numbers = [goods.get(line[2]) for line in lines]
    tile_numbers = [tiles.get(line[3]) for line in lines]
    if None in givers or None in receivers or None in good_numbers or None in tile_numbers:
        book.move_many([GoodsMove(*line) for line in lines])
        return
    codes = {purpose: book.purposes.encode(purpose) for purpose in {line[5] for line in lines}}
    count = len(lines)
    moves = table_from(GOODS_MOVE_POSTINGS, GoodsMovePostings, count, givers, receivers, good_numbers, tile_numbers, tile_numbers,
                       [line[4] for line in lines], [codes[line[5]][0] for line in lines], [codes[line[5]][1] for line in lines],
                       numpy.zeros(count, dtype=numpy.int64))
    outcomes, _scratch = book.apply_postings(table_from(TRANSFER_POSTINGS, TransferPostings, 0, *[[] for _column in TRANSFER_POSTINGS.columns]),
                                             moves, 1)
    if int(outcomes.code[0]) != OK:
        book.move_many([GoodsMove(*line) for line in lines])          # the book's own refusal


def turn_figures(setup, record, ledger, producer_ids: Sequence[str]) -> tuple:
    """Per producer of the turn, in order: (stock of each output on its tile by good, its money, the money it paid out other than for
    plant), each read for all of them at once."""
    book = record.book
    members = [(producer_id, record.producers[producer_id]) for producer_id in producer_ids]
    cells = [(producer_id, good, producer.tile) for producer_id, producer in members
             for good in setup.recipes[producer.recipe_id].outputs]
    stocks = iter(read_stocks(book, cells))
    held: List[Dict[str, float]] = [{good: next(stocks) for good in setup.recipes[producer.recipe_id].outputs}
                                    for _producer_id, producer in members]
    cash = book.balances_of(list(producer_ids), setup.currency_id).tolist()
    running = ledger.running_costs_of(list(producer_ids)).tolist()
    return held, cash, running
