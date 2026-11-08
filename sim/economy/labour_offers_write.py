"""Every cohort's labour offers written as rows (`labour_offer_rows.LabourOfferRows`): what `households_cohort.labour_offers` makes for one
cohort as `LabourOffer`s, made for all the cohorts at once from columns.

Each cohort offers, in every trade its tile's labour area has people in (trades by name), the cohort's share of those people for the
hours the year leaves them, at the reservation wage for the trade's danger. The rows come out in the order the objects did: cohorts by
id, trades by name. A cohort that is left no hours, or has a share of no one, makes none; so does a trade whose share rounds to nothing."""
from typing import Callable, Dict, Iterable, Mapping, Optional, Sequence

import numpy

from .households_cohort import VALUE_OF_LIFE_YEARS_OF_INCOME, Cohort
from .labour_offer_rows import LabourOfferRows


class _AreaTrades:
    """The trades with people in one labour area, in name order, with the figures the offers are made from."""

    def __init__(self, rows: LabourOfferRows, people: Mapping[str, float], danger: Mapping[str, float], value_of_life: float):
        trades = [trade for trade in sorted(people) if people[trade] > 0.0]
        self.count = len(trades)
        self.trade_name = trades
        self.trade = rows.trades.numbers(trades)
        self.people = numpy.array([people[trade] for trade in trades], dtype=numpy.float64)
        self.risk_factor = numpy.array([1.0 + max(0.0, danger.get(trade, 0.0)) * value_of_life for trade in trades], dtype=numpy.float64)


def hours_left_by_cohort(cohorts: Sequence[Cohort], hours_per_year: float, levy_hours_per_worker: float, levied_tiles: Iterable[str]) -> list:
    """The hours each cohort's workers have to offer: the year's, less the levy on a levied tile (never below zero)."""
    levied = set(levied_tiles)
    levy = max(0.0, levy_hours_per_worker)
    return [max(0.0, hours_per_year - levy) if cohort.tile in levied else hours_per_year for cohort in cohorts]


def write_cohort_offers(rows: LabourOfferRows, cohorts: Iterable[Cohort], people_in_area: Callable[[str], Mapping[str, float]],
                        area_of: Callable[[str, str], str], labour_area_of_tile: Callable[[str], str],
                        subsistence_by_tile: Mapping[str, float], hours_per_year: float, danger_by_trade: Mapping[str, float],
                        levy_hours_per_worker: float = 0.0, levied_tiles: Iterable[str] = (),
                        value_of_life: Optional[float] = None) -> None:
    """Append every cohort's offers to `rows`. `cohorts` are in the table's order (any order: they are taken by id);
    `people_in_area(area)` is the working people by trade of a labour area; `area_of(trade, tile)` the area a trade's hours are
    offered in from a tile."""
    value_of_life = VALUE_OF_LIFE_YEARS_OF_INCOME if value_of_life is None else value_of_life
    cohorts = list(cohorts)
    working_by_tile: Dict[str, float] = {}
    for cohort in cohorts:
        working_by_tile[cohort.tile] = working_by_tile.get(cohort.tile, 0.0) + cohort.working_people
    ordered = sorted(cohorts, key=lambda each: each.agent_id)
    left = hours_left_by_cohort(ordered, hours_per_year, levy_hours_per_worker, levied_tiles)
    areas: Dict[str, _AreaTrades] = {}
    number_of_area: Dict[str, int] = {}
    chosen, area_index, share, hours, subsistence = [], [], [], [], []
    for cohort, hours_left in zip(ordered, left):
        tile_working = working_by_tile.get(cohort.tile, 0.0)
        area = labour_area_of_tile(cohort.tile)
        if hours_left <= 0.0:
            continue
        if area not in areas:
            areas[area] = _AreaTrades(rows, people_in_area(area), danger_by_trade, value_of_life)
            number_of_area[area] = len(number_of_area)
        chosen.append(cohort)
        area_index.append(number_of_area[area])
        share.append(cohort.working_people / tile_working if tile_working > 0.0 else 0.0)
        hours.append(hours_left)
        subsistence.append(subsistence_by_tile.get(cohort.tile, 0.0))
    if not chosen:
        return
    _append_rows(rows, chosen, list(areas.values()), numpy.array(area_index, dtype=numpy.int64), numpy.array(share), numpy.array(hours),
                 numpy.array(subsistence), area_of)


def _append_rows(rows, chosen, area_trades, area_index, share, hours_left, subsistence, area_of) -> None:
    """Expand each cohort over its area's trades and keep the offers that hold a share of someone."""
    lengths = numpy.array([each.count for each in area_trades], dtype=numpy.int64)
    starts = numpy.cumsum(lengths) - lengths
    people = numpy.concatenate([each.people for each in area_trades])
    trade = numpy.concatenate([each.trade for each in area_trades])
    factor = numpy.concatenate([each.risk_factor for each in area_trades])
    per_cohort = lengths[area_index]
    row_cohort = numpy.repeat(numpy.arange(len(chosen), dtype=numpy.int64), per_cohort)
    source = starts[area_index][row_cohort] + (numpy.arange(len(row_cohort), dtype=numpy.int64)
                                               - numpy.repeat(numpy.cumsum(per_cohort) - per_cohort, per_cohort))
    workers = people[source] * share[row_cohort]
    keep = numpy.flatnonzero(workers > 0.0)
    if not len(keep):
        return
    row_cohort, source, workers = row_cohort[keep], source[keep], workers[keep]
    hours = workers * hours_left[row_cohort]
    wage = subsistence[row_cohort] / hours_left[row_cohort] * factor[source]
    worker = rows.workers.numbers([chosen[each].agent_id for each in row_cohort.tolist()])
    rows.add_rows(worker, trade[source], _area_numbers(rows, chosen, row_cohort, trade[source], area_of), hours, wage)


def _area_numbers(rows, chosen, row_cohort, trade, area_of) -> numpy.ndarray:
    """The number of the area each offer is made in, asked of `area_of` once for each distinct (trade, tile)."""
    tiles = {}
    tile_of_cohort = numpy.array([tiles.setdefault(each.tile, len(tiles)) for each in chosen], dtype=numpy.int64)
    tile_names = list(tiles)
    key = trade * len(tile_names) + tile_of_cohort[row_cohort]
    distinct, inverse = numpy.unique(key, return_inverse=True)
    trade_names = rows.trades.names
    found = numpy.array([rows.areas.number(area_of(trade_names[each // len(tile_names)], tile_names[each % len(tile_names)]))
                         for each in distinct.tolist()], dtype=numpy.int64)
    return found[inverse.reshape(-1)]
