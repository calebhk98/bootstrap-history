"""Why a number moved: (cause, signed amount) rows for wages, state notice and concern closures, as plain values.

Rows are written where things happen; closing the yearly period stamps them with the year and adds what the year's change
leaves over: the wage index change no shock named, and the change in state notice split by what moved it. Only the last few
years are kept, so a save holds a bounded history."""
from typing import Any, Callable, Dict, List, Optional

YEARS_KEPT = 5
ROWS_KEPT = 400   # a hard cap for runs that never close a period
WAGE = "wage"
NOTICE = "notice"
STATE_CAUSE = "state reach"
SCALE_CAUSES = ("headcount", "wealth", "eminence", "defiance")
UNSHOCKED_WAGE_CAUSE = "births and deaths outside dated shocks"

Row = Dict[str, Any]


def append_row(rows: List[Row], kind: str, subject: str, cause: str, amount: float, extra: Optional[Dict[str, Any]] = None) -> Row:
    """Append one row to the open period (its year is stamped when the period closes); the oldest go past the cap."""
    row = {"year": None, "kind": kind, "subject": subject, "cause": cause, "amount": amount, **(extra or {})}
    rows.append(row)
    del rows[:-ROWS_KEPT]
    return row


def notice_steps(before: Dict[str, float], after: Dict[str, float], notice_of: Callable[..., float]) -> Dict[str, float]:
    """The notice change one input at a time, so the parts add to it exactly. `notice_of(capacity, headcount, wealth,
    eminence, defiance)` is the notice at those readings."""
    inputs = dict(before)

    def level(capacity: float) -> float:
        return notice_of(capacity, inputs["headcount"], inputs["wealth"], inputs["eminence"], inputs["defiance"])

    parts = {}
    last = level(before["state_reach"])
    now = level(after["state_reach"])
    parts[STATE_CAUSE], last = now - last, now
    for name in SCALE_CAUSES:
        inputs[name] = after[name]
        now = level(after["state_reach"])
        parts[name], last = now - last, now
    return parts


def close_period(rows: List[Row], mark: Optional[Dict[str, float]], now: Dict[str, float], year: int,
                 notice_of: Callable[..., float]) -> List[Row]:
    """End the open period: add the year's derived rows (when there is a reading to measure from), stamp the open rows with
    `year`, and return the rows within the years kept."""
    if mark is not None:
        named = sum(row["amount"] for row in rows if row["year"] is None and row["kind"] == WAGE)
        residual = now["wage_index"] - mark["wage_index"] - named
        if residual:
            append_row(rows, WAGE, "wage_index", UNSHOCKED_WAGE_CAUSE, residual)
        for cause, part in notice_steps(mark, now, notice_of).items():
            if part:
                append_row(rows, NOTICE, "state_notice", cause, part)
    for row in rows:
        if row["year"] is None:
            row["year"] = year
    return [row for row in rows if row["year"] > year - YEARS_KEPT]


def rows_of(rows: List[Row], year: int, kind: Optional[str] = None, years: Optional[int] = None) -> List[Row]:
    """Rows of one kind (all kinds when None) from the latest `years` years, oldest first; the open period counts as `year`."""
    first_year = None if years is None else year - max(1, int(years))
    found = []
    for row in rows:
        row_year = year if row["year"] is None else row["year"]
        if (kind is None or row["kind"] == kind) and (first_year is None or row_year >= first_year):
            found.append({**row, "year": row_year})
    return found


def totals_since(rows: List[Row], kind: str, year: Optional[int]) -> Dict[str, float]:
    """Signed amount per cause for `kind` since the snapshot of `year` (all kept rows when `year` is None)."""
    totals: Dict[str, float] = {}
    for row in rows:
        if row["kind"] == kind and (year is None or row["year"] is None or row["year"] > year):
            totals[row["cause"]] = totals.get(row["cause"], 0.0) + row["amount"]
    return totals
