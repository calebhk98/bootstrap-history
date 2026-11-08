"""The fills of a year's labour markets as columns (the table form of the `LabourResult`s `year_labour._result` builds one by one).

`LabourFills` holds, per cleared market (in (trade, area) order): the trade, area, wage and hours; and per fill, market after
market, the buys (employers' hours hired) then the sells (workers' hours sold), each side in name order. An agent is a `ref`:
its place among `names`, the sorted names of every employer and worker with a fill. A buy's quantity is the hours the employer
hired; a sell's is the market's hours hired in proportion to the hours the worker offered. `from_clearings` reads the core's
`Clearings` columns; `from_objects` takes a plain list of `LabourClearing`s (a mod's or a test's).
"""
from typing import Dict, List, NamedTuple, Sequence, Tuple

import numpy

from .labour_walk_kernel import grouped_python_sums


class MarketRows(NamedTuple):
    """The cleared markets, in (trade, area) order."""
    trade: List[str]                  # the market's trade
    area: List[str]                   # the market's labour area
    wage: numpy.ndarray               # the one wage of the market, money per hour
    hours_hired: numpy.ndarray        # hours employers hired in it
    vacant_hours: numpy.ndarray       # hours employers wanted and did not get (never below zero)
    idle_hours: numpy.ndarray         # hours offered and not hired (never below zero)


class BuyRows(NamedTuple):
    """Hours hired by each employer in each market, market after market; employers are unique in a market."""
    market_start: numpy.ndarray       # market m's rows are market_start[m]:market_start[m + 1] (any order within the market)
    employer: numpy.ndarray           # index into the employer names
    hours: numpy.ndarray              # hours hired, above zero


class LabourFills(NamedTuple):
    markets: MarketRows
    names: List[str]                  # sorted names of the agents with a fill; a ref is a place in this list
    buy_start: numpy.ndarray          # market m's buys are buy_start[m]:buy_start[m + 1]
    buy_ref: numpy.ndarray            # the employer
    buy_hours: numpy.ndarray          # hours hired
    sell_start: numpy.ndarray         # market m's sells are sell_start[m]:sell_start[m + 1]
    sell_ref: numpy.ndarray           # the worker
    sell_hours: numpy.ndarray         # hours sold


def _positive_part(difference: numpy.ndarray) -> numpy.ndarray:
    """`max(0.0, difference)` for each, as Python takes it."""
    return numpy.where(difference > 0.0, difference, 0.0)


def rows_from_clearings(clearings) -> Tuple[MarketRows, BuyRows, Sequence[str]]:
    """The market and buy rows of the core's `Clearings` columns, and the employer names their numbers index."""
    area_names, trade_names = clearings.names
    hired = clearings.hours_hired
    markets = MarketRows([trade_names[each] for each in clearings.trade.tolist()], [area_names[each] for each in clearings.area.tolist()],
                         clearings.wage, hired, _positive_part(clearings.hours_wanted - hired),
                         _positive_part(clearings.hours_offered - hired))
    packed = clearings.markets
    first, last = clearings.slot_offsets[packed], clearings.slot_offsets[packed + 1]
    counts = last - first
    cut = numpy.concatenate(([0], numpy.cumsum(counts))).astype(numpy.int64)
    position = numpy.repeat(first - cut[:-1], counts) + numpy.arange(int(cut[-1]), dtype=numpy.int64)
    employer, hours = clearings.slot_employer[position], clearings.slot_hired[position]
    market_of_row = numpy.repeat(numpy.arange(len(packed), dtype=numpy.int64), counts)
    keep = hours > 0.0
    start = numpy.concatenate(([0], numpy.cumsum(numpy.bincount(market_of_row[keep], minlength=len(packed))))).astype(numpy.int64)
    return markets, BuyRows(start, employer[keep], hours[keep]), clearings.employers


def rows_from_objects(clearings) -> Tuple[MarketRows, BuyRows, Sequence[str]]:
    """`rows_from_clearings` of a list of `LabourClearing`s, in (trade, area) order."""
    ordered = sorted(clearings, key=lambda each: (each.trade, each.area))
    employers: Dict[str, int] = {}
    employer, hours, start = [], [], [0]
    for clearing in ordered:
        for name, amount in clearing.hired_by_employer.items():
            if amount > 0.0:
                employer.append(employers.setdefault(name, len(employers)))
                hours.append(amount)
        start.append(len(employer))
    hired = numpy.array([each.hours_hired for each in ordered], dtype=numpy.float64)
    markets = MarketRows([each.trade for each in ordered], [each.area for each in ordered],
                         numpy.array([each.wage for each in ordered], dtype=numpy.float64), hired,
                         numpy.array([each.vacant_hours for each in ordered], dtype=numpy.float64),
                         numpy.array([each.idle_hours for each in ordered], dtype=numpy.float64))
    return (markets, BuyRows(numpy.array(start, dtype=numpy.int64), numpy.array(employer, dtype=numpy.int64),
                             numpy.array(hours, dtype=numpy.float64)), list(employers))


def sell_rows(markets: MarketRows, offers: Sequence) -> Tuple[List[str], numpy.ndarray, numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    """The sells of the offers that sold into these markets: (worker names, the place in them of each sell's worker, market, hours
    sold, order of the offer), in the order of the offers. A market's hired hours are shared out in proportion to the hours each
    offer held (the sum taken in the offers' order, as `year_labour._result` did); only a market that hired anything gives sells,
    and only an offer holding hours. The offers of a market the clearing did not cover are not sells. Offers that are the rows of
    a supply's settlement (`labour_sold_offers.SoldOffers`) are read from their columns; any other sequence, offer by offer."""
    if hasattr(offers, "sold_columns"):
        rows, held = offers.market_rows(markets.trade, markets.area), offers.sold_columns()
    else:
        row_of = {(trade, area): row for row, (trade, area) in enumerate(zip(markets.trade, markets.area))}
        rows = numpy.array([row_of.get((offer.trade, offer.area), -1) for offer in offers], dtype=numpy.int64)
        held = numpy.array([offer.hours for offer in offers], dtype=numpy.float64)
    inside = numpy.flatnonzero(rows >= 0)
    by_market = inside[numpy.argsort(rows[inside], kind="stable")]
    start = numpy.searchsorted(rows[by_market], numpy.arange(len(markets.wage) + 1)).astype(numpy.int64)
    offered = grouped_python_sums(start, held[by_market])
    hired = markets.hours_hired
    sells = numpy.flatnonzero((rows >= 0) & (held > 0.0))
    sells = sells[(offered[rows[sells]] > 0.0) & (hired[rows[sells]] > 0.0)]
    quantity = hired[rows[sells]] * held[sells] / offered[rows[sells]]
    if hasattr(offers, "sold_columns"):
        workers, worker_place = offers.workers_of(sells)
    else:
        workers, worker_place = [offers[each].worker for each in sells.tolist()], numpy.arange(len(sells), dtype=numpy.int64)
    return workers, worker_place, rows[sells], quantity, sells


def fills_of(markets: MarketRows, buys: BuyRows, employer_names: Sequence[str], offers: Sequence) -> LabourFills:
    """The fills of the markets: buys and sells each sorted by name inside their market (a worker with two offers in a market
    keeps them in the offers' order)."""
    workers, worker_place, sell_market, sell_quantity, sell_order = sell_rows(markets, offers)
    used, buy_employer = numpy.unique(buys.employer, return_inverse=True)
    used_names = [employer_names[each] for each in used.tolist()]
    names = sorted(set(used_names).union(workers))
    ref_of = {name: ref for ref, name in enumerate(names)}
    buy_ref = numpy.array([ref_of[name] for name in used_names], dtype=numpy.int64)[buy_employer.reshape(-1)]
    sell_ref = numpy.array([ref_of[name] for name in workers], dtype=numpy.int64)[worker_place]
    count = len(markets.wage)
    buy_market = numpy.repeat(numpy.arange(count, dtype=numpy.int64), numpy.diff(buys.market_start))
    buy_order = numpy.lexsort((buy_ref, buy_market))
    sell_order_sorted = numpy.lexsort((sell_order, sell_ref, sell_market))
    return LabourFills(
        markets, names, buys.market_start, buy_ref[buy_order], buys.hours[buy_order],
        numpy.searchsorted(sell_market[sell_order_sorted], numpy.arange(count + 1)).astype(numpy.int64),
        sell_ref[sell_order_sorted], sell_quantity[sell_order_sorted])
