"""Every cohort's labour offers written as rows (`labour_offer_rows.LabourOfferRows`): what `households_cohort.labour_offers` makes for one
cohort as `LabourOffer`s, made for all the cohorts at once from columns.

Each cohort offers, in every trade its tile's labour area has people in (trades by name), the cohort's share of those people for the
hours the year leaves them, at the reservation wage for the trade's danger. The rows come out in the order the objects did: cohorts by
id, trades by name. A cohort that is left no hours, or has a share of no one, makes none; so does a trade whose share rounds to nothing."""
from typing import Callable, Dict, Iterable, Mapping, Optional, Sequence, Union

import numpy as np

from .cohort_people import total_by_tile
from .cohort_store import CohortStore, table_of
from .households_cohort import VALUE_OF_LIFE_YEARS_OF_INCOME, Cohort
from .labour_offer_rows import LabourOfferRows


class _AreaTrades:
    """The trades with people in one labour area, in name order, with the figures the offers are made from."""

    def __init__(self, rows: LabourOfferRows, people: Mapping[str, float], danger: Mapping[str, float], value_of_life: float):
        trades = [trade for trade in sorted(people) if people[trade] > 0.0]
        self.count = len(trades)
        self.trade_name = trades
        self.trade = rows.trades.numbers(trades)
        self.people = np.array([people[trade] for trade in trades], dtype=np.float64)
        self.risk_factor = np.array([1.0 + max(0.0, danger.get(trade, 0.0)) * value_of_life for trade in trades], dtype=np.float64)


def hours_left_by_tile(tiles: Sequence[str], hours_per_year: float, levy_hours_per_worker: float, levied_tiles: Iterable[str]) -> list:
    """The hours the workers of each tile have to offer: the year's, less the levy on a levied tile (never below zero)."""
    levied = set(levied_tiles)
    levy = max(0.0, levy_hours_per_worker)
    return [max(0.0, hours_per_year - levy) if tile in levied else hours_per_year for tile in tiles]


def write_cohort_offers(rows: LabourOfferRows, cohorts: Union[CohortStore, Iterable[Cohort]], people_in_area: Callable[[str], Mapping[str, float]],
                        area_of: Callable[[str, str], str], labour_area_of_tile: Callable[[str], str],
                        subsistence_by_tile: Mapping[str, float], hours_per_year: float, danger_by_trade: Mapping[str, float],
                        levy_hours_per_worker: float = 0.0, levied_tiles: Iterable[str] = (),
                        value_of_life: Optional[float] = None) -> None:
    """Append every cohort's offers to `rows`. `cohorts` is the cohort table (or cohorts, made a table here); they are taken by id;
    `people_in_area(area)` is the working people by trade of a labour area; `area_of(trade, tile)` the area a trade's hours are
    offered in from a tile."""
    value_of_life = VALUE_OF_LIFE_YEARS_OF_INCOME if value_of_life is None else value_of_life
    store = table_of(cohorts) if isinstance(cohorts, Mapping) else CohortStore({each.agent_id: each for each in cohorts})
    order = store.order()
    if not len(order):
        return
    tile_names = store.names["tiles"].name_list
    tile_of_row = store.tile_numbers()[order]
    hours_of_tile = np.array(hours_left_by_tile(tile_names, hours_per_year, levy_hours_per_worker, levied_tiles), dtype=np.float64)
    working_of_tile = total_by_tile(store, "working_people")
    area_of_tile = {number: labour_area_of_tile(tile_names[number]) for number in np.unique(tile_of_row).tolist()}
    left = hours_of_tile[tile_of_row]
    kept = np.nonzero(left > 0.0)[0]
    if not len(kept):
        return
    areas: Dict[str, _AreaTrades] = {}
    number_of_area: Dict[str, int] = {}
    for number in tile_of_row[kept].tolist():           # an area is made on its first cohort, in cohort id order
        area = area_of_tile[number]
        if area not in areas:
            areas[area] = _AreaTrades(rows, people_in_area(area), danger_by_trade, value_of_life)
            number_of_area[area] = len(number_of_area)
    chosen_tile = tile_of_row[kept]
    tile_working = working_of_tile[chosen_tile]
    working = store.column("working_people")[order][kept]
    share = np.where(tile_working > 0.0, working / np.where(tile_working > 0.0, tile_working, 1.0), 0.0)
    subsistence = np.array([subsistence_by_tile.get(tile, 0.0) for tile in tile_names], dtype=np.float64)
    area_index = np.array([number_of_area[area_of_tile[number]] for number in chosen_tile.tolist()], dtype=np.int64)
    chosen_ids = [store.ids[row] for row in order[kept].tolist()]
    _append_rows(rows, chosen_ids, [tile_names[number] for number in chosen_tile.tolist()], list(areas.values()), area_index, share,
                 left[kept], subsistence[chosen_tile], area_of)


def _append_rows(rows, chosen_ids, chosen_tiles, area_trades, area_index, share, hours_left, subsistence, area_of) -> None:
    """Expand each cohort over its area's trades and keep the offers that hold a share of someone."""
    lengths = np.array([each.count for each in area_trades], dtype=np.int64)
    starts = np.cumsum(lengths) - lengths
    people = np.concatenate([each.people for each in area_trades])
    trade = np.concatenate([each.trade for each in area_trades])
    factor = np.concatenate([each.risk_factor for each in area_trades])
    per_cohort = lengths[area_index]
    row_cohort = np.repeat(np.arange(len(chosen_ids), dtype=np.int64), per_cohort)
    source = starts[area_index][row_cohort] + (np.arange(len(row_cohort), dtype=np.int64)
                                               - np.repeat(np.cumsum(per_cohort) - per_cohort, per_cohort))
    workers = people[source] * share[row_cohort]
    keep = np.flatnonzero(workers > 0.0)
    if not len(keep):
        return
    row_cohort, source, workers = row_cohort[keep], source[keep], workers[keep]
    hours = workers * hours_left[row_cohort]
    wage = subsistence[row_cohort] / hours_left[row_cohort] * factor[source]
    worker = rows.workers.numbers([chosen_ids[each] for each in row_cohort.tolist()])
    rows.add_rows(worker, trade[source], _area_numbers(rows, chosen_tiles, row_cohort, trade[source], area_of), hours, wage)


def _area_numbers(rows, chosen_tiles, row_cohort, trade, area_of) -> np.ndarray:
    """The number of the area each offer is made in, asked of `area_of` once for each distinct (trade, tile)."""
    tiles = {}
    tile_of_cohort = np.array([tiles.setdefault(each, len(tiles)) for each in chosen_tiles], dtype=np.int64)
    tile_names = list(tiles)
    key = trade * len(tile_names) + tile_of_cohort[row_cohort]
    distinct, inverse = np.unique(key, return_inverse=True)
    trade_names = rows.trades.names
    found = np.array([rows.areas.number(area_of(trade_names[each // len(tile_names)], tile_names[each % len(tile_names)]))
                         for each in distinct.tolist()], dtype=np.int64)
    return found[inverse.reshape(-1)]
