"""The figures the year's goods orders read of a cohort, taken from the cohort table's columns in one block (no `Cohort` is built).

`OrderFigures` carries what `households_orders_pack.kernel_orders`, `households_store.store_offers`, the land bids, the tool bids and the
basket key (`household_work_year.basket_signature`) read: a cohort-like object for those rules, with the same values and scalar types a `Cohort` built from
the row hands back."""
from typing import List, NamedTuple, Optional

import numpy as np

from .cohort_store import CohortStore


class OrderFigures(NamedTuple):
    agent_id: str
    tile: str
    people: float
    hired_work_per_person: float
    milled_grains: tuple
    expected_spending: float
    expected_floor_cost: float
    expected_inflation: float
    cash_target: float
    share_wealth: Optional[float]
    last_year_income: float


def order_figures(store: CohortStore, rows: np.ndarray) -> List[OrderFigures]:
    """The order figures of the cohorts in `rows`, in that order; `share_wealth` is None where the cohort has had no close."""
    names = ("people", "hired_work_per_person", "expected_spending", "expected_floor_cost", "expected_inflation", "cash_target",
             "share_wealth", "last_year_income")
    people, hired, spending, floor_cost, inflation, target, wealth, income = (store.floats(name, rows) for name in names)
    return [OrderFigures(store.ids[row], tile, people[place], hired[place], store.milled_of(row), spending[place], floor_cost[place],
                         inflation[place], target[place], None if wealth[place] != wealth[place] else wealth[place], income[place])
            for place, (row, tile) in enumerate(zip(rows.tolist(), store.tile_names(rows)))]
