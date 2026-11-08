"""Each goods market's memory after a year's rounds, worked out over the year's table of markets (`goods_year_markets.py`) in kernels
(`goods_remember_kernel.py`), then written to the memory in one call (`goods_memory_notes.write_markets`).

A market on the tables whose good is not the coin metal's takes the kernels: the price its sellers got from the ledger's rounds, what its
buyers would have taken at the old price from the order tables' bid rows and the added bids, and the quote it rests on from the first round's
columns. A market cleared on `Bid` and `Offer` objects, a market of the coin metal (whose mint tops up the price) and every market when a
kernel meets a figure it does not reproduce take the Python rules (`remember_one`)."""
import numpy

from . import goods_memory_notes, goods_remember_kernel as kernel
from .goods_good_clear import ON_OBJECTS, QUOTE_KINDS
from .market_memory_asks import REPRESENTATIVE_TRADE_SHARE, memory_reference_volume
from .market_memory_asks import RESUMED_TRADE_MEMORY_SHARE
from .market_memory_offers import NO_OFFER_MEMORY_SHARE, price_after_thin_trade, price_toward_quote
from .notional import making_costs
from .setup import opening_price_today
from .types import EDGE_EXTERNAL
from .year_ledger_tables import ROUNDS


class Costs:
    """What each good costs to make, worked out the first time it is read."""

    def __init__(self, setup, record):
        self._setup, self._record, self._found = setup, record, None

    def get(self, good):
        if self._found is None:
            self._found = making_costs(self._setup, self._record)
        return self._found.get(good)


def remember_one(setup, record, good, area, market, old, total, usual, was_quote, idle_years, ledger, orders, costs: Costs):
    """The Python rules for one market: (the signal or None, the quote kind or None, whether it came from trade)."""
    from . import year_goods
    quote_kind = None
    received = year_goods._received_price(setup, record, good, market, ledger) if total > 0.0 else None
    if received is not None:
        reference = memory_reference_volume(usual, year_goods._wanted_at(market, old, orders))
        signal = year_goods.price_after_trade(old, was_quote, received, total, reference, idle_years)
        if total < REPRESENTATIVE_TRADE_SHARE * usual:
            signal = price_after_thin_trade(signal, costs.get(good), total, usual)
        return signal, None, True
    quote = market.result.quote
    if market.bids and not market.offers:
        from .goods_market_rows import bids_only_quote
        from . import market_quote
        quote = (bids_only_quote(orders.bid_lists(), market.rows.bid_rows, costs.get(good)) if market.rows is not None else
                 market_quote.no_trade_quote(market.bids, market.offers, costs.get(good)))
    signal = price_toward_quote(old, quote.price) if quote is not None else None
    if signal is not None:
        quote_kind = quote.kind
    return signal, quote_kind, False


def _bid_columns(year_markets, cells, orders):
    """The first-round bids of the markets at `cells` as columns, market by market: (pointers, floor, flexible, reference, elasticity, budget,
    maximum, whether the buyer counts: it is not the foreign partner)."""
    table = year_markets.table
    counts = table.bid_count[cells]
    pointers = numpy.concatenate(([0], numpy.cumsum(counts))).astype(numpy.int64)
    taken = year_markets.bid_rows()[numpy.repeat(table.bid_first[cells] - pointers[:-1], counts) + numpy.arange(int(pointers[-1]), dtype=numpy.int64)]
    bids = orders.tables()[0]
    external = orders.book.agent_ids.numbers.get(EDGE_EXTERNAL)
    counted = numpy.ones(len(taken), dtype=numpy.bool_) if external is None else bids.buyer[taken] != external
    return (pointers, bids.floor_quantity[taken], bids.flexible_quantity[taken], bids.reference_price[taken], bids.elasticity[taken],
            bids.budget[taken], bids.maximum_price[taken], counted)


def _kind_numbers(memory, kind: numpy.ndarray) -> numpy.ndarray:
    """The memory's number of each market's quote kind (`NO_KIND` for none); a kind is numbered when first used, in market order."""
    numbers = numpy.full(len(kind), goods_memory_notes.NO_KIND, dtype=numpy.int64)
    used, first = numpy.unique(kind[kind != 0], return_index=True)
    for code in used[numpy.argsort(first)].tolist():
        numbers[kind == code] = memory.tables.kind_number(QUOTE_KINDS[code])
    return numbers


def remember_markets(setup, record, ordered, rows, year_markets, cells, ledger, orders, metal):
    """The memory's notes for the markets `ordered` (sorted (good, area), market) pairs, with their market numbers `rows` and table rows `cells`."""
    memory, table = record.memory, year_markets.table
    total_all, cleared_all = ledger.market_total_columns()
    total, cleared = total_all[rows], cleared_all[rows]
    was_quote, usual = goods_memory_notes.last_year_columns(memory, rows)
    was_quote, usual = numpy.array(was_quote, dtype=numpy.bool_), numpy.array(usual, dtype=numpy.float64)
    old, idle, way = table.last_price[cells], table.idle_years[cells], table.way[cells]
    goods = [key[0] for key, _market in ordered]
    plain = (way == ON_OBJECTS) | (numpy.array([good == metal for good in goods], dtype=numpy.bool_) if metal is not None else False)
    costs = Costs(setup, record)
    flags = numpy.zeros(1, dtype=numpy.int64)
    pointers, floor, flexible, reference, elasticity, budget, maximum, counted = _bid_columns(year_markets, cells, orders)
    ledger.tables.flush(ROUNDS)
    rounds = ledger.tables.rounds
    received = kernel.received_prices(rounds.market, rounds.quantity, rounds.price, int(rounds.row_count[0]),
                                      len(memory.tables.goods_markets))[rows]
    added = year_markets.added_bids(cells)
    wanted_old = kernel.wanted_at_markets(old, pointers, floor, flexible, reference, elasticity, budget, maximum, counted, *added, flags)
    funded, best = kernel.bid_figures(pointers, budget, maximum)
    has_bids, offers_left = table.bid_count[cells] > 0, table.left_count[cells]
    traded = (total > 0.0) & ~numpy.isnan(received)
    needs_cost = (traded & (total < REPRESENTATIVE_TRADE_SHARE * usual)) | (~traded & has_bids & (offers_left == 0))
    cost = numpy.array([numpy.nan if each is None else each for each in (costs.get(good) for good in goods)]) if needs_cost.any() \
        else numpy.full(len(rows), numpy.nan)
    signal, kind, from_trade = kernel.signals(old, was_quote, usual, idle, total, received, wanted_old, table.quote_price[cells],
                                              table.quote_kind[cells], has_bids, offers_left, cost, funded, best, REPRESENTATIVE_TRADE_SHARE,
                                              RESUMED_TRADE_MEMORY_SHARE, NO_OFFER_MEMORY_SHARE)
    if flags[0] != kernel.FALLBACK and not plain.any():
        return _write(setup, memory, rows, goods, signal, kind, from_trade, cleared, table.delivered[cells])
    every = numpy.ones(len(rows), dtype=numpy.bool_) if flags[0] == kernel.FALLBACK else plain
    for place in numpy.flatnonzero(every).tolist():
        (good, area), market = ordered[place]
        found, name, trade = remember_one(setup, record, good, area, market, None if old[place] != old[place] else float(old[place]),
                                          float(total[place]), float(usual[place]), bool(was_quote[place]), int(idle[place]), ledger, orders, costs)
        signal[place], kind[place], from_trade[place] = numpy.nan if found is None else found, QUOTE_KINDS.index(name), trade
    return _write(setup, memory, rows, goods, signal, kind, from_trade, cleared, table.delivered[cells])


def _write(setup, memory, rows, goods, signal, kind, from_trade, cleared, delivered) -> None:
    """The year's notes into the memory: the signals, the quote kinds numbered, the cleared prices, the deliveries and each good's opening price."""
    opening_of_good = {}
    for good in goods:
        if good not in opening_of_good:
            opening_of_good[good] = opening_price_today(setup, memory, good)
    openings = numpy.array([numpy.nan if opening_of_good[good] is None else opening_of_good[good] for good in goods], dtype=numpy.float64)
    goods_memory_notes.write_markets(memory, rows, signal, _kind_numbers(memory, kind), from_trade, cleared, delivered, openings)
