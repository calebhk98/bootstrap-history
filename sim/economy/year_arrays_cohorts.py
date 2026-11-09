"""The cohorts' numeric fields as columns, one row per cohort in sorted id order. Cohorts are few and mutable records,
so the columns are read again whole whenever they are asked for (`CohortColumns.build`)."""
from dataclasses import dataclass
from typing import Dict, Mapping, Tuple

import numpy as np

from .cohort_store import CohortStore
from .year_arrays_recipes import Names

NUMERIC_FIELDS = ("people", "working_people", "ownership_share", "expected_inflation", "cash_target",
                  "last_basket_price_level", "last_year_income", "planned_spending", "expected_spending",
                  "expected_floor_cost", "hired_work_per_person")


@dataclass
class CohortColumns:
    ids: Tuple[str, ...]
    row: Dict[str, int]
    tile_row: np.ndarray
    income_class: np.ndarray
    share_wealth: np.ndarray           # NaN: none held yet
    numeric: Dict[str, np.ndarray]     # by field name in NUMERIC_FIELDS

    @classmethod
    def build(cls, cohorts: Mapping[str, object], tiles: Names) -> "CohortColumns":
        """The columns of the cohort table in id order, read as blocks (a plain mapping of cohorts is made a table first)."""
        store = cohorts if isinstance(cohorts, CohortStore) else CohortStore(cohorts)
        order = store.order()
        ids = tuple(store.ids[row] for row in order.tolist())
        numeric = {name: store.column(name)[order] for name in NUMERIC_FIELDS}
        tile_row = np.array([tiles.row[name] for name in store.names["tiles"].name_list], dtype=np.int64)[store.tile_numbers()[order]] \
            if len(order) else np.zeros(0, dtype=np.int64)
        return cls(ids, {each: position for position, each in enumerate(ids)}, tile_row, store.table.income_class[:store.count][order],
                   store.column("share_wealth")[order], numeric)
