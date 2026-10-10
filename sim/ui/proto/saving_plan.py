"""An actor's planned project and savings target, and the year it becomes affordable (Complaints/294).

One function builds the plan; the `saving` reply and the `stuck` row both read it.
"""

import math
from sim.engine.ui_port import money_text, tagged


def saving_plan(sim):
    """The standing plan as a dict, or None when the household is not saving for anything."""
    household = sim.state.household
    node_id = household.saving_for
    if not node_id:
        return None
    target = household.saving_target
    cash = sim.capital
    income = sim.recurring_net()
    if cash >= target:
        year_affordable = sim.year
    elif income > 0:
        year_affordable = sim.year + int(math.ceil((target - cash) / income))
    else:
        year_affordable = None
    return tagged({"id": node_id, "target": round(target, 1), "cash": round(cash, 1),
                   "net_income_per_year": round(income, 1), "year_affordable": year_affordable},
                  target="money:civ_coin")


def saving_reason(sim):
    """The `stuck` row for the plan, or None."""
    plan = saving_plan(sim)
    if plan is None:
        return None
    when = ("it is in hand now" if plan["year_affordable"] == sim.year
            else "at the current net income of %s a year that is %s"
                 % (money_text(plan["net_income_per_year"], sim, grouped=True),
                    "the year %d" % plan["year_affordable"] if plan["year_affordable"] is not None
                    else "never: income does not cover your costs"))
    return {"what": "saving for %s" % plan["id"], "kind": "saving",
            "why": "you are putting money by on purpose: %s target, %s in hand; %s"
                   % (money_text(plan["target"], sim, grouped=True),
                      money_text(plan["cash"], sim, grouped=True), when)}
