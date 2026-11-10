"""The year's labour markets packed from the state's tables and the bid columns into the arrays `clearing_kernel.market_heads`
reads.

The kernel stands in for the plain functions of `clearing.py`, `import_cost.py` and `fetch_wage.py`, so it is used only where
they would give its answer: the fetched-hands search is the reference one (a mod's replacement is called through the plain
path), and the hours each market sells are given as packed matrices (`sold_hours_kernel`) or not at all.

Areas and trades are the state's own numbers (sorted name order, state_ids.py), a grid row is `area * trade_count + trade`.
Markets are listed by (trade, area), the order the plain code visited them in."""
from typing import Dict, List, NamedTuple, Tuple

import numpy as np

from sim.compiled_tables.grouping import group_starts, stable_order

from . import bid_book, clearing_kernel as kernel, clearing_pack
from .fetch_wage import fetch_wage as reference_fetch_wage
from .year_carriage import dense_carriage
from .market_state import MarketState
from .premium import annuity_factor, training_premium
from .records import YearInputs, no_hours
from .sold_hours_kernel import OFFER_ROWS
from .trades import fallback_trade


class PackedHeads(NamedTuple):
    """The kernel's arguments for one year, and the markets and bids they hold (bids end to end by market, in the order the
    caller gave them within a market)."""
    arguments: tuple
    market_row: np.ndarray        # grid row of each market
    market_area: np.ndarray
    market_trade: np.ndarray
    bid_offsets: np.ndarray       # market m's bids are bid_offsets[m] .. bid_offsets[m + 1] - 1
    caps: np.ndarray              # maximum wage of each bid
    bid_hours: np.ndarray         # hours of each bid
    bid_employer: np.ndarray      # employer number of each bid
    heads: np.ndarray

    @property
    def markets(self) -> int:
        return len(self.market_row)


def kernel_applies(inputs: YearInputs) -> bool:
    """Whether the kernel gives the plain functions' answer: the reference fetched-hands search is in use and every schedule
    is a packed one (or there is none)."""
    if inputs.fetch_wage is not None and inputs.fetch_wage is not reference_fetch_wage:
        return False
    if inputs.hours_sold_at is None or getattr(inputs.hours_sold_at, "columns", None) is not None:
        return True       # no schedule, or the offers' table gives the matrix itself (labour_supply_markets.MarketHours)
    return all(schedule is no_hours or getattr(schedule, "packed", None) is not None
               for schedule in inputs.hours_sold_at.values())


def _offer_columns(inputs: YearInputs, state: MarketState, cells: np.ndarray, in_play: np.ndarray):
    """The matrix of every market's offers end to end, with each market's columns written into `cells`; the exponent."""
    trade_of, area_of = state.ids.trades.find, state.ids.areas.find
    columns = getattr(inputs.hours_sold_at, "columns", None)
    if columns is not None:                 # the table's matrix as it is: only the ranges of the markets in play are named
        for position, (trade, area) in enumerate(columns.markets):
            trade_number, area_number = trade_of(trade), area_of(area)
            if trade_number is not None and area_number is not None and in_play[trade_number]:
                cells[kernel.FIRST, area_number, trade_number] = columns.first[position]
                cells[kernel.LAST, area_number, trade_number] = columns.last[position]
        return columns.matrix, columns.exponent
    pieces: List[np.ndarray] = [np.zeros((OFFER_ROWS, 0))]
    exponent = 1.0
    taken = 0
    for (trade, area), schedule in sorted(inputs.hours_sold_at.items()):
        trade_number, area_number = trade_of(trade), area_of(area)
        if trade_number is None or area_number is None or not in_play[trade_number] or schedule is no_hours:
            continue
        matrix, exponent = schedule.packed
        cells[kernel.FIRST, area_number, trade_number] = taken
        taken += matrix.shape[1]
        cells[kernel.LAST, area_number, trade_number] = taken
        pieces.append(matrix)
    return np.concatenate(pieces, axis=1), exponent


def _area_names(state: MarketState, inputs: YearInputs) -> set:
    """Every area the year names."""
    names = set(inputs.subsistence_per_worker_year) | set(inputs.routes) | set(inputs.ask_floor_per_worker_year) | bid_book.area_names(inputs.bids)
    names.update(route.destination for routes in inputs.routes.values() for route in routes)
    if inputs.hours_sold_at is not None:
        names.update(area for _trade, area in (inputs.hours_sold_at.columns.markets if getattr(inputs.hours_sold_at, "columns", None) is not None
                                                else inputs.hours_sold_at))
    return names


def _reaches(inputs: YearInputs, areas_with_bids: np.ndarray, state: MarketState) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per area with bids: the areas reachable from it, nearest first (ties by name), with the cost (`ImportCosts.reach`)."""
    count = len(state.ids.areas)
    carriage = dense_carriage(state, inputs)
    others = np.arange(count)
    found = {}
    for area in areas_with_bids.tolist():
        reachable = np.flatnonzero(~np.isnan(carriage[area]) & (others != area))
        found[area] = reachable[np.lexsort((reachable, carriage[area, reachable]))]
    width = max([len(each) for each in found.values()] + [1])
    reach_other = np.zeros((count, width), np.int64)
    reach_cost = np.zeros((count, width))
    reach_count = np.zeros(count, np.int64)
    for area, reachable in found.items():
        reach_count[area] = len(reachable)
        reach_other[area, :len(reachable)] = reachable
        reach_cost[area, :len(reachable)] = carriage[area, reachable]
    return reach_other, reach_cost, reach_count


def pack_heads(state: MarketState, inputs: YearInputs, share_closed_per_year: float) -> PackedHeads:
    """Arguments of `market_heads` for every market of the year: those with a bid for hours and those whose trade has people in
    the area. Admits to the state the areas, trades and employers the year names."""
    state.admit(_area_names(state, inputs), inputs.trades)
    bids = bid_book.numbered(state, inputs.bids)
    ids = state.ids
    area_count, trade_count = len(ids.areas), len(ids.trades)
    in_play = np.zeros(trade_count, np.bool_)
    in_play[[ids.trades.number(trade) for trade in inputs.trades]] = True
    bid_employer, bid_area = bids.employer, bids.area
    placed = (bids.trade >= 0) & in_play[np.maximum(bids.trade, 0)]       # a bid for a trade the year does not list is not placed
    bid_trade = np.where(placed, bids.trade, -1)
    market_row = np.where(placed, bid_area * trade_count + bid_trade, 0)
    hours = inputs.hours_per_worker_year
    cells = np.zeros((kernel.CELL_FIELDS, area_count, trade_count))
    everyone, with_people = np.zeros(area_count * trade_count), np.zeros(area_count * trade_count, np.bool_)
    clearing_pack.people_hours(state.workers_table.people, state.workers_table.present, np.tile(in_play, area_count), hours,
                               trade_count, everyone, with_people)
    cells[kernel.EVERYONE] = everyone.reshape(area_count, trade_count)
    cells[kernel.WAGE] = np.where(in_play[None, :], state.market_table.wage.reshape(area_count, trade_count), np.nan)
    wanted, most = np.zeros(area_count * trade_count), np.zeros(area_count * trade_count)
    clearing_pack.bid_totals(market_row[placed], bids.hours[placed], bids.maximum_wage[placed], wanted, most)
    cells[kernel.WANTED], cells[kernel.MOST] = wanted.reshape(area_count, trade_count), most.reshape(area_count, trade_count)
    constant = inputs.hours_sold_at is None
    offers, exponent = (np.zeros((OFFER_ROWS, 0)), 1.0) if constant else _offer_columns(inputs, state, cells, in_play)
    subsistence, ask_floor = np.full(area_count, np.nan), np.full(area_count, np.nan)
    for area, value in inputs.subsistence_per_worker_year.items():
        subsistence[ids.areas.number(area)] = value
    for area, value in inputs.ask_floor_per_worker_year.items():
        ask_floor[ids.areas.number(area)] = value
    ask = state.market_table.ask
    scale = np.where(np.isnan(ask), 1.0, ask).reshape(area_count, trade_count)
    specs = [inputs.trades.get(name) for name in ids.trades.names]
    risk = np.array([spec.fatality_risk_per_year if spec else 0.0 for spec in specs])
    training_years = np.array([spec.training_years if spec else 0.0 for spec in specs])
    premium = np.array([training_premium(spec.training_years, inputs.discount_rate, inputs.career_years) if spec else 0.0 for spec in specs])
    career_hours = max(annuity_factor(inputs.discount_rate, inputs.career_years) * hours, 1e-12)
    positive = placed & (bids.hours > 0.0)
    grouped_row, grouped_hours, grouped_wage, grouped_employer = (each[positive] for each in (
        market_row, bids.hours, bids.maximum_wage, bid_employer))
    in_market = np.zeros(area_count * trade_count, np.bool_)
    in_market[grouped_row] = True
    in_market |= with_people
    market_rows = np.flatnonzero(in_market.reshape(area_count, trade_count).T.ravel())    # (trade, area) order
    market_trade, market_area = market_rows // area_count, market_rows % area_count
    market_row_grid = market_area * trade_count + market_trade
    market_of_row = np.full(area_count * trade_count, -1, np.int64)
    market_of_row[market_row_grid] = np.arange(len(market_row_grid))
    group = market_of_row[grouped_row]
    starts = group_starts(group, len(group), len(market_row_grid))
    order = stable_order(group, len(group), starts)
    caps, bid_hours, bid_employer = grouped_wage[order], grouped_hours[order], grouped_employer[order]
    with_bids = np.unique(market_area[np.diff(starts) > 0])
    reach_other, reach_cost, reach_count = _reaches(inputs, with_bids, state)
    fallback = ids.trades.number(fallback_trade(inputs.trades))
    heads = np.zeros((len(market_row_grid), kernel.HEAD_FIELDS))
    arguments = (cells, offers, exponent, constant, subsistence, ask_floor, scale, risk, training_years, premium, fallback,
                 inputs.value_of_life_years_of_income, hours, career_hours, reach_other, reach_cost, reach_count, market_area,
                 market_trade, starts, caps, bid_hours, share_closed_per_year, heads)
    return PackedHeads(arguments, market_row_grid, market_area, market_trade, starts, caps, bid_hours, bid_employer, heads)


def run_heads(packed: PackedHeads) -> np.ndarray:
    """`heads[market, field]` for the packed markets."""
    kernel.market_heads(*packed.arguments)
    return packed.heads
