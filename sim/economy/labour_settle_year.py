"""A year's labour markets settled from the fill columns: pairs, book postings and ledger notes in a few calls, no object per market.

What `settlement.settle_labour`, `YearLedger.note_settlement` and `note_labour_settled` did market by market is done for all of
them: the greedy pairs of every market (`labour_walk_kernel`), each market settled and applied on the book on the balances the
earlier ones left (`labour_wage_kernel`), and the ledger fed whole arrays (`YearLedger.note_settlement_rows`, `note_hours_rows`).
The employers' ids are the labour core's own; they are mapped to the book's agent numbers once a year (`numbers_of_refs`), because the
core numbers an employer when it first bids and the book when it first holds or owes.
"""
from typing import List

import numpy

from sim.book_post import settled_scratch

from .labour_fills import LabourFills
from .labour_idle_hours import market_keys
from .labour_walk_kernel import fill_slots, market_agents, walk_pairs
from .labour_wage_kernel import settle_wage_markets
from .year_ledger_tables import WAGES_PURPOSE


def pair_markets(fills: LabourFills) -> dict:
    """The pairs of every market and the agents each settlement lists: a dict of arrays, `pair_start`, `pair_quantity`,
    `agent_start`, `agent_ref`, `pair_buyer_agent`, `pair_seller_agent` (see `labour_walk_kernel`). A fill of zero hours is
    not paired."""
    buys, sells = fills.buy_hours > 0.0, fills.sell_hours > 0.0
    buy_position, sell_position = numpy.flatnonzero(buys), numpy.flatnonzero(sells)
    buy_start = numpy.searchsorted(buy_position, fills.buy_start).astype(numpy.int64)
    sell_start = numpy.searchsorted(sell_position, fills.sell_start).astype(numpy.int64)
    buy_ref, sell_ref = fills.buy_ref[buy_position], fills.sell_ref[sell_position]
    pair_start, pair_buy, pair_sell, pair_quantity = walk_pairs(buy_start, fills.buy_hours[buy_position], sell_start,
                                                                fills.sell_hours[sell_position])
    agent_start, agent_ref, buyer_agent, seller_agent = market_agents(pair_start, pair_buy, pair_sell, buy_start, buy_ref, sell_start,
                                                                      sell_ref, len(fills.names))
    return {"pair_start": pair_start, "pair_quantity": pair_quantity, "agent_start": agent_start, "agent_ref": agent_ref,
            "pair_buyer_agent": buyer_agent, "pair_seller_agent": seller_agent}


def numbers_of_refs(numbering, names: List[str], agent_ref: numpy.ndarray) -> numpy.ndarray:
    """The agent number of every ref, from `numbering(names)` (a list of names to their numbers, admitting new ones in the order
    given). Names not numbered yet are admitted in the order the markets' settlements first list them, then the rest by name."""
    count = len(names)
    _unique, first = numpy.unique(agent_ref, return_index=True)
    listed = agent_ref[numpy.sort(first)]
    unlisted = numpy.setdiff1d(numpy.arange(count, dtype=numpy.int64), listed)
    order = numpy.concatenate((listed, unlisted))
    found = numpy.zeros(count, dtype=numpy.int64)
    found[order] = numbering([names[ref] for ref in order.tolist()])
    return found


def interleave(first_start, first_values, second_start, second_values) -> numpy.ndarray:
    """Each market's rows of `first_values` then its rows of `second_values`, market after market."""
    first_count, second_count = numpy.diff(first_start), numpy.diff(second_start)
    before = numpy.cumsum(first_count + second_count) - first_count - second_count
    merged = numpy.empty(len(first_values) + len(second_values), dtype=first_values.dtype)
    merged[numpy.arange(len(first_values)) - numpy.repeat(first_start[:-1], first_count) + numpy.repeat(before, first_count)] = first_values
    merged[numpy.arange(len(second_values)) - numpy.repeat(second_start[:-1], second_count)
           + numpy.repeat(before + first_count, second_count)] = second_values
    return merged


def settle_year(book, ledger, fills: LabourFills, currency: str) -> None:
    """Settle every market of the year on the book and note it in the ledger, markets in the order of `fills`."""
    markets = fills.markets
    market_count = len(markets.wage)
    if not market_count:
        return
    pairs = pair_markets(fills)
    tables = ledger.tables
    ledger_of_ref = numbers_of_refs(tables.agent_numbers, fills.names, pairs["agent_ref"])
    book_of_ref = ledger_of_ref if tables.book is book else numbers_of_refs(      # a ledger made bare (a test) has a book of its own
        lambda names: numpy.array([book.agent_number(name) for name in names], dtype=numpy.int64), fills.names, pairs["agent_ref"])
    agent_start, pair_start = pairs["agent_start"], pairs["pair_start"]
    agent_book = book_of_ref[pairs["agent_ref"]]
    agent_market = numpy.repeat(numpy.arange(market_count, dtype=numpy.int64), numpy.diff(agent_start))
    paid = received = imports = exports = numpy.zeros(0)
    if len(agent_book):
        currency_number = book.currency_number(currency)
        trades = dict.fromkeys(markets.trade[row] for row in numpy.flatnonzero(numpy.diff(pair_start) > 0).tolist())
        good = [book.good_number(trade) for trade in trades][0]
        book.tile_number("")      # a wage is paid between agents with no tile; the book numbers the empty tile the first time
        scratch = settled_scratch(int(numpy.diff(agent_start).max()), 0)
        paid, received, imports, exports, failed, cause, culprit = settle_wage_markets(
            book.tables(), scratch, currency_number, good, agent_start, agent_book, pair_start, pairs["pair_buyer_agent"],
            pairs["pair_seller_agent"], pairs["pair_quantity"], markets.wage)
        if failed >= 0:
            _refuse(book, fills, currency, failed, agent_start, agent_ref=pairs["agent_ref"], paid=paid, received=received)
        _note_settlements(ledger, markets, ledger_of_ref[pairs["agent_ref"]], agent_market, paid, received, imports, exports)
    _note_hours(ledger, fills, ledger_of_ref, agent_market, pairs["agent_ref"], paid, received)


def _refuse(book, fills, currency, market, agent_start, agent_ref, paid, received) -> None:
    """The error the book raises for a market it refused: asking it to post the same sums raises it."""
    first, last = int(agent_start[market]), int(agent_start[market + 1])
    trade = fills.markets.trade[market]
    book.post_settled(currency, "wages for %s" % trade, trade, [fills.names[ref] for ref in agent_ref[first:last].tolist()],
                      paid[first:last].tolist(), received[first:last].tolist(), [], [], [])
    raise RuntimeError("the book refused the wages of %s and then took them" % trade)


def _note_settlements(ledger, markets, agent_book, agent_market, paid, received, imports, exports) -> None:
    """The ledger's rows for every agent of every settlement (`YearLedger.note_settlement` of each market)."""
    count = len(agent_book)
    template = numpy.zeros(count, dtype=numpy.int64)
    reference = numpy.zeros(count, dtype=numpy.int64)
    if imports.any() or exports.any():
        for market in numpy.unique(agent_market[(imports != 0.0) | (exports != 0.0)]).tolist():
            here = agent_market == market
            template[here], reference[here] = ledger.tables.purpose_code("wages for %s" % markets.trade[market])
    ledger.note_settlement_rows(agent_book, paid, received, imports, exports, numpy.zeros(count, dtype=numpy.bool_), numpy.zeros(count),
                                numpy.zeros(count), numpy.full(count, WAGES_PURPOSE, dtype=numpy.int64),
                                numpy.full(count, -1, dtype=numpy.int64), template, reference, numpy.zeros(count, dtype=numpy.bool_))


def _ledger_numbers(tables, trades, areas, rows: numpy.ndarray):
    """(trade number, labour market number) in the market memory of each listed market. A name not yet numbered is numbered in the
    order the markets come, trades and markets each as the one-at-a-time calls number them."""
    trade_names = numpy.asarray(trades, dtype=str)[rows]
    distinct, first, inverse = numpy.unique(trade_names, return_index=True, return_inverse=True)
    by_number = numpy.zeros(len(distinct), dtype=numpy.int64)
    for place in numpy.argsort(first, kind="stable").tolist():                 # a new trade is numbered where its first market comes
        by_number[place] = tables.trade_number(str(distinct[place]))
    keys = market_keys(trade_names, numpy.asarray(areas, dtype=str)[rows])
    found = list(map(tables.markets.labour_numbers.get, keys))
    for place, number in enumerate(found):
        if number is None:
            found[place] = tables.markets.labour_row_for_write(keys[place])
    return by_number[inverse.reshape(-1)], numpy.array(found, dtype=numpy.int64)


def _note_hours(ledger, fills, book_of_ref, agent_market, agent_ref, paid, received) -> None:
    """The ledger's rows for every fill (`YearLedger.note_labour_settled` of each market): hours count as far as the wages
    paid cover them."""
    markets = fills.markets
    buys, sells = numpy.diff(fills.buy_start), numpy.diff(fills.sell_start)
    with_fills = numpy.flatnonzero(buys + sells > 0)
    if not len(with_fills):
        return
    market_count, ref_count = len(markets.wage), len(fills.names)
    buy_slot, sell_slot, slot_market, slot_ref = fill_slots(fills.buy_start, fills.buy_ref, fills.sell_start, fills.sell_ref, ref_count)
    paid_by_slot, paid_to_slot = numpy.zeros(len(slot_ref)), numpy.zeros(len(slot_ref))
    if len(paid):
        key = slot_market * ref_count + slot_ref
        order = numpy.argsort(key, kind="stable")
        slot = order[numpy.searchsorted(key[order], agent_market * ref_count + agent_ref)]
        paid_by_slot[slot] = numpy.where(paid > 0.0, paid, 0.0)
        paid_to_slot[slot] = numpy.where(received > 0.0, received, 0.0)
    tables = ledger.tables
    trade_number = numpy.zeros(market_count, dtype=numpy.int64)
    market_number = numpy.zeros(market_count, dtype=numpy.int64)
    trade_number[with_fills], market_number[with_fills] = _ledger_numbers(tables, markets.trade, markets.area, with_fills)
    per_fill = buys + sells
    market_of_fill = numpy.repeat(numpy.arange(market_count, dtype=numpy.int64), per_fill)
    wage = markets.wage[market_of_fill]
    is_buy = interleave(fills.buy_start, numpy.ones(len(fills.buy_ref), dtype=numpy.bool_), fills.sell_start,
                        numpy.zeros(len(fills.sell_ref), dtype=numpy.bool_))
    ledger.note_hours_rows(
        book_of_ref[interleave(fills.buy_start, fills.buy_ref, fills.sell_start, fills.sell_ref)],
        interleave(fills.buy_start, buy_slot, fills.sell_start, sell_slot),
        interleave(fills.buy_start, fills.buy_hours, fills.sell_start, fills.sell_hours), wage, is_buy,
        trade_number[market_of_fill], market_number[market_of_fill], wage, wage > 0.0, paid_by_slot, paid_to_slot)
