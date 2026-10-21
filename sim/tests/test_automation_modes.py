"""Complaint 421: `auto_hire` has a replace-only mode that hires only for staff lost.

The replace-only rule is tested on a stand-in for the household (`replace_lost_staff`) and the typed switch is parsed
on its own. The mode on a game, the policy switch and the mine order id from audit row to working are the named
scenarios in test_automation_modes_scenario."""
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.engine.staff_replacement import REPLACE_ONLY, replace_lost_staff
from sim.ui.proto.typed import parse_typed

def household_that(refuses=()):
    """A household, labour that takes on whole people (refusing the trades named) and an empty audit."""
    household = SimpleNamespace(capital=1000.0, employees={}, automation_audit=[])

    def hire_buying_room(trade, count):
        if trade in refuses:
            return False, "no room for %s" % trade
        household.employees[trade] = household.employees.get(trade, 0.0) + count
        household.capital -= 10.0 * count
        return True, None

    return SimpleNamespace(state=SimpleNamespace(household=household, scenario=SimpleNamespace(year=100)),
                           labour=SimpleNamespace(hire_buying_room=hire_buying_room))


# ---- replace-only restores what was lost and never more -----------------------------------------
nobody_lost = household_that()
replace_lost_staff(nobody_lost, {})
check("replace-only hires nobody when nobody was lost",
      not nobody_lost.state.household.employees and not nobody_lost.state.household.automation_audit)

lossy = household_that()
replace_lost_staff(lossy, {"artisan": 6, "scholar": 1})
replaced = lossy.state.household.automation_audit
check("replace-only rehires each trade it lost, exactly as many, one row each",
      lossy.state.household.employees == {"artisan": 6.0, "scholar": 1.0}
      and sorted(each["what"] for each in replaced) == ["1 scholar", "6 artisan"] and all(each["action"] == "replace" for each in replaced),
      (lossy.state.household.employees, replaced))
check("each row costs what the hire cost", sorted(each["cost"] for each in replaced) == [10.0, 60.0], replaced)
check("the audit row names the mode", all("replace-only" in each["reason"] for each in replaced), replaced)

refused = household_that(refuses=("scholar",))
replace_lost_staff(refused, {"artisan": 2, "scholar": 1})
skips = [each for each in refused.state.household.automation_audit if each["action"] == "skipped"]
# presentation: the skip row carries the refusal's wording
check("a refused rehire is recorded as a skipped action with the refusal, and the other trades are still rehired",
      refused.state.household.employees == {"artisan": 2.0} and len(skips) == 1 and skips[0]["what"] == "replace 1 scholar"
      and "no room for scholar" in skips[0]["reason"], refused.state.household.automation_audit)

# ---- the switch is typed and parsed
check("typed 'policy auto_hire replace' parses",
      parse_typed("policy auto_hire replace")[0] == {"cmd": "policy", "set": {"auto_hire": REPLACE_ONLY}},
      parse_typed("policy auto_hire replace"))
check("another policy refuses 'replace'", parse_typed("policy auto_mine replace")[0] is None)


