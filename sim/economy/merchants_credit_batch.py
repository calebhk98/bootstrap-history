"""Every merchant's credit request in one pass (`merchants_credit.credit_request` for all of them): the rows of the merchants that may
borrow are searched together, what each holds by market slot comes from the book and the merchant table, and one kernel sizes the loans."""
from typing import List

import numpy

from . import credit, merchant_year, merchant_year_kernels, merchants, merchants_batch, merchants_book, merchants_credit_kernel
from .merchant_table import MerchantTable
from .merchants_shares import MERCHANT_GROUP_SHARE, MERCHANT_SOURCE_SHARE
from .merchants_credit import MERCHANT_LEVERAGE_LIMIT, MERCHANT_LOAN_YEARS
from .types import LoanRequest

SLOT_PAIRS = merchant_year.PairRows(retry_unnumbered=False)
TRANSIT_SLOT_PAIRS = merchant_year.PairRows(retry_unnumbered=False)


def slot_resolver(book):
    """`PairRows` resolver: the route book's slot of the market area holding the tile (-1: not a market of the book)."""
    def resolve(good, tile):
        if good not in book.index_of:
            return -1
        try:
            return book.slot_of.get((good, book.area_map.area_of(good, tile)), -1)
        except KeyError:        # a tile outside every area
            return -1
    return resolve


def held_by_slot(store: MerchantTable, rows: numpy.ndarray, numbers: numpy.ndarray, book, record_book) -> numpy.ndarray:
    """What each merchant at `rows` holds, and has on the road, in each slot of the route book: [merchant position, slot]. Added in the order
    a merchant's stock is listed (goods then tiles by name, then its shipments in turn)."""
    first = numpy.where(numbers >= 0, record_book.agent_table.first_slot[numpy.where(numbers >= 0, numbers, 0)], -1)
    table = record_book.stock_rows.table
    owner, good, tile, quantity = merchant_year_kernels.merchant_stock(first, table.next_in_agent, table.good, table.tile, table.quantity)
    good_names, tile_names = record_book.good_ids.name_list, record_book.tile_ids.name_list
    good_rank = numpy.argsort(numpy.argsort(numpy.array(good_names))) if len(good_names) else numpy.zeros(0, numpy.int64)
    tile_rank = numpy.argsort(numpy.argsort(numpy.array(tile_names))) if len(tile_names) else numpy.zeros(0, numpy.int64)
    order = numpy.lexsort((tile_rank[tile], good_rank[good], owner)) if len(owner) else numpy.zeros(0, numpy.int64)
    slot = SLOT_PAIRS.lookup(good[order], tile[order], good_names, tile_names, (book,), slot_resolver(book))
    held = numpy.zeros((len(rows), book.slots))
    merchants_credit_kernel.accumulate_by_slot(owner[order], slot, quantity[order], held)
    count = store.transit_count
    position_of_row = numpy.zeros(len(store), numpy.int64)
    position_of_row[rows] = numpy.arange(len(rows))
    shipped = numpy.argsort(store.transit_owner[:count], kind="stable")
    transit_slot = TRANSIT_SLOT_PAIRS.lookup(store.transit_good[:count][shipped], store.transit_tile[:count][shipped],
                                             store.goods.name_list, store.tiles.name_list, (book,), slot_resolver(book))
    merchants_credit_kernel.accumulate_by_slot(position_of_row[store.transit_owner[:count][shipped]], transit_slot,
                                               store.transit_quantity[:count][shipped], held)
    return held


def credit_requests(store: MerchantTable, route, record_book, debts, currency, interest_rate: float) -> List[LoanRequest]:
    """The loan each merchant asks for (none for one that wants nothing), in merchant order; `debts` is what each owes now."""
    rows = store.rank_order()
    if len(rows) == 0:
        return []
    debt = numpy.array([debts.get(store.agents[row], 0.0) for row in rows.tolist()])
    limit = MERCHANT_LEVERAGE_LIMIT * (store.capital_base[rows] - debt) - debt
    asking = numpy.flatnonzero(limit > 0.0)
    if len(asking) == 0:
        return []
    book = route.book
    asked_rows = rows[asking]
    market_rows = book.market_rows(store.tables)
    expected = store.gather("prices", asked_rows, market_rows)
    volumes = store.gather("volumes", asked_rows, market_rows)
    numbers = merchant_year.book_numbers(store, record_book, asked_rows)
    held = held_by_slot(store, asked_rows, numbers, book, record_book)
    counts, _good, _source, _destination, source_slot, destination_slot, rank, _price, outlay, _ceiling = merchants_batch.search_arrays(
        route, expected, [store.homes[row] for row in asked_rows.tolist()], float(interest_rate), merchants.MERCHANT_MARGIN_SHARE)
    offsets = numpy.concatenate(([0], numpy.cumsum(counts))).astype(numpy.int64)
    wanted, gain = merchants_credit_kernel.commit_credit_all(
        offsets, destination_slot, source_slot, rank, outlay, merchant_year.purses(record_book, numbers, currency), limit[asking], volumes, held,
        merchants.MERCHANT_MARKET_SHARE, MERCHANT_GROUP_SHARE, MERCHANT_SOURCE_SHARE)
    return [LoanRequest(store.agents[asked_rows[place]], currency, float(wanted[place]),
                        interest_rate + credit.earnable_rate(float(gain[place]), float(wanted[place])), MERCHANT_LOAN_YEARS,
                        float(wanted[place]), "trade") for place in numpy.flatnonzero(wanted > 0.0).tolist()]
