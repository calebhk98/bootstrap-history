"""The founder's cash book: every movement of the purse, by cause.

`HouseholdState.credit` and `.debit` are the only writers of the purse and call
`record`, so opening cash plus the open period's entries is always the cash in
hand. The yearly snapshot closes the period; the last few closed periods stay,
so a save holds a bounded history however long the game runs.
"""
from collections.abc import Mapping

PERIODS_KEPT = 6   # closed years kept in a save


def _parts(purpose, amount):
    """A label, or a mapping of label to share when one payment covers several things."""
    return dict(purpose) if isinstance(purpose, Mapping) else {purpose: amount}


def record(household, direction, amount, purpose):
    """Enter a movement of `amount` (direction +1 in, -1 out) under its cause or causes.

    A mapping purpose gives each cause's own signed part, so one posting can carry income and costs.
    """
    for label, part in _parts(purpose, amount).items():
        if part:
            household.cash_flow[label] = household.cash_flow.get(label, 0.0) + direction * part


def opening(household):
    """Cash at the start of the open period."""
    if household.cash_mark is not None:
        return household.cash_mark
    return household.capital - sum(household.cash_flow.values())


def unaccounted(sim):
    """Cash in hand less opening cash and the open period's entries: zero when nothing bypassed the ledger."""
    household = sim.state.household
    return household.capital - (opening(household) + sum(household.cash_flow.values()))


def close_period(sim):
    """End the open period (the yearly snapshot calls this) and start the next from today's cash."""
    household = sim.state.household
    household.cash_periods.append({"year": sim.year, "opening": opening(household),
                                   "closing": household.capital, "causes": dict(household.cash_flow)})
    del household.cash_periods[:-PERIODS_KEPT]
    household.cash_flow = {}
    household.cash_mark = household.capital


def causes_since(sim, year):
    """Cash moved by cause since the snapshot of `year` (all kept periods when `year` is None)."""
    household = sim.state.household
    totals = {}
    entries = [period["causes"] for period in household.cash_periods
               if year is None or period["year"] > year]
    for causes in entries + [household.cash_flow]:
        for cause, amount in causes.items():
            totals[cause] = totals.get(cause, 0.0) + amount
    return totals


def book(sim):
    """The open period, and the closed ones before it, newest last."""
    household = sim.state.household
    return {"year": sim.year, "opening": round(opening(household), 1),
            "closing": round(household.capital, 1),
            "causes": {cause: round(amount, 1) for cause, amount in sorted(household.cash_flow.items())},
            "earlier_years": [{"year": period["year"], "opening": round(period["opening"], 1),
                               "closing": round(period["closing"], 1),
                               "causes": {cause: round(amount, 1)
                                          for cause, amount in sorted(period["causes"].items())}}
                              for period in household.cash_periods]}
