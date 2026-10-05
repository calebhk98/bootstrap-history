"""Complaint 421: `auto_hire` has a replace-only mode that hires only for staff lost, and a mine ordered by
automation can be traced from its audit row to the tranche that was sunk."""
from .harness import *  # noqa: F401,F403

from sim.ui.proto.typed import parse_typed


def hire_game(mode, attrition):
    game = sim(capital=2_000_000.0, manual=False)
    game.STAFF_ATTRITION_RATE = attrition
    game.state.founder.policy["auto_hire"] = mode
    game.state.household.automation_audit = []
    return game


def rows_of(game, action):
    return [row for row in game.state.household.automation_audit if row["policy"] == "auto_hire" and row["action"] == action]


# ---- growth is the default, replace-only never grows ------------------------------------------
growing = hire_game(True, 0.0)
for _ in range(3):
    growing._step_staff()
check("the default mode grows the staff", sum(growing.state.household.employees.values()) > 0
      and rows_of(growing, "hire"))

steady = hire_game("replace", 0.0)
for _ in range(3):
    steady._step_staff()
check("replace-only hires nobody when nobody was lost",
      not steady.state.household.employees and not rows_of(steady, "hire") and not rows_of(steady, "replace"),
      (steady.state.household.employees, steady.state.household.automation_audit))

# ---- replace-only restores what was lost ------------------------------------------------------
lossy = hire_game("replace", 0.0)
lossy.state.household.employees.update({"artisan": 6.0, "scholar": 1.0})
lossy.labour.resync_pools()
lossy.STAFF_ATTRITION_RATE = 1.0
lossy._step_staff()
replaced = rows_of(lossy, "replace")
check("replace-only rehires the trades it lost, one row each", replaced and {row["what"].split()[-1] for row in replaced} >= {"artisan"},
      (lossy.state.household.employees, lossy.state.household.automation_audit))
check("it never hires beyond what was lost", lossy.state.household.employees.get("artisan", 0.0) <= 6.0
      and lossy.state.household.employees.get("scholar", 0.0) <= 1.0, lossy.state.household.employees)
check("the audit row names the mode", all("replace-only" in row["reason"] for row in replaced), replaced)

# ---- the switch --------------------------------------------------------------------------------
switch = hire_game(True, 0.0)
reply = S._agent_dispatch(switch, NODES, {"cmd": "policy", "set": {"auto_hire": "replace"}})
check("the policy command sets the replace-only mode", reply["ok"] and switch.policy["auto_hire"] == "replace", reply)
reply = S._agent_dispatch(switch, NODES, {"cmd": "policy", "set": {"auto_hire": "off"}})
check("off is still off", reply["ok"] and switch.policy["auto_hire"] is False, reply)
check("typed 'policy auto_hire replace' parses",
      parse_typed("policy auto_hire replace")[0] == {"cmd": "policy", "set": {"auto_hire": "replace"}},
      parse_typed("policy auto_hire replace"))
check("another policy refuses 'replace'", parse_typed("policy auto_mine replace")[0] is None)

# ---- a mine's tranche is tied to the row that ordered it ----------------------------------------
mined = sim(capital=5_000_000_000_000.0, manual=False)
mined.state.founder.policy["auto_mine"] = True
mined.annual_material_demand = lambda: {"coal_kg": 1_000_000.0}
mined.resource_throttle = lambda: 0.3
mined.state.economy.binding = "coal"
mined._step_materials()
order_rows = [row for row in mined.state.household.automation_audit if row["action"] == "mine"]
check("the mine row carries an order id", len(order_rows) == 1 and order_rows[0].get("order"), order_rows)
tranches = [tranche for tranche in mined.state.economy.mine_tranches if tranche[0] == "coal"]
check("the tranche it sank carries the same order id", tranches and tranches[0][4] == order_rows[0]["order"], tranches)
mined.state.scenario.year = tranches[0][2]
mined.commission_mines()
working = [each for each in mined.state.economy.mines if each["material"] == "coal"]
check("the working it became still names the order", working and working[0].get("order") == order_rows[0]["order"], working)

by_hand = sim(capital=5_000_000_000_000.0, manual=True)
by_hand.open_mine("coal", 10.0)
check("a mine ordered by hand has no order id", by_hand.state.economy.mine_tranches[0][4] == "", by_hand.state.economy.mine_tranches)
