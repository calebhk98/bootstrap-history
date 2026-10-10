"""Why a number moved: (cause, signed amount) rows for wages, state notice and concern closures (Complaint 420).

Closures and openings are written where they happen; a wage shock is written by the hazard that
caused it. Closing the yearly period (the snapshot calls it) stamps those rows with the year and adds
what the year's change leaves over: the wage index change not named by a shock, and the change in
state notice split by what moved it (the state, headcount, wealth, eminence, defiance). Only the last few
years are kept, so a save holds a bounded history.
"""

from sim.agents.api import demand_answer

YEARS_KEPT = 5
ROWS_KEPT = 400   # a hard cap for runs that never close a period
WAGE = "wage"
NOTICE = "notice"
STATE_CAUSE = "state capacity"
SCALE_CAUSES = ("headcount", "wealth", "eminence", "defiance")
UNSHOCKED_WAGE_CAUSE = "births and deaths outside dated shocks"


def record(sim, kind, subject, cause, amount, **extra):
    """Append one row to the open period; its year is stamped when the period closes."""
    row = {"year": None, "kind": kind, "subject": subject, "cause": cause, "amount": amount, **extra}
    kept = sim.state.household.cause_rows
    kept.append(row)
    del kept[:-ROWS_KEPT]
    return row


def concern_effect(sim, node_id):
    """What running a concern is worth a year, from its node: the effect line of an opening or closure."""
    node = sim.nodes[node_id]
    return {"revenue": node["rev"], "upkeep": node["up"]}


def record_concern(sim, kind, node_id, cause):
    return record(sim, kind, node_id, cause, 1.0, **concern_effect(sim, node_id))


def record_wage_shock(sim, cause, index_before):
    """A shock moved the wage index from `index_before` to now; name it."""
    return record(sim, WAGE, "wage_index", cause, sim.labour.market.wage_index_change(index_before))


def _readings(sim):
    household = sim.state.household
    return {"wage_index": sim.labour.market.wage_index(), "state_capacity": sim.state_capacity,
            "headcount": sim.labour.headcount(), "wealth": demand_answer.visible_wealth(household.capital, household.concealed),
            "eminence": household.eminence, "defiance": household.defiance}


def _notice_steps(sim, before, after):
    """The notice change, one input at a time so the parts add to it exactly."""
    inputs = dict(before)
    capacity = before["state_capacity"]

    def level():
        return capacity * sim.visible_scale(inputs["headcount"], inputs["wealth"], inputs["eminence"], inputs["defiance"])

    parts = {}
    last = level()
    capacity = after["state_capacity"]
    now = level()
    parts[STATE_CAUSE], last = now - last, now
    for name in SCALE_CAUSES:
        inputs[name] = after[name]
        now = level()
        parts[name], last = now - last, now
    return parts


def close_period(sim):
    """End the open period: stamp its rows, add the year's derived rows, drop rows past the window."""
    household = sim.state.household
    now = _readings(sim)
    before = household.cause_mark
    if before is not None:
        named = sum(row["amount"] for row in household.cause_rows
                    if row["year"] is None and row["kind"] == WAGE)
        residual = now["wage_index"] - before["wage_index"] - named
        if residual:
            record(sim, WAGE, "wage_index", UNSHOCKED_WAGE_CAUSE, residual)
        for cause, part in _notice_steps(sim, before, now).items():
            if part:
                record(sim, NOTICE, "state_notice", cause, part)
    for row in household.cause_rows:
        if row["year"] is None:
            row["year"] = sim.year
    household.cause_rows = [row for row in household.cause_rows if row["year"] > sim.year - YEARS_KEPT]
    household.cause_mark = now


def rows(sim, kind=None, years=None):
    """Rows of one kind (all kinds when None) from the latest `years` years, oldest first; the open period counts as this year."""
    first_year = None if years is None else sim.year - max(1, int(years))
    found = []
    for row in sim.state.household.cause_rows:
        year = sim.year if row["year"] is None else row["year"]
        if (kind is None or row["kind"] == kind) and (first_year is None or year >= first_year):
            found.append({**row, "year": year})
    return found


def causes_since(sim, kind, year):
    """Signed amount per cause for `kind` since the snapshot of `year` (all kept rows when `year` is None)."""
    totals = {}
    for row in sim.state.household.cause_rows:
        if row["kind"] == kind and (year is None or row["year"] is None or row["year"] > year):
            totals[row["cause"]] = totals.get(row["cause"], 0.0) + row["amount"]
    return totals
