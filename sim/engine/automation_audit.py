"""The audit trail of what automation did: one row per action, kept for the last few years (Complaints/91).

Each row is {"year", "policy", "action", "what", "reason", "cost"}, plus "ids" when it names concerns. `cost` is the
change in capital across the action, measured where the action ran, so it
is the same money the books moved. The `automation` command and the
yearly log read the same rows.
"""

YEARS_KEPT = 5


def begin_year(sim):
    """Drop rows older than the years kept; called once at the start of a step."""
    household = sim.state.household
    household.automation_audit = [row for row in household.automation_audit
                                  if row["year"] > sim.state.scenario.year - YEARS_KEPT]


def record(sim, policy, action, what, reason, capital_before, **extra):
    """Append one row; cost is what capital fell by since `capital_before`."""
    household = sim.state.household
    row = {"year": sim.state.scenario.year, "policy": policy, "action": action,
           "what": what, "reason": reason, "cost": round(capital_before - household.capital, 1), **extra}
    household.automation_audit.append(row)
    return row


def rows(sim, years=1):
    """The rows from the latest `years` years that were played, oldest first."""
    first_year = sim.state.scenario.year - max(1, int(years))
    return [row for row in sim.state.household.automation_audit if row["year"] >= first_year]


def record_skip(sim, policy, what, reason):
    """Append a row for something automation looked at and did not do, with the refusal reason."""
    return record(sim, policy, "skipped", what, reason, sim.state.household.capital)


def order_id(policy, subject, year):
    """The id an order carries from its audit row to what it set going (a mine tranche, then the working)."""
    return "%s:%s:%d" % (policy, subject, year)
