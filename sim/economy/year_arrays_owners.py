"""Per-producer figures of the year arrays that come from names, read once per distinct name or debt and not once per producer."""
import numpy as np


def eligible_owners(columns, cohorts) -> np.ndarray:
    """Whether each producer's owner is one of `cohorts` (a container of cohort ids), by producer row: the owners' names are tested once
    each, then spread over the producers by the rows' owner numbers."""
    owner_names = columns.store.names["owners"].name_list
    held = np.fromiter((name in cohorts for name in owner_names), dtype=np.bool_, count=len(owner_names))
    return held[columns.owner_number]


def debts_by_row(columns, debts) -> np.ndarray:
    """What each producer owes (`debts`: borrower -> amount), by producer row; zero for a producer that owes nothing. Only the borrowers
    are visited, not every producer."""
    owed = np.zeros(len(columns.ids), dtype=np.float64)
    row_of = columns.row
    for borrower, amount in debts.items():
        row = row_of.get(borrower)
        if row is not None:
            owed[row] = amount
    return owed
