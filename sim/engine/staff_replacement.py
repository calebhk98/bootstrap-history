"""The replace-only mode of `auto_hire`: hire back the people lost this year, never grow the staff."""
from . import automation_audit

REPLACE_ONLY = "replace"
REPLACE_STANCE = "replace"
GROW_STANCE = "grow"


def hire_stance(hire_mode, has_room):
    """What the yearly staff phase does with the auto_hire setting: REPLACE_STANCE (rehire what was lost, nothing
    more), GROW_STANCE (smooth the staff toward capacity) or None (nothing: the setting is off or the credit line
    leaves no room to hire)."""
    if not hire_mode or not has_room:
        return None
    return REPLACE_STANCE if hire_mode == REPLACE_ONLY else GROW_STANCE


def replace_lost_staff(sim, lost):
    """Hire each trade back up to the people it lost to attrition this year, through `hire` so every rule a
    player meets applies; a refusal is recorded as a skipped action. `lost` is {trade: people}."""
    household = sim.state.household
    for trade, people in sorted(lost.items()):
        before = household.capital
        have = household.employees.get(trade, 0.0)
        hired, refusal = sim.labour.hire_buying_room(trade, int(people))
        if not hired:
            automation_audit.record_skip(sim, "auto_hire", "replace %d %s" % (people, trade),
                                         "replace-only mode: " + str(refusal))
            continue
        found = round(household.employees.get(trade, 0.0) - have)
        automation_audit.record(sim, "auto_hire", "replace", "%d %s" % (found, trade),
                                "replace-only mode: %d lost this year, none hired beyond that" % people, before)


GENERIC_STAFF = ("artisan", "scholar")


def replacement_wanted(trade_id, have, taught, drawn_on, target_headcount):
    """The headcount a specialist trade is topped back up to, or None when it is not. Only a trade something draws on
    (a project in hand or an open concern) is replaced, so idle specialists are not paid for decades; of those only a trade
    the household taught is raised to `target_headcount`, and the generic bucket trades are left to the staff target."""
    if trade_id in GENERIC_STAFF or trade_id not in drawn_on:
        return None
    return max(have, target_headcount if taught else 0.0)
