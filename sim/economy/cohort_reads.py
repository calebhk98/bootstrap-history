"""Questions about the cohorts that rules ask without wanting a `Cohort`: read from the columns of the cohort table, or, for a plain
mapping of cohort-like objects (a test's), from the objects, with the same answer."""
from typing import Dict, List, Optional, Set

import numpy as np

from .cohort_store import CohortFigures, CohortStore, table_of


def populated_tiles(cohorts) -> Set[str]:
    """The tiles that have a cohort."""
    if isinstance(cohorts, CohortStore):
        return set(cohorts.tiles_present())
    return {cohort.tile for cohort in cohorts.values()}


def tile_of(cohorts, cohort_id: str) -> Optional[str]:
    """The tile of the cohort, None for an id the mapping does not hold."""
    if isinstance(cohorts, CohortStore):
        return cohorts.tile_of(cohort_id)
    cohort = cohorts.get(cohort_id)
    return None if cohort is None else cohort.tile


def poorest_by_tile(cohorts) -> Dict[str, str]:
    """Tile -> id of its poorest cohort (lowest income class; of equal classes the first in the table's order), tiles in the order
    their first cohort entered."""
    if not isinstance(cohorts, CohortStore):
        found: Dict[str, str] = {}
        for cohort in cohorts.values():
            held = found.get(cohort.tile)
            if held is None or cohort.income_class < cohorts[held].income_class:
                found[cohort.tile] = cohort.agent_id
        return found
    classes = cohorts.table.income_class
    found = {}
    for tile in cohorts.tiles_present():
        rows = cohorts.rows_on_tile(tile)
        found[tile] = cohorts.ids[int(rows[int(np.argmin(classes[rows]))])]     # argmin is the first of equal minima
    return found


def figures_of(cohorts, cohort_id: str) -> Optional[CohortFigures]:
    """The figures of one cohort (id, tile, people, working people, last year's income, hired work, grains milled), None for an id the
    mapping does not hold; no `Cohort` is built."""
    store = table_of(cohorts)
    row = store.row_of.get(cohort_id)
    return None if row is None else store.figures(np.array([row], dtype=np.int64))[0]


def figures_in_id_order(cohorts) -> List[CohortFigures]:
    """The figures of every cohort, in id order. A plain mapping's object (a test's) may carry only the figures its rule reads; the
    others read as nothing."""
    if isinstance(cohorts, CohortStore):
        return cohorts.figures(cohorts.order())
    return [CohortFigures(each.agent_id, each.tile, each.people, getattr(each, "working_people", 0.0), getattr(each, "last_year_income", 0.0),
                          getattr(each, "hired_work_per_person", 0.0), getattr(each, "milled_grains", ()), None)
            for each in sorted(cohorts.values(), key=lambda each: each.agent_id)]


def tiles_by_first_id(cohorts) -> List[str]:
    """Each tile that has a cohort once, in the order the lowest-id cohort of each is met going through the cohorts by id."""
    if isinstance(cohorts, CohortStore):
        return list(dict.fromkeys(cohorts.tile_names(cohorts.order())))
    return list(dict.fromkeys(each.tile for each in sorted(cohorts.values(), key=lambda each: each.agent_id)))
