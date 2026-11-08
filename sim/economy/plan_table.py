"""The year's producer plans as columns (docs/architecture/COMPILED_YEAR.md, stage 4): what `producers.plan` gives every producer, kept as
one row per producer and one row per bid or labour bid, with no `Plan`, `Bid` or `LabourBid` object made in the year loop.

`PlanTable` is what `plan_year.plans_of` returns. A producer is a position (`ids` is sorted, `position[id]` its place).

Producer columns (one entry per producer):
    runs            runs planned this year (0.0: idle)                                           runs
    wanted_runs     runs it wanted before the land it was granted capped them                    runs
    wage_line       cash set for the planned runs' labour                                        currency units
    budget_total    the producer's input bids' budgets added as Python's `sum` adds them        currency units
    outlay_total    the plan's lines (wage line, then each input budget, each at least zero) added as `sum` adds    currency units
    bid_start       first input-bid row of the producer (`bid_start[n]` is the row count)       row

Input-bid rows (`bids`, grouped by producer in slot order, the order the bids reach the book of orders):
    position        the buying producer                                                         producer position
    good, tile, area  index into `good_names`, `tile_names`, `area_names`
    priority        need tier                                                                    tier
    figures         floor, flexible quantity, reference price, elasticity, budget, maximum price (the fields of `types.Bid`)

Labour-bid rows (`labour`, grouped by producer in slot order): position, trade (index into `trade_names`), labour area (index into
`area_names`), hours, maximum wage per hour. `write_labour_bids(bid_table)` appends them to the year's `LabourBidTable`.

Objects exist only at the edge: `plan_of(id)` builds the `Plan` of one producer (tests, screens), `labour_bid_objects()` the
`LabourBid`s of every producer (tests), `get(id)` a `Plan` with the figures and no bids (what the goods clearing reads)."""
import math
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Tuple

import numpy

from sim.jit import njit

from .goods_order_book import GoodsOrderBook
from .goods_order_objects import make_bid
from .goods_order_tables import PRODUCER_INPUT
from .producers import Plan
from .types import LabourBid


@njit
def plan_sums(wage_line, budget, bid_start):
    """Per producer, (the input budgets added left to right as CPython 3.12+ `sum` of floats adds them, the wage line and then each
    budget clamped at zero added the same way). Empty groups add to 0.0."""
    count = len(bid_start) - 1
    budget_total = numpy.zeros(count)
    outlay_total = numpy.zeros(count)
    for producer in range(count):
        total, carry = 0.0, 0.0
        line_total, line_carry = 0.0, 0.0
        line_total, line_carry = _add(line_total, line_carry, wage_line[producer] if wage_line[producer] > 0.0 else 0.0)
        for row in range(bid_start[producer], bid_start[producer + 1]):
            total, carry = _add(total, carry, budget[row])
            line_total, line_carry = _add(line_total, line_carry, budget[row] if budget[row] > 0.0 else 0.0)
        budget_total[producer] = _finish(total, carry)
        outlay_total[producer] = _finish(line_total, line_carry)
    return budget_total, outlay_total


@njit
def _add(total, carry, value):
    """One step of the compensated sum Python's `sum` of floats takes: the running total and the low digits lost so far."""
    step = total + value
    if abs(total) >= abs(value):
        carry += (total - step) + value
    else:
        carry += (value - step) + total
    return step, carry


@njit
def _finish(total, carry):
    """The sum with its compensation added, unless that would turn an infinite or overflowed sum into NaN."""
    if carry != 0.0 and math.isfinite(carry):
        return total + carry
    return total


@dataclass
class BidColumns:
    position: numpy.ndarray
    good: numpy.ndarray
    tile: numpy.ndarray
    area: numpy.ndarray
    priority: numpy.ndarray
    figures: numpy.ndarray


@dataclass
class LabourColumns:
    position: numpy.ndarray        # the bidding producer's position
    trade: numpy.ndarray           # index into the table's trade names
    area: numpy.ndarray            # index into the table's area names (a labour area)
    hours: numpy.ndarray           # hours wanted, hours per year
    maximum_wage: numpy.ndarray    # most an hour is worth to the producer, money per hour


class ColumnMap(Mapping):
    """A read-only `{producer id: value}` over a column (a list of Python floats), for the callers that look a producer up."""

    def __init__(self, position: Mapping[str, int], values: List[float]):
        self._position, self._values = position, values

    def __getitem__(self, producer_id):
        return self._values[self._position[producer_id]]

    def get(self, producer_id, default=None):
        found = self._position.get(producer_id)
        return default if found is None else self._values[found]

    def __iter__(self):
        return iter(self._position)

    def __len__(self):
        return len(self._position)


class PlanTable:
    """Every producer's plan as columns (see the module docstring)."""

    def __init__(self, ids: Tuple[str, ...], runs: List[float], wanted_runs: List[float], wage_line: numpy.ndarray, bids: BidColumns,
                 labour: LabourColumns, good_names: List[str], tile_names: List[str], area_names: List[str],
                 objects: Optional[Dict[int, Plan]] = None, trade_names: Optional[List[str]] = None):
        self.ids = ids
        self.position = {producer_id: place for place, producer_id in enumerate(ids)}
        self.runs, self.wanted_runs = runs, wanted_runs
        self.wage_line = numpy.ascontiguousarray(wage_line, dtype=numpy.float64)
        self.bids, self.labour = bids, labour
        self.good_names, self.tile_names, self.area_names = good_names, tile_names, area_names
        self.trade_names = trade_names or []
        self.objects = objects or {}      # position -> the Plan itself, kept for a producer planned by `producers.plan`
        self.bid_start = numpy.searchsorted(bids.position, numpy.arange(len(ids) + 1)).astype(numpy.int64)
        totals = plan_sums(self.wage_line, numpy.ascontiguousarray(bids.figures[:, 4]), self.bid_start)
        self.budget_total, self.outlay_total = totals
        self._labour_start = numpy.searchsorted(labour.position, numpy.arange(len(ids) + 1))

    def __len__(self) -> int:
        return len(self.ids)

    def wanted_runs_by_id(self) -> ColumnMap:
        return ColumnMap(self.position, self.wanted_runs)

    def budget_total_by_id(self) -> ColumnMap:
        return ColumnMap(self.position, self.budget_total.tolist())

    def get(self, producer_id: str, default=None) -> Optional[Plan]:
        """The producer's runs, runs wanted and wage line as a `Plan` without bids (the goods clearing reads `runs`); the Plan itself
        for a producer `producers.plan` planned."""
        place = self.position.get(producer_id)
        if place is None:
            return default
        if place in self.objects:
            return self.objects[place]
        return Plan(self.runs[place], wanted_runs=self.wanted_runs[place], wage_line=float(self.wage_line[place]))

    def plan_of(self, producer_id: str) -> Plan:
        """The producer's whole plan, its bids and labour bids made as objects (an edge: a test, a screen)."""
        place = self.position[producer_id]
        if place in self.objects:
            return self.objects[place]
        first, last = int(self.bid_start[place]), int(self.bid_start[place + 1])
        bids = tuple(self._bid(row) for row in range(first, last))
        labour = self.labour_objects(int(self._labour_start[place]), int(self._labour_start[place + 1]))
        return Plan(self.runs[place], tuple(labour), bids, self.wanted_runs[place], float(self.wage_line[place]))

    def _bid(self, row: int):
        columns = self.bids
        floor, flexible, reference, elasticity, budget, ceiling = columns.figures[row].tolist()
        return make_bid(self.ids[int(columns.position[row])], self.good_names[int(columns.good[row])],
                        self.area_names[int(columns.area[row])], self.tile_names[int(columns.tile[row])], floor, flexible, reference,
                        elasticity, budget, int(columns.priority[row]), ceiling)

    def labour_objects(self, first: int, last: int) -> List[LabourBid]:
        columns = self.labour
        hours, wages = columns.hours[first:last].tolist(), columns.maximum_wage[first:last].tolist()
        employers = [self.ids[place] for place in columns.position[first:last].tolist()]
        trades = [self.trade_names[place] for place in columns.trade[first:last].tolist()]
        areas = [self.area_names[place] for place in columns.area[first:last].tolist()]
        return [LabourBid(*each) for each in zip(employers, trades, areas, hours, wages)]

    def labour_bid_objects(self) -> List[LabourBid]:
        """Every producer's labour bids as objects, in producer order (an edge: tests)."""
        return self.labour_objects(0, len(self.labour.position))

    def write_labour_bids(self, bid_table) -> None:
        """Append every producer's labour bids to the year's `LabourBidTable`, in producer order (the order of the rows). Names are
        numbered once for each distinct producer, trade and area."""
        columns = self.labour
        if not len(columns.position):
            return
        producers, producer_place = numpy.unique(columns.position, return_inverse=True)
        trades, trade_place = numpy.unique(columns.trade, return_inverse=True)
        areas, area_place = numpy.unique(columns.area, return_inverse=True)
        bid_table.add_rows(bid_table.employers.numbers([self.ids[each] for each in producers.tolist()])[producer_place.reshape(-1)],
                           bid_table.trades.numbers([self.trade_names[each] for each in trades.tolist()])[trade_place.reshape(-1)],
                           bid_table.areas.numbers([self.area_names[each] for each in areas.tolist()])[area_place.reshape(-1)],
                           columns.hours, columns.maximum_wage)


class PlanBids:
    """The table's input bids as an item for a `NamedOrderBook` (order_book_named.py): the names are the distinct producers, goods, tiles
    and (good, area) pairs of the rows, numbered once each, and the rows are the table's own columns with those ids put in."""

    source = PRODUCER_INPUT

    def __init__(self, table: PlanTable):
        columns = table.bids
        self.table = table
        self.buyers, self.buyer_place = numpy.unique(columns.position, return_inverse=True)
        self.goods, self.good_place = numpy.unique(columns.good, return_inverse=True)
        self.tiles, self.tile_place = numpy.unique(columns.tile, return_inverse=True)
        self.areas = len(table.area_names)
        self.pairs, self.pair_place = numpy.unique(columns.good * self.areas + columns.area, return_inverse=True)

    def names(self) -> tuple:
        table = self.table
        return ([table.ids[place] for place in self.buyers.tolist()], [table.good_names[place] for place in self.goods.tolist()],
                [table.tile_names[place] for place in self.tiles.tolist()],
                [(table.good_names[pair // self.areas], table.area_names[pair % self.areas]) for pair in self.pairs.tolist()])

    def rows(self, order_book) -> tuple:
        table = self.table
        names = self.names()
        markets = order_book.market_ids([good for good, _area in names[3]], [area for _good, area in names[3]])
        return (numpy.array(order_book.agent_ids_of(names[0]), dtype=numpy.int64)[self.buyer_place],
                numpy.array(order_book.good_ids_of(names[1]), dtype=numpy.int64)[self.good_place],
                numpy.array(order_book.tile_ids_of(names[2]), dtype=numpy.int64)[self.tile_place],
                numpy.array(markets, dtype=numpy.int64)[self.pair_place], table.bids.priority, table.bids.figures)


def write_bids(table: PlanTable, order_book) -> None:
    """Hand every producer's input bids to the book of orders as rows, in the order of the table (producer order, slot order): they wait
    by name in a `NamedOrderBook`, are appended at once to a plain `GoodsOrderBook`, and are made into `Bid` objects for a plain
    `{(good, area): (bids, offers)}` dict (a test)."""
    count = len(table.bids.position)
    if not count:
        return
    if hasattr(order_book, "add_named_bids"):
        order_book.add_named_bids(PlanBids(table))
    elif isinstance(order_book, GoodsOrderBook):
        order_book.append_bids(*PlanBids(table).rows(order_book), PRODUCER_INPUT)
    else:
        for row in range(count):
            bid = table._bid(row)
            order_book.setdefault((bid.good, bid.area), ([], []))[0].append(bid)
