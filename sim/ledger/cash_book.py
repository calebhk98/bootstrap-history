"""A seat's cash book: every movement of its purse, by cause.

The ledger's seat account is the only writer of the purse and calls `record`, so opening cash plus the open
period's entries is always the cash in hand. The yearly snapshot closes the period; the last few closed
periods stay, so a save holds a bounded history however long the game runs. Every function takes the seat's
cash state (`LedgerSeat`) and, where it needs the cash in hand, the purse's balance.
"""
from collections.abc import Mapping

PERIODS_KEPT = 6   # closed years kept in a save


def _parts(purpose, amount):
    """A label, or a mapping of label to share when one payment covers several things."""
    return dict(purpose) if isinstance(purpose, Mapping) else {purpose: amount}


def record(cash, direction, amount, purpose):
    """Enter a movement of `amount` (direction +1 in, -1 out) under its cause or causes.

    A mapping purpose gives each cause's own signed part, so one posting can carry income and costs.
    """
    for label, part in _parts(purpose, amount).items():
        if part:
            cash.cash_flow[label] = cash.cash_flow.get(label, 0.0) + direction * part


def opening(cash, balance):
    """Cash at the start of the open period."""
    if cash.cash_mark is not None:
        return cash.cash_mark
    return balance - sum(cash.cash_flow.values())


def unaccounted(cash, balance):
    """Cash in hand less opening cash and the open period's entries: zero when nothing bypassed the ledger."""
    return balance - (opening(cash, balance) + sum(cash.cash_flow.values()))


def close_period(cash, balance, year):
    """End the open period (the yearly snapshot calls this) and start the next from today's cash."""
    cash.cash_periods.append({"year": year, "opening": opening(cash, balance),
                              "closing": balance, "causes": dict(cash.cash_flow)})
    del cash.cash_periods[:-PERIODS_KEPT]
    cash.cash_flow = {}
    cash.cash_mark = balance


def causes_since(cash, year):
    """Cash moved by cause since the snapshot of `year` (all kept periods when `year` is None)."""
    totals = {}
    entries = [period["causes"] for period in cash.cash_periods
               if year is None or period["year"] > year]
    for causes in entries + [cash.cash_flow]:
        for cause, amount in causes.items():
            totals[cause] = totals.get(cause, 0.0) + amount
    return totals


def book(cash, balance, year):
    """The open period, and the closed ones before it, newest last."""
    return {"year": year, "opening": round(opening(cash, balance), 1),
            "closing": round(balance, 1),
            "causes": {cause: round(amount, 1) for cause, amount in sorted(cash.cash_flow.items())},
            "earlier_years": [{"year": period["year"], "opening": round(period["opening"], 1),
                               "closing": round(period["closing"], 1),
                               "causes": {cause: round(amount, 1)
                                          for cause, amount in sorted(period["causes"].items())}}
                              for period in cash.cash_periods]}
