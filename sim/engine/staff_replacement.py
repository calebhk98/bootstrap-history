"""The replace-only mode of `auto_hire`: hire back the people lost this year, never grow the staff."""
from sim.reporting.api import RecordAutomation, RecordAutomationSkip
from .staff_phase_rules import hires_needed

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
            sim.send(RecordAutomationSkip("auto_hire", "replace %d %s" % (people, trade), "replace-only mode: " + str(refusal)))
            continue
        found = round(household.employees.get(trade, 0.0) - have)
        sim.send(RecordAutomation("auto_hire", "replace", "%d %s" % (found, trade), "replace-only mode: %d lost this year, none hired beyond that" % people, before))


def grow_trade_toward(sim, trade, want, closure_need=0.0):
    """Hire a trade up to (or release it down to) the whole-person target drawn from `want`, through `hire_buying_room`
    so every rule a player meets applies. A refusal is not an error: it is recorded as a skip when shut concerns need
    the hands. A hire's audit row names the people the market found, which can be fewer than sought."""
    household = sim.state.household
    have = household.employees.get(trade, 0.0)
    change = hires_needed(have, sim.labour.stochastic_round(want))
    if change > 0:
        before = household.capital
        hired, why = sim.labour.hire_buying_room(trade, change)
        if not hired and closure_need >= 1.0:
            sim.send(RecordAutomationSkip("auto_hire", "hire %d %s" % (change, trade), "concerns shut for want of staff need %.1f more: %s" % (closure_need, why)))
        if hired:
            found = round(household.employees.get(trade, 0.0) - have)
            sim.send(RecordAutomation("auto_hire", "hire", "%d %s" % (found, trade), "staff target %.1f against %.1f held, with %.1f supervision room"
                % (want, have, sim.labour.supervision_room()), before))
    elif change < 0:
        before = household.capital
        sim.labour.fire(trade, -change)
        sim.send(RecordAutomation("auto_hire", "release", "%d %s" % (-change, trade), "staff target %.1f is below the %.1f held" % (want, have), before))


GENERIC_STAFF = ("artisan", "scholar")


def replacement_wanted(trade_id, have, taught, drawn_on, target_headcount):
    """The headcount a specialist trade is topped back up to, or None when it is not. Only a trade something draws on
    (a project in hand or an open concern) is replaced, so idle specialists are not paid for decades; of those only a trade
    the household taught is raised to `target_headcount`, and the generic bucket trades are left to the staff target."""
    if trade_id in GENERIC_STAFF or trade_id not in drawn_on:
        return None
    return max(have, target_headcount if taught else 0.0)
