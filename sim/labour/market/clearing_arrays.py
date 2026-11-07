"""The year's labour markets packed into the arrays `clearing_kernel.market_heads` reads, and its answer unpacked.

Areas and trades become positions in sorted id order. The kernel stands in for the plain functions of `clearing.py`,
`import_cost.py` and `fetch_wage.py`, so it is used only where they would give its answer: the fetched-hands search is
the reference one (a mod's replacement is called through the plain path), and the hours each market sells are given as
packed matrices (`sold_hours_kernel`) or not at all."""
from itertools import chain
from operator import attrgetter
from typing import Dict, List, Sequence, Tuple

import numpy as np

from . import clearing_kernel as kernel
from .fetch_wage import fetch_wage as reference_fetch_wage
from .premium import annuity_factor, training_premium
from .records import EmployerHoursBid, MarketState, YearInputs, no_hours
from .sold_hours_kernel import OFFER_ROWS
from .trades import fallback_trade


class PackedHeads:
    """The kernel's arguments for one year, and the markets they hold."""

    def __init__(self, arguments: tuple, markets: Sequence[Tuple[str, str]], groups: Sequence[Sequence[EmployerHoursBid]]):
        self.arguments = arguments
        self.markets = markets
        self.groups = groups        # each market's bids, in the order packed
        (self.cells, self.offers, self.exponent, self.constant) = arguments[:4]
        self.scale, self.market_area, self.market_trade = arguments[6], arguments[17], arguments[18]
        self.bid_offsets, self.caps, self.bid_hours, self.heads = arguments[19], arguments[20], arguments[21], arguments[-1]


def kernel_applies(inputs: YearInputs) -> bool:
    """Whether the kernel gives the plain functions' answer: the reference fetched-hands search is in use and every schedule
    is a packed one (or there is none)."""
    if inputs.fetch_wage is not None and inputs.fetch_wage is not reference_fetch_wage:
        return False
    if inputs.hours_sold_at is None:
        return True
    return all(schedule is no_hours or getattr(schedule, "packed", None) is not None
               for schedule in inputs.hours_sold_at.values())


def _offer_columns(inputs: YearInputs, trade_index: Dict[str, int], area_index: Dict[str, int], cells: np.ndarray):
    """The matrix of every market's offers end to end, with each market's columns written into `cells`; the exponent."""
    pieces: List[np.ndarray] = [np.zeros((OFFER_ROWS, 0))]
    exponent = 1.0
    taken = 0
    for (trade, area), schedule in sorted(inputs.hours_sold_at.items()):
        if trade not in trade_index or area not in area_index:
            continue
        if schedule is no_hours:
            continue
        matrix, exponent = schedule.packed
        cells[kernel.FIRST, area_index[area], trade_index[trade]] = taken
        taken += matrix.shape[1]
        cells[kernel.LAST, area_index[area], trade_index[trade]] = taken
        pieces.append(matrix)
    return np.concatenate(pieces, axis=1), exponent


def pack_heads(state: MarketState, inputs: YearInputs, markets: Sequence[Tuple[str, str]],
               bids_by_market: Dict[Tuple[str, str], List[EmployerHoursBid]], import_costs,
               share_closed_per_year: float) -> PackedHeads:
    """Arguments of `market_heads` for the markets (trade, area), in the order given."""
    trades = sorted(inputs.trades)
    trade_index = {trade: position for position, trade in enumerate(trades)}
    names = set(state.workers) | set(state.wages) | set(state.asks) | set(inputs.subsistence_per_worker_year) | set(inputs.routes)
    names.update(area for _trade, area in markets)
    names.update(map(attrgetter("area"), inputs.bids))
    names.update(route.destination for routes in inputs.routes.values() for route in routes)
    if inputs.hours_sold_at is not None:
        names.update(area for _trade, area in inputs.hours_sold_at)
    areas = sorted(names)
    area_index = {area: position for position, area in enumerate(areas)}
    cells = np.zeros((kernel.CELL_FIELDS, len(areas), len(trades)))
    cells[kernel.WAGE] = np.nan
    hours = inputs.hours_per_worker_year
    for area, by_trade in state.workers.items():
        for trade, bands in by_trade.items():
            if trade in trade_index:
                cells[kernel.EVERYONE, area_index[area], trade_index[trade]] = sum(bands) * hours
    for area, by_trade in state.wages.items():
        for trade, wage in by_trade.items():
            if trade in trade_index:
                cells[kernel.WAGE, area_index[area], trade_index[trade]] = wage
    placed = [bid for bid in inputs.bids if bid.trade in trade_index]      # each bid added to its market's cell in bid order
    if placed:
        bid_cell = (np.array([area_index[area] for area in map(attrgetter("area"), placed)], np.int64),
                    np.array([trade_index[trade] for trade in map(attrgetter("trade"), placed)], np.int64))
        np.add.at(cells[kernel.WANTED], bid_cell, np.maximum(np.fromiter(map(attrgetter("hours"), placed), np.float64, len(placed)), 0.0))
        np.maximum.at(cells[kernel.MOST], bid_cell, np.fromiter(map(attrgetter("maximum_wage"), placed), np.float64, len(placed)))
    constant = inputs.hours_sold_at is None
    if constant:
        offers, exponent = np.zeros((OFFER_ROWS, 0)), 1.0
    else:
        offers, exponent = _offer_columns(inputs, trade_index, area_index, cells)
    subsistence = np.full(len(areas), np.nan)
    ask_floor = np.full(len(areas), np.nan)
    for area, value in inputs.subsistence_per_worker_year.items():
        subsistence[area_index[area]] = value
    for area, value in inputs.ask_floor_per_worker_year.items():
        if area in area_index:
            ask_floor[area_index[area]] = value
    scale = np.ones((len(areas), len(trades)))
    for area, by_trade in state.asks.items():
        for trade, value in by_trade.items():
            if trade in trade_index:
                scale[area_index[area], trade_index[trade]] = value
    specs = [inputs.trades[trade] for trade in trades]
    risk = np.array([spec.fatality_risk_per_year for spec in specs])
    training_years = np.array([spec.training_years for spec in specs])
    premium = np.array([training_premium(spec.training_years, inputs.discount_rate, inputs.career_years) for spec in specs])
    career_hours = max(annuity_factor(inputs.discount_rate, inputs.career_years) * hours, 1e-12)
    with_bids = sorted({area for (_trade, area), bids in bids_by_market.items() if bids})
    reaches = {area: import_costs.reach(area) for area in with_bids}
    width = max([len(each) for each in reaches.values()] + [1])
    reach_other = np.zeros((len(areas), width), np.int64)
    reach_cost = np.zeros((len(areas), width))
    reach_count = np.zeros(len(areas), np.int64)
    for area, reach in reaches.items():
        position = area_index[area]
        reach_count[position] = len(reach)
        for slot, (cost, other) in enumerate(reach):
            reach_other[position, slot] = area_index[other]
            reach_cost[position, slot] = cost
    market_area = np.array([area_index[area] for _trade, area in markets], np.int64)
    market_trade = np.array([trade_index[trade] for trade, _area in markets], np.int64)
    groups = [bids_by_market.get(market, ()) for market in markets]
    bid_offsets = np.zeros(len(markets) + 1, np.int64)
    np.cumsum([len(each) for each in groups], out=bid_offsets[1:])
    packed_bids = list(chain.from_iterable(groups))
    caps = np.fromiter(map(attrgetter("maximum_wage"), packed_bids), np.float64, len(packed_bids))
    bid_hours = np.fromiter(map(attrgetter("hours"), packed_bids), np.float64, len(packed_bids))
    fallback = trade_index[fallback_trade(inputs.trades)]
    heads = np.zeros((len(markets), kernel.HEAD_FIELDS))
    arguments = (cells, offers, exponent, constant, subsistence, ask_floor, scale, risk, training_years, premium, fallback,
                 inputs.value_of_life_years_of_income, hours, career_hours, reach_other, reach_cost, reach_count, market_area,
                 market_trade, bid_offsets, caps, bid_hours, share_closed_per_year, heads)
    return PackedHeads(arguments, markets, groups)


def run_heads(packed: PackedHeads) -> np.ndarray:
    """`heads[market, field]` for the packed markets."""
    kernel.market_heads(*packed.arguments)
    return packed.arguments[-1]
