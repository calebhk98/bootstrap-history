"""bounty_save_and_credit_freeze: a posted bounty survives a save and costs no
founder hours (Complaints/153), the save carries no version stamp
(Complaints/184), and a credit freeze still allows starts paid from cash
(Complaints/150)."""
from .harness import *  # noqa: F401,F403
from sim.engine.saveload import save_state, load_state


def _bounty_node(test_sim):
    return next(node_id for node_id in ORDER
                if node_id not in test_sim.done and NODES[node_id]["ph"] > 100
                and NODES[node_id]["lab"] and test_sim.bounty_eligible(node_id))


def _round_trip(test_sim):
    path = os.path.join(tempfile.mkdtemp(), "save.json")
    save_state(test_sim, path)
    load_state(target, path)
    return target, path


# One game receives every load; one game posts the bounty and steps.
target = sim(capital=1.0)

# --- 157: a posted bounty round-trips through the save file, and is paid for, so it draws none
# of the poster's hours
bounty_sim = sim(capital=1e9)
bounty_id = _bounty_node(bounty_sim)
hours_before = bounty_sim.state.founder.director_hours_spent_founder
check("set-up: a bounty can be posted", bounty_sim.post_bounty(bounty_id))
check("a fresh bounty asks for no founder hours",
      bounty_sim.active[bounty_id]["ph_left"] == 0, bounty_sim.active[bounty_id])
try:
    reloaded_sim, _save_path = _round_trip(bounty_sim)
    reload_error = None
except ValueError as error:
    reloaded_sim, reload_error = None, str(error)
check("a save holding a posted bounty loads back", reload_error is None, reload_error)
check("...and the bounty is still active and marked bountied after the load",
      reloaded_sim is not None and bounty_id in reloaded_sim.active
      and bounty_id in reloaded_sim.bountied)
# --- 188: no version stamp in the save
with open(_save_path) as _stamp_handle:
    _stamp_blob = json.load(_stamp_handle)
check("the save carries no version stamp", "_version" not in _stamp_blob,
      _stamp_blob.get("_version"))
import sim.engine.saveload as _saveload_module
check("saveload has no SAVE_VERSION", not hasattr(_saveload_module, "SAVE_VERSION"))
bounty_sim.step()
check("stepping a year with only a bounty active spends no founder hours",
      bounty_sim.state.founder.director_hours_spent_founder == hours_before,
      bounty_sim.state.founder.director_hours_spent_founder - hours_before)
check("...and its hours are not reported as wanted",
      bounty_id not in bounty_sim.active_hours_still_wanted())

# --- 154: a credit freeze allows what cash in hand covers -------------------
frozen = sim(capital=1e9)
cheap_id = next(node_id for node_id in ORDER
                if node_id not in frozen.done and frozen.can_start(node_id)
                and 0 < frozen.project_cost(node_id) < 5000)
cheap_cost = frozen.project_cost(cheap_id)
other_id = next(node_id for node_id in ORDER
                if node_id != cheap_id and node_id not in frozen.done
                and frozen.can_start(node_id) and 0 < frozen.project_cost(node_id) < cheap_cost * 1.5)
frozen.household.credit_frozen_until = frozen.year + 3

frozen.capital = cheap_cost * 0.5
started, why_not = frozen.start_project(cheap_id)
check("during a credit freeze, a start needing credit is still refused",
      not started and "nobody here will fund" in (why_not or ""), why_not)

frozen.capital = cheap_cost * 1.5
frozen.active[cheap_id] = dict(ph_left=1.0, yrs=0.0, spent=0.0, cost_left=cheap_cost, lab_left={})
started, why_not = frozen.start_project(other_id)
check("cash already owed to work in hand is not spent twice during a freeze", not started, why_not)
del frozen.active[cheap_id]

frozen.capital = cheap_cost * 4
started, why_not = frozen.start_project(cheap_id)
check("during a credit freeze, a start fully covered by cash is allowed", started, why_not)
