"""The year's close written into the cohort table's columns in one block (`households_close` makes the figures, this writes them).

`write_close(store, rows, figures)`: for the cohorts in `rows`, each float field named in `figures` takes its list of values (a numpy
float stays one, a None for `share_wealth` is none) and the two mappings take theirs. Nothing is built per cohort: the lists are
turned into columns once each."""
from typing import Dict, List, Mapping, Sequence

import numpy as np

from .cohort_store import CohortStore, typed_flags


def write_close(store: CohortStore, rows: np.ndarray, figures: Mapping[str, Sequence], unmet: List[Dict[str, float]],
                plan: List[Dict[str, float]]) -> None:
    """The cohorts in `rows` take the close's figures: `figures` is {float field: a value for each row}."""
    for name, values in figures.items():
        flags = typed_flags(values)
        floats = np.array([np.nan if value is None else value for value in values], dtype=np.float64) if name == "share_wealth" \
            else np.array(values, dtype=np.float64)
        store.set_rows(name, rows, floats, typed=flags)
    store.write_pairs("unmet", rows, unmet)
    store.write_pairs("plan", rows, plan)
