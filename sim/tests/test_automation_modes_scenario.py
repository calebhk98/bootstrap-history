"""SCENARIO (Complaint 421): in a whole game `auto_hire` replace-only hires nobody when nobody was lost and rehires what it
lost, the policy command sets the mode, and a mine ordered by automation can be traced from its audit row to the tranche
that was sunk. The replace-only rule and the typed switch are in test_automation_modes."""

from .harness import *  # noqa: F401,F403

from sim.engine.staff_replacement import REPLACE_ONLY


# ---- scenario: the mode on a game
def hire_game(mode, underpaid):
    game = sim(capital=2_000_000.0, manual=False)
    game.state.founder.policy["keep_pay_at_market"] = not underpaid
    game.state.founder.policy["auto_hire"] = mode
    game.state.household.automation_audit = []
    return game


def rows_of(game, action):
    return [each for each in game.state.household.automation_audit if each["policy"] == "auto_hire" and each["action"] == action]


growing = hire_game(True, False)
steady = hire_game(REPLACE_ONLY, False)
for _ in range(3):
    growing._step_staff()
    steady._step_staff()
check("scenario: the default mode grows the staff; replace-only hires nobody when nobody was lost",
      sum(growing.state.household.employees.values()) > 0 and rows_of(growing, "hire")
      and not steady.state.household.employees and not rows_of(steady, "hire") and not rows_of(steady, "replace"),
      (growing.state.household.employees, steady.state.household.employees, steady.state.household.automation_audit))

lossy = hire_game(REPLACE_ONLY, True)
lossy.state.household.employees.update({"artisan": 6.0, "scholar": 1.0})
lossy.labour.resync_pools()
lossy.state.household.staff_pay_held.update({"artisan": 1e-6, "scholar": 1e-6})    # paid next to nothing
lossy._step_staff()
replaced = rows_of(lossy, "replace")
# presentation: the audit row names the mode in words
check("scenario: replace-only on a game rehires the trades it lost, never beyond what was lost, naming the mode",
      replaced and {each["what"].split()[-1] for each in replaced} >= {"artisan"}
      and lossy.state.household.employees.get("artisan", 0.0) <= 6.0
      and lossy.state.household.employees.get("scholar", 0.0) <= 1.0
      and all("replace-only" in each["reason"] for each in replaced),
      (lossy.state.household.employees, lossy.state.household.automation_audit))

# ---- scenario: the policy command sets the mode
switch = hire_game(True, False)
set_reply = S._agent_dispatch(switch, NODES, {"cmd": "policy", "set": {"auto_hire": "replace"}})
set_mode = switch.policy["auto_hire"]
off_reply = S._agent_dispatch(switch, NODES, {"cmd": "policy", "set": {"auto_hire": "off"}})
check("scenario: the policy command sets the replace-only mode, and off is still off",
      set_reply["ok"] and set_mode == REPLACE_ONLY and off_reply["ok"] and switch.policy["auto_hire"] is False,
      (set_reply, off_reply))

# ---- scenario: a mine's tranche is tied to the row that ordered it
mined = sim(capital=5_000_000_000_000.0, manual=False)
mined.state.founder.policy["auto_mine"] = True
mined.annual_material_demand = lambda: {"coal_kg": 1_000_000.0}
mined.resource_throttle = lambda: 0.3
mined.state.holdings.binding = "coal"
mined._step_materials()
order_rows = [each for each in mined.state.household.automation_audit if each["action"] == "mine"]
tranches = [tranche for tranche in mined.state.holdings.mine_tranches if tranche[0] == "coal"]
mined.state.scenario.year = tranches[0][2]
mined.commission_mines()
working = [each for each in mined.state.holdings.mines if each["material"] == "coal"]
by_hand = sim(capital=5_000_000_000_000.0, manual=True)
by_hand.open_mine("coal", 10.0)
check("scenario: a mine ordered by automation carries one order id from its audit row to the tranche sunk and the working "
      "it became; a mine ordered by hand has none",
      len(order_rows) == 1 and order_rows[0].get("order") and tranches and tranches[0][4] == order_rows[0]["order"]
      and working and working[0].get("order") == order_rows[0]["order"]
      and by_hand.state.holdings.mine_tranches[0][4] == "",
      (order_rows, tranches, working, by_hand.state.holdings.mine_tranches))
