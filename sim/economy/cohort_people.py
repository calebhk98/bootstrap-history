"""The cohorts' people as columns: the totals by tile and the rescaling of every cohort to demography's count.

`total_by_tile` adds a float column by tile in table order, left to right from zero, as a loop over the cohorts did.
`follow_population` rescales each tile's cohorts to the tile's people and working-age people (`economy._follow_population`) in one
block: the new people and working people of every cohort whose figures move are written to the columns together."""
from typing import Dict, Mapping, Optional

import numpy as np

from .cohort_rows import FLOAT_BIT
from .cohort_store import CohortStore, typed_flags
from .household_offer_kernels import sum_in_order_by_group


def total_by_tile(store: CohortStore, name: str, where: Optional[np.ndarray] = None) -> np.ndarray:
    """The float column `name` added up by tile number (`store.names["tiles"]`), rows in table order; the cohorts left out by the
    flag `where` (one per row) add nothing. A tile with no cohort has a zero."""
    values = store.column(name)
    if where is not None:
        values = np.where(where, values, 0.0)
    return sum_in_order_by_group(np.ascontiguousarray(store.tile_numbers()), len(store.names["tiles"]), np.ascontiguousarray(values))


def _per_tile(store: CohortStore, wanted: Mapping[str, float]):
    """(the figure of each tile number named in `wanted`, NaN for a tile not named; whether it is a numpy float)."""
    names = store.names["tiles"].name_list
    found = np.full(len(names), np.nan)
    typed = np.zeros(len(names), dtype=np.bool_)
    for number, tile in enumerate(names):
        if tile in wanted:
            found[number] = wanted[tile]
            typed[number] = isinstance(wanted[tile], np.floating)
    return found, typed


def follow_population(store: CohortStore, people_by_tile: Mapping[str, float], working_by_tile: Mapping[str, float]) -> None:
    """Each tile's cohorts take its people (`people_by_tile`, a tile not named keeps its people) in proportion to the people they hold,
    and its working-age people (`working_by_tile`, a tile not named scales its working people as its people) in proportion to the
    working people they hold; a tile with no working people yet shares its working-age people by people. A tile whose cohorts hold
    nobody is left alone. A cohort whose figures move is written, working people never above its people."""
    tile = np.ascontiguousarray(store.tile_numbers())
    people, working = store.column("people"), store.column("working_people")
    people_now = total_by_tile(store, "people")[tile]
    working_now = total_by_tile(store, "working_people")[tile]
    after_tile, after_typed = _per_tile(store, people_by_tile)
    wanted_tile, wanted_typed = _per_tile(store, working_by_tile)
    after = np.where(np.isnan(after_tile[tile]), people_now, after_tile[tile])
    wanted = wanted_tile[tile]
    has_wanted = ~np.isnan(wanted)
    alive = people_now > 0.0
    with np.errstate(divide="ignore", invalid="ignore"):
        new_people = people * after / people_now
        scaled_by_people = working * after / people_now
        scaled_by_wanted = working * wanted / working_now
        shared_by_people = wanted * people / people_now
    new_working = np.where(~has_wanted, scaled_by_people, np.where(working_now > 0.0, scaled_by_wanted, shared_by_people))
    moved = alive & ((new_people != people) | (new_working != working))
    rows = np.nonzero(moved)[0]
    if not len(rows):
        return
    kinds = store.table.numpy_typed[rows]
    after_numpy = np.where(np.isnan(after_tile[tile[rows]]), (kinds & FLOAT_BIT["people"]) != 0, after_typed[tile[rows]])
    people_numpy = ((kinds & FLOAT_BIT["people"]) != 0) | after_numpy
    working_numpy = np.where(~has_wanted[rows], ((kinds & FLOAT_BIT["working_people"]) != 0) | after_numpy,
                             np.where(working_now[rows] > 0.0, ((kinds & FLOAT_BIT["working_people"]) != 0) | wanted_typed[tile[rows]],
                                      wanted_typed[tile[rows]] | ((kinds & FLOAT_BIT["people"]) != 0)))
    capped = np.minimum(new_working[rows], new_people[rows])
    capped_numpy = np.where(new_people[rows] < new_working[rows], people_numpy, working_numpy)      # `min` hands back the one it chose
    store.set_rows("people", rows, new_people[rows], typed=people_numpy)
    store.set_rows("working_people", rows, capped, typed=capped_numpy)


def hunger_by_tile(store: CohortStore, hunger_need: str) -> Dict[str, float]:
    """{tile: need units short of the hunger floor, added over the tile's cohorts in table order}, for the tiles where some cohort is short."""
    short = store.unmet_of(hunger_need)
    totals = sum_in_order_by_group(np.ascontiguousarray(store.tile_numbers()), len(store.names["tiles"]),
                                   np.ascontiguousarray(np.where(short > 0.0, short, 0.0))).tolist()
    names = store.names["tiles"].name_list
    short_tiles = np.unique(store.tile_numbers()[short > 0.0])
    return {names[number]: totals[number] for number in short_tiles.tolist()}


def apply_work_plans(store: CohortStore, plans: Mapping[str, tuple]) -> None:
    """Each cohort's household-work plan (`plans`: id -> (hired hours a person, own hours, grains bought milled)) is stored where it
    differs from what the cohort holds: its hired hours a person and its grains bought milled (the own hours are not stored)."""
    ids = list(plans)
    rows = store.rows_of(ids)
    hired = [plans[each][0] for each in ids]
    milled = [tuple(plans[each][2]) for each in ids]
    changed = np.array(hired, dtype=np.float64) != store.column("hired_work_per_person")[rows]
    counts = np.fromiter(map(len, milled), dtype=np.int64, count=len(milled))
    for place in np.nonzero((counts != store.table.milled_count[rows]) | (counts > 0))[0].tolist():     # only a cohort that mills is compared
        changed[place] |= milled[place] != store.milled_of(int(rows[place]))
    places = np.nonzero(changed)[0]
    if not len(places):
        return
    store.set_rows("hired_work_per_person", rows[places], np.array([hired[each] for each in places.tolist()], dtype=np.float64),
                   typed=typed_flags([hired[each] for each in places.tolist()]))
    store.write_milled(rows[places], [milled[each] for each in places.tolist()])

