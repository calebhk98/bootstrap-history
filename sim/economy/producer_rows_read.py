"""A producer's whole row read as a plain tuple, many rows in one block read, for the rules that read a producer's fields by name
(`producers.plan`, `practice.recipe_for`) and are not yet kernels.

`ProducerFields` has the field names of `Producer` and the values `ProducerStore.at` would hold for the same row (a numpy float where
the field was written as one, `None` for a land cap or staffed runs that is absent), but nothing in the year loop builds a `Producer`."""
from typing import Iterable, List, NamedTuple, Optional

import numpy as np

from .producer_blocks import expected_prices_of, figures_of

_SCALARS = ("capacity_runs", "yield_factor", "years_of_loss", "cash_target", "expected_sales", "last_runs", "land_rent_per_run",
            "workshops", "idle_years")
_INTEGERS = ("years_of_loss", "workshops", "idle_years")


class ProducerFields(NamedTuple):
    agent_id: str
    owner: str
    recipe_id: str
    tile: str
    capacity_runs: float
    yield_factor: float
    expected_prices: dict
    years_of_loss: int
    cash_target: float
    expected_sales: float
    last_runs: float
    land_rent_per_run: float
    land_run_cap: Optional[float]
    workshops: int
    net_earnings_history: tuple
    revenue_history: tuple
    idle_years: int
    staffed_runs: Optional[float]
    crew_runs: dict


def _histories(values: np.ndarray, counts: np.ndarray) -> List[tuple]:
    """Each row's first `count` places of the wide column, as a tuple."""
    return [tuple(values[place, :count].tolist()) for place, count in enumerate(counts.tolist())]


def _optional(figures: list) -> list:
    """The figures with NaN (the column's mark for an absent field) as None."""
    return [None if figure != figure else figure for figure in figures]


def fields_of(store, rows: Iterable[int]) -> List[ProducerFields]:
    """The fields of the producer in each row (`ProducerStore.at(row)` field by field), read as columns."""
    rows = np.fromiter(rows, dtype=np.int64)
    table, names = store.table, store.names
    scalars = {name: getattr(table, name)[rows].tolist() if name in _INTEGERS else figures_of(store, name, rows) for name in _SCALARS}
    owners, recipes, tiles = (names[kind].name_list for kind in ("owners", "recipes", "tiles"))
    expected = expected_prices_of(store, rows)
    land_caps, staffed = _optional(figures_of(store, "land_run_cap", rows)), _optional(figures_of(store, "staffed_runs", rows))
    earnings = _histories(table.earnings_history[rows], table.earnings_count[rows])
    revenue = _histories(table.revenue_history[rows], table.revenue_count[rows])
    crewed = (table.crew_count[rows] > 0).tolist()
    owner_of, recipe_of, tile_of = table.owner[rows].tolist(), table.recipe[rows].tolist(), table.tile[rows].tolist()
    return [ProducerFields(
        store.ids[row], owners[owner_of[place]], recipes[recipe_of[place]], tiles[tile_of[place]], scalars["capacity_runs"][place],
        scalars["yield_factor"][place], expected[place], scalars["years_of_loss"][place], scalars["cash_target"][place],
        scalars["expected_sales"][place], scalars["last_runs"][place], scalars["land_rent_per_run"][place], land_caps[place],
        scalars["workshops"][place], earnings[place], revenue[place], scalars["idle_years"][place], staffed[place],
        store.crew_of(row) if crewed[place] else {})
        for place, row in enumerate(rows.tolist())]
