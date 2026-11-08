"""The cohorts' numeric fields as columns, one row per cohort in sorted id order. Cohorts are few and mutable records,
so the columns are read again whole whenever they are asked for (`CohortColumns.build`)."""
from dataclasses import dataclass
from operator import attrgetter
from typing import Dict, Mapping, Tuple

import numpy as np

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
        ids = tuple(sorted(cohorts))
        count = len(ids)
        records = [cohorts[each] for each in ids]
        columns = zip(*map(attrgetter(*NUMERIC_FIELDS), records)) if records else [()] * len(NUMERIC_FIELDS)   # every field of every cohort in one pass
        numeric = {name: np.array(values, dtype=np.float64) for name, values in zip(NUMERIC_FIELDS, columns)}
        wealth = np.array([np.nan if record.share_wealth is None else record.share_wealth for record in records], dtype=np.float64)
        return cls(ids, {each: position for position, each in enumerate(ids)},
                   np.array([tiles.row[record.tile] for record in records], dtype=np.int64),
                   np.array([record.income_class for record in records], dtype=np.int64), wealth, numeric)
