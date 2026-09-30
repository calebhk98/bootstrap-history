"""bounty_save_and_credit_freeze: a posted bounty survives a save and costs no
founder hours (Complaints/157), the save carries no version stamp
(Complaints/188), and a credit freeze still allows starts paid from cash
(Complaints/154)."""
from .harness import *  # noqa: F401,F403
from sim.engine.proto.saveload import save_state, load_state


def _bounty_node(test_sim):
    return next(node_id for node_id in ORDER
                if node_id not in test_sim.done and NODES[node_id]["ph"] > 100
                and NODES[node_id]["lab"] and test_sim.bounty_eligible(node_id))


def _round_trip(test_sim):
    path = os.path.join(tempfile.mkdtemp(), "save.json")
    save_state(test_sim, path)
    fresh = sim(capital=1.0)
    load_state(fresh, path)
    return fresh, path


# --- 157: a posted bounty round-trips through the save file -----------------
bounty_sim = sim(capital=1e9)
bounty_id = _bounty_node(bounty_sim)
check("set-up: a bounty can be posted", bounty_sim.post_bounty(bounty_id))
try:
    reloaded_sim, _save_path = _round_trip(bounty_sim)
    reload_error = None
except ValueError as error:
    reloaded_sim, reload_error = None, str(error)
check("a save holding a posted bounty loads back", reload_error is None, reload_error)
check("...and the bounty is still active and marked bountied after the load",
      reloaded_sim is not None and bounty_id in reloaded_sim.active
      and bounty_id in reloaded_sim.bountied)

# --- 157: a bounty is paid for, so it draws none of the poster's hours ------
hours_sim = sim(capital=1e9)
hours_before = hours_sim.state.founder.director_hours_spent_founder
hours_sim.post_bounty(bounty_id)
check("a fresh bounty asks for no founder hours",
      hours_sim.active[bounty_id]["ph_left"] == 0, hours_sim.active[bounty_id])
hours_sim.step()
check("stepping a year with only a bounty active spends no founder hours",
      hours_sim.state.founder.director_hours_spent_founder == hours_before,
      hours_sim.state.founder.director_hours_spent_founder - hours_before)
check("...and its hours are not reported as wanted",
      bounty_id not in hours_sim.active_hours_still_wanted())

# --- 188: no version stamp in the save --------------------------------------
_stamp_sim, _stamp_path = _round_trip(sim(capital=1000.0))
with open(_stamp_path) as _stamp_handle:
    _stamp_blob = json.load(_stamp_handle)
check("the save carries no version stamp", "_version" not in _stamp_blob,
      _stamp_blob.get("_version"))
import sim.engine.proto.saveload as _saveload_module
check("saveload has no SAVE_VERSION", not hasattr(_saveload_module, "SAVE_VERSION"))

# --- 154: a credit freeze allows what cash in hand covers -------------------
def _frozen_sim(capital):
    frozen_sim = sim(capital=capital)
    frozen_sim.household.credit_frozen_until = frozen_sim.year + 3
    return frozen_sim


_probe = sim(capital=1e9)
cheap_id = next(node_id for node_id in ORDER
                if node_id not in _probe.done and _probe.can_start(node_id)
                and 0 < _probe.project_cost(node_id) < 5000)
cheap_cost = _probe.project_cost(cheap_id)

rich_frozen = _frozen_sim(cheap_cost * 4)
started, why_not = rich_frozen.start_project(cheap_id)
check("during a credit freeze, a start fully covered by cash is allowed",
      started, why_not)

poor_frozen = _frozen_sim(cheap_cost * 0.5)
started, why_not = poor_frozen.start_project(cheap_id)
check("during a credit freeze, a start needing credit is still refused",
      not started and "nobody here will fund" in (why_not or ""), why_not)

busy_frozen = _frozen_sim(cheap_cost * 1.5)
busy_frozen.active[cheap_id] = dict(ph_left=1.0, yrs=0.0, spent=0.0,
                                    cost_left=cheap_cost, lab_left={})
other_id = next(node_id for node_id in ORDER
                if node_id not in (cheap_id,) and node_id not in busy_frozen.done
                and _probe.can_start(node_id) and 0 < _probe.project_cost(node_id) < cheap_cost * 1.5)
started, why_not = busy_frozen.start_project(other_id)
check("cash already owed to work in hand is not spent twice during a freeze",
      not started, why_not)
