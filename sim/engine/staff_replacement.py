"""The replace-only mode of `auto_hire`: hire back the people lost this year, never grow the staff."""
from . import automation_audit

REPLACE_ONLY = "replace"


def replace_lost_staff(sim, lost):
    """Hire each trade back up to the people it lost to attrition this year, through `hire` so every rule a
    player meets applies; a refusal is recorded as a skipped action. `lost` is {trade: people}."""
    household = sim.state.household
    for trade, people in sorted(lost.items()):
        before = household.capital
        have = household.employees.get(trade, 0.0)
        hired, refusal = sim.labour.hire(trade, int(people))
        if not hired:
            automation_audit.record_skip(sim, "auto_hire", "replace %d %s" % (people, trade),
                                         "replace-only mode: " + str(refusal))
            continue
        found = round(household.employees.get(trade, 0.0) - have)
        automation_audit.record(sim, "auto_hire", "replace", "%d %s" % (found, trade),
                                "replace-only mode: %d lost this year, none hired beyond that" % people, before)
