"""grow_trade_toward (the yearly auto_hire top-up of one trade): a hire row names the people the market found, not the
people sought; a release row names the people let go; a refusal is a skip only when shut concerns need the hands."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.engine.staff_replacement import grow_trade_toward
from sim.tests import event_stand_in


def world(held, found, accepts=True):
    """A household holding `held` artisans whose market finds only `found` of any number asked; labour rounds a target as is."""
    household = SimpleNamespace(capital=1000.0, employees={"artisan": held}, automation_audit=[])

    def hire_buying_room(trade, count):
        if not accepts:
            return False, "no room"
        household.employees[trade] += min(count, found)
        household.capital -= 10.0 * min(count, found)
        return True, None

    def fire(trade, count):
        household.employees[trade] -= count

    labour = SimpleNamespace(stochastic_round=lambda target: int(target), hire_buying_room=hire_buying_room, fire=fire,
                             supervision_room=lambda: 3.0)
    return event_stand_in.stood_in(SimpleNamespace(
        state=SimpleNamespace(household=household, scenario=SimpleNamespace(year=100)), labour=labour))


partial = world(held=2.0, found=1)
grow_trade_toward(partial, "artisan", 7.0)
rows = partial.state.household.automation_audit
check("a partial hire's row names the people found", [row["what"] for row in rows] == ["1 artisan"], rows)
check("the row's action is hire and its cost is what the hire cost", (rows[0]["action"], rows[0]["cost"]) == ("hire", 10.0), rows)

released = world(held=6.0, found=0)
grow_trade_toward(released, "artisan", 2.0)
rows = released.state.household.automation_audit
check("a target below the staff releases the difference and the row names it",
      released.state.household.employees["artisan"] == 2.0 and [(row["action"], row["what"]) for row in rows] == [("release", "4 artisan")], rows)

steady = world(held=3.0, found=5)
grow_trade_toward(steady, "artisan", 3.6)
check("less than a whole person of change does nothing", steady.state.household.automation_audit == []
      and steady.state.household.employees["artisan"] == 3.0)

refused = world(held=1.0, found=5, accepts=False)
grow_trade_toward(refused, "artisan", 4.0, closure_need=0.5)
check("a refusal is not recorded when shut concerns do not need the hands", refused.state.household.automation_audit == [])
grow_trade_toward(refused, "artisan", 4.0, closure_need=2.0)
rows = refused.state.household.automation_audit
check("a refusal is a skip row when shut concerns need the hands", [(row["action"], row["what"]) for row in rows] == [("skipped", "hire 3 artisan")], rows)
