"""A good's cleared markets settled on the book and noted in the year ledger and the market memory, for `year_goods.clear_goods`.

`settle_good` takes the `Cleared` markets of one good in the order they clear. When every market that traded is a `TableClearing`
of one batch, they are settled by ids straight from the order tables (`settlement_ids.settle_by_ids`) and the ledger is given
the settlements as rows (`YearLedger.note_settlement_rows`, one call for the good), the clearings and the rounds likewise
(`note_clearings`); otherwise (a plain clearing on objects, as when a mod replaces the rules) the markets take the old path
through `settlement.settle_goods_many` and `YearLedger.note_settlement`.

What a market's first settlement tells the households' second round is its `bought` (buyer -> units received, money paid net),
which is a `BoughtColumns`: the dictionary is built when the respend asks for a buyer."""
from typing import Dict, List, Optional

import numpy

from . import settlement
from .goods_idle_years import note_idle_years as note_idle_years_kernel
from .goods_good_clear import TABLE_TRADED, TABLE_UNTRADED
from .goods_table_results import TableClearing
from .settlement_ids import SettledByIds, settle_by_ids
from .year_ledger_tables import SALES_PURPOSE


class BoughtColumns:
    """`Settlement.bought_by_buyer` of one market from the settlement's columns, as a mapping built on its first read."""

    def __init__(self, names: list, agents: numpy.ndarray, units: numpy.ndarray, got: numpy.ndarray, net: numpy.ndarray,
                 seen: numpy.ndarray):
        self._columns = (names, agents, units, got, net, seen)
        self._bought = None

    def _built(self) -> Dict[str, tuple]:
        if self._bought is None:
            names, agents, units, got, net, seen = self._columns
            self._bought = {names[agent]: (unit, paid if saw else 0.0) for agent, unit, was_given, paid, saw in zip(
                agents.tolist(), units.tolist(), got.tolist(), net.tolist(), seen.tolist()) if was_given or saw}
        return self._bought

    def columns(self) -> tuple:
        """(agent numbers, units received, money paid net) of the buyers `get` finds: those that were given goods or paid; the money is
        zero where the buyer was not seen paying. In the settlement's row order."""
        _names, agents, units, got, net, seen = self._columns
        found = got | seen
        return agents[found], units[found], numpy.where(seen[found], net[found], 0.0)

    def get(self, buyer: str, default=None):
        return self._built().get(buyer, default)

    def __bool__(self) -> bool:
        return True


def settle_good(record, ledger, cleared, good: str, plant_makers: Dict[str, list]) -> List[tuple]:
    """Settle the traded markets of `cleared` (a `GoodClearing`) on the book and note them in the ledger; returns per market (goods delivered,
    `bought`). `plant_makers` maps a good to the producers whose plant is built from it (`ledger.note_settlement`'s `plant_goods`)."""
    book = record.book
    slots = numpy.flatnonzero(cleared.quantity > 0.0).tolist() if len(cleared) else []
    answer = [(0.0, {}) for _each in range(len(cleared))]     # per market (goods delivered, bought, units to the mint by (seller, tile) if any)
    if not slots:
        return answer
    if (cleared.way[slots] == TABLE_TRADED).all():
        settled = settle_by_ids(book, cleared.batch, cleared.slots[slots], cleared.context.setup.currency_id, good, "sale of %s" % good,
                                ledger.import_accounts, ledger.export_accounts)
        return _noted_by_ids(book, ledger, good, plant_makers, slots, answer, settled, cleared)
    results = [cleared.result(position) for position in slots]
    plant_goods = {producer: {good} for producer in plant_makers.get(good, ())}
    done = iter(settlement.settle_goods_many(book, results, ledger.import_accounts, ledger.export_accounts))
    for position in slots:
        taken = next(done)
        ledger.note_settlement(taken, "sales", plant_goods)
        answer[position] = (taken.delivered, taken.bought_by_buyer(), ledger.pending_mint_takes)    # the takes are noted with the clearing
        ledger.pending_mint_takes = {}
    return answer


def _noted_by_ids(book, ledger, good: str, plant_makers: Dict[str, list], slots: list, answer: list, settled: SettledByIds, cleared) -> list:
    """The ledger's rows of the settled markets (what `YearLedger.note_settlement` noted for each) and the answer per market."""
    if settled is None:
        return answer
    tables = ledger.tables
    tables.fit_agents()
    counts = numpy.diff(settled.agent_offset)
    rows = int(settled.agent_offset[-1])
    market_of_row = numpy.repeat(numpy.arange(len(counts), dtype=numpy.int64), counts)
    template, reference = numpy.zeros(rows, dtype=numpy.int64), numpy.zeros(rows, dtype=numpy.int64)
    foreign = (settled.imports != 0.0) | (settled.exports != 0.0)
    if foreign.any():
        code = tables.purpose_code("sale of %s" % good)
        for market in numpy.unique(market_of_row[foreign]).tolist():
            here = market_of_row == market
            template[here], reference[here] = code
    makers = numpy.array([book.agent_ids.numbers[name] for name in plant_makers.get(good, ()) if name in book.agent_ids.numbers],
                         dtype=numpy.int64)
    plant_bought = (settled.paid > 0.0) & settled.got_goods & numpy.isin(settled.agent, makers)
    ledger.note_settlement_rows(settled.agent, settled.paid, settled.received, settled.imports, settled.exports, settled.got_goods,
                                settled.goods_in, settled.goods_out, numpy.full(rows, SALES_PURPOSE, dtype=numpy.int64),
                                numpy.full(rows, book.good_number(good), dtype=numpy.int64), template, reference, plant_bought)
    found = settled.got_goods | settled.paid_as_buyer
    cleared.bought = (numpy.repeat(numpy.array(slots, dtype=numpy.int64), counts)[found], settled.agent[found], settled.goods_in[found],
                      numpy.where(settled.paid_as_buyer[found], settled.buyer_net[found], 0.0))
    names = book.agent_ids.name_list
    delivered = settled.delivered.tolist()
    for place, position in enumerate(slots):
        first, last = int(settled.agent_offset[place]), int(settled.agent_offset[place + 1])
        answer[position] = (delivered[place], BoughtColumns(names, settled.agent[first:last], settled.goods_in[first:last],
                                                           settled.got_goods[first:last], settled.buyer_net[first:last],
                                                           settled.paid_as_buyer[first:last]))
    _note_mint_takes(book, settled, slots, answer)
    return answer


def _note_mint_takes(book, settled: SettledByIds, slots: list, answer: list) -> None:
    """The units each market's settlement delivered to the mint by (seller, tile), kept for `YearLedger.settled_to_mint`: stored in
    `answer` as a third item of the market's entry when there are any."""
    if not (settled.key_to_mint > 0.0).any():
        return
    names, tiles = book.agent_ids.name_list, book.tile_ids.name_list
    for place, position in enumerate(slots):
        first, last = int(settled.key_offset[place]), int(settled.key_offset[place + 1])
        takes = {}
        for holder, tile, taken in zip(settled.key_holder[first:last].tolist(), settled.key_tile[first:last].tolist(),
                                       settled.key_to_mint[first:last].tolist()):
            if taken > 0.0:
                takes[(names[holder], tiles[tile])] = takes.get((names[holder], tiles[tile]), 0.0) + taken
        if takes:
            answer[position] = (*answer[position], takes)


def note_clearings(ledger, cleared, answer: list, memory_names: list, metal: Optional[str] = None) -> None:
    """`YearLedger.note_clearing` of every market of `cleared` (a `GoodClearing`) in order: the round (market, quantity, price, goods moved)
    added to the ledger's rounds in one call, the watchers' buy fills, and, for a market of the coin `metal` (the good a struck coin's mint
    buys), its clearing with what its settlement delivered to the mint, which `mint_price` reads; no other market keeps its `ClearingResult`."""
    if not len(cleared):
        return
    tables = ledger.tables
    numbers = tables.markets.goods_numbers
    good = cleared.good
    markets = []
    for each in cleared.market.tolist():
        number = numbers.get(memory_names[each])
        markets.append(tables.market_number(good, cleared.areas[len(markets)]) if number is None else number)
    if metal is not None and good == metal:
        for place, entry in enumerate(answer):
            ledger.mint_takes.append((cleared.result(place), entry[2] if len(entry) > 2 else {}))
    watchers = ledger.fill_watchers
    if watchers is not None:
        watched_cumulative = {}
        for place in numpy.flatnonzero(cleared.way != TABLE_UNTRADED).tolist():
            if cleared.way[place] == TABLE_TRADED:
                result = cleared.result(place)
                if _watched_buys(result, watchers, watched_cumulative):
                    for agent, fills in result.bought_by(watchers).items():
                        ledger.buy_fills.setdefault(agent, []).extend(fills)
                continue
            for fill in cleared.result(place).fills:
                if fill.side == "buy" and fill.agent in watchers:
                    ledger.buy_fills.setdefault(fill.agent, []).append(fill)
    else:
        for place in numpy.flatnonzero(cleared.way != TABLE_UNTRADED).tolist():
            for fill in cleared.result(place).fills:
                if fill.side == "buy":
                    ledger.buy_fills.setdefault(fill.agent, []).append(fill)
    ledger.note_round_rows(numpy.array(markets, dtype=numpy.int64), cleared.quantity, cleared.price,
                           numpy.array([entry[0] for entry in answer], dtype=float))


def _watched_buys(result: TableClearing, watchers, kept: dict) -> bool:
    """Whether a watcher's bid in the market took units (`bought_by` would find a fill); the batch's mask is summed once."""
    batch = result.batch
    cumulative = kept.get(id(batch))
    if cumulative is None:
        mask = batch.watched_buys(watchers)
        cumulative = kept[id(batch)] = (False if mask is None else numpy.concatenate(([0], numpy.cumsum(mask))), batch)
    counts = cumulative[0]
    return counts is not False and counts[batch.bid_ptr[result.market + 1]] > counts[batch.bid_ptr[result.market]]


def idle_years(memory, cleared) -> List[int]:
    """`goods_good_clear.note_idle_years` of every market of `cleared` in order: the years each lacked bids or offers before this year, added."""
    tables = memory.tables
    table = tables.goods_table
    before = note_idle_years_kernel(
        table.years_without_bids, table.years_without_offers, table.held, table.order_years_without_bids,
        table.order_years_without_offers, tables.next_order, tables.member_count, cleared.market, cleared.has_offers, cleared.has_units,
        cleared.has_funded_bid)
    return before.tolist()


def last_prices(memory, cleared) -> numpy.ndarray:
    """The remembered price of each market of `cleared` (NaN where it has none), read from the memory's price column in one pass."""
    return memory.tables.goods_table.price[cleared.market] if len(cleared) else numpy.zeros(0)
