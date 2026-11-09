"""Every cohort's labour offers written as rows (`labour_offer_rows.LabourOfferRows`): what `households_cohort.labour_offers` makes for one
cohort as `LabourOffer`s, made for all the cohorts at once from columns.

Each cohort offers, in every trade its tile's labour area has people in (trades by name), the cohort's share of those people for the
hours the year leaves them, at the reservation wage for the trade's danger. The rows come out in the order the objects did: cohorts by
id, trades by name. A cohort that is left no hours, or has a share of no one, makes none; so does a trade whose share rounds to nothing."""
from typing import Callable, Iterable, Mapping, Optional, Sequence, Tuple, Union

import numpy as np

from .cohort_people import total_by_tile
from .cohort_store import CohortStore, table_of
from .households_cohort import VALUE_OF_LIFE_YEARS_OF_INCOME, Cohort
from .labour_offer_rows import LabourOfferRows


def hours_left_by_tile(tiles: Sequence[str], hours_per_year: float, levy_hours_per_worker: float, levied_tiles: Iterable[str]) -> list:
    """The hours the workers of each tile have to offer: the year's, less the levy on a levied tile (never below zero)."""
    levied = set(levied_tiles)
    levy = max(0.0, levy_hours_per_worker)
    return [max(0.0, hours_per_year - levy) if tile in levied else hours_per_year for tile in tiles]


def write_cohort_offers(rows: LabourOfferRows, cohorts: Union[CohortStore, Iterable[Cohort]],
                        people_in_areas: Callable[[Sequence[str]], Tuple[np.ndarray, Sequence[str]]],
                        labour_area_of_tile: Callable[[str], str],
                        subsistence_by_tile: Mapping[str, float], hours_per_year: float, danger_by_trade: Mapping[str, float],
                        levy_hours_per_worker: float = 0.0, levied_tiles: Iterable[str] = (),
                        value_of_life: Optional[float] = None) -> None:
    """Append every cohort's offers to `rows`. `cohorts` is the cohort table (or cohorts, made a table here); they are taken by id;
    `people_in_areas(areas)` is the working people of the labour areas as (people per area and trade, the trade names in name order); a
    trade's hours are offered in the labour area `labour_area_of_tile(tile)` of the tile."""
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
    chosen_tile = tile_of_row[kept]
    first_seen = chosen_tile[np.sort(np.unique(chosen_tile, return_index=True)[1])]       # an area is made on its first cohort, in cohort id order
    area_names = list(dict.fromkeys(area_of_tile[number] for number in first_seen.tolist()))
    area_place = {area: place for place, area in enumerate(area_names)}
    area_of_tile_number = np.zeros(int(chosen_tile.max()) + 1, dtype=np.int64)
    area_of_tile_number[first_seen] = [area_place[area_of_tile[number]] for number in first_seen.tolist()]
    area_index = area_of_tile_number[chosen_tile]
    tile_working = working_of_tile[chosen_tile]
    working = store.column("working_people")[order][kept]
    share = np.where(tile_working > 0.0, working / np.where(tile_working > 0.0, tile_working, 1.0), 0.0)
    subsistence = np.array([subsistence_by_tile.get(tile, 0.0) for tile in tile_names], dtype=np.float64)
    chosen_ids = [store.ids[row] for row in order[kept].tolist()]
    people, trade_names = people_in_areas(area_names)
    trade_risk = np.array([1.0 + max(0.0, danger_by_trade.get(trade, 0.0)) * value_of_life for trade in trade_names], dtype=np.float64)
    _append_rows(rows, chosen_ids, area_of_tile, chosen_tile, np.asarray(trade_names), people, trade_risk, area_index, share, left[kept],
                 subsistence[chosen_tile])


def _append_rows(rows, chosen_ids, area_of_tile, chosen_tile, trade_names, people, trade_risk, area_index, share, hours_left, subsistence) -> None:
    """Expand each cohort over its area's trades and keep the offers that hold a share of someone. `people` has a row per area and a
    column per trade name; the trades of an area are those with people, in name order."""
    held = people > 0.0
    lengths = held.sum(axis=1).astype(np.int64)
    starts = np.cumsum(lengths) - lengths
    _area_place, trade_place = np.nonzero(held)
    trade = rows.trades.numbers(trade_names[trade_place].tolist())
    flat_people = people[held]
    factor = trade_risk[trade_place]
    per_cohort = lengths[area_index]
    row_cohort = np.repeat(np.arange(len(chosen_ids), dtype=np.int64), per_cohort)
    source = starts[area_index][row_cohort] + (np.arange(len(row_cohort), dtype=np.int64)
                                               - np.repeat(np.cumsum(per_cohort) - per_cohort, per_cohort))
    workers = flat_people[source] * share[row_cohort]
    keep = np.flatnonzero(workers > 0.0)
    if not len(keep):
        return
    row_cohort, source, workers = row_cohort[keep], source[keep], workers[keep]
    hours = workers * hours_left[row_cohort]
    wage = subsistence[row_cohort] / hours_left[row_cohort] * factor[source]
    worker = rows.workers.numbers([chosen_ids[each] for each in row_cohort.tolist()])
    rows.add_rows(worker, trade[source], _area_numbers(rows, area_of_tile, chosen_tile, row_cohort, trade[source]), hours, wage)


def _area_numbers(rows, area_of_tile, chosen_tile, row_cohort, trade) -> np.ndarray:
    """The number of the area each offer is made in: a trade's hours are offered in its tile's labour area. Areas new to `rows` are
    numbered in the order the sorted (trade, tile) pairs reach them, tiles taken in the order the cohorts name them."""
    appearance = chosen_tile[np.sort(np.unique(chosen_tile, return_index=True)[1])]
    rank = np.zeros(int(chosen_tile.max()) + 1, dtype=np.int64)
    rank[appearance] = np.arange(len(appearance))
    key = trade * len(appearance) + rank[chosen_tile][row_cohort]
    distinct = np.unique(key)
    ranks = distinct % len(appearance)
    tile_first_seen = appearance[ranks[np.sort(np.unique(ranks, return_index=True)[1])]]
    number_of_tile = np.zeros(len(rank), dtype=np.int64)
    number_of_tile[tile_first_seen] = rows.areas.numbers([area_of_tile[tile] for tile in tile_first_seen.tolist()])
    return number_of_tile[chosen_tile][row_cohort]
