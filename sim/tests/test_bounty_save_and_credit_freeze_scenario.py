"""SCENARIO (Complaints 153 and 150): in a whole game a posted bounty round-trips through a save, carries no version stamp and
costs no founder hours over a year, and a credit freeze refuses a start that needs credit while allowing one that cash
covers. The cash rule itself is in test_bounty_save_and_credit_freeze."""
from .harness import *  # noqa: F401,F403
from sim.engine.saveload import save_state, load_state



def _bounty_node(test_sim):
    return next(node_id for node_id in ORDER
                if node_id not in test_sim.done and NODES[node_id]["ph"] > 100
                and NODES[node_id]["lab"] and test_sim.bounty_eligible(node_id))


# --- scenario: a posted bounty round-trips through the save file, carries no version stamp, and draws none of the
# poster's hours (it is paid for)
target = sim(capital=1.0)          # the game that receives the load
bounty_sim = sim(capital=1e9)
bounty_id = _bounty_node(bounty_sim)
hours_before = bounty_sim.state.founder.director_hours_spent_founder
posted = bounty_sim.post_bounty(bounty_id)
fresh_hours = bounty_sim.active[bounty_id]["ph_left"]
_save_path = os.path.join(tempfile.mkdtemp(), "save.json")
save_state(bounty_sim, _save_path)
try:
    load_state(target, _save_path)
    reload_error = None
except ValueError as error:
    reload_error = str(error)
with open(_save_path) as _stamp_handle:
    _stamp_blob = json.load(_stamp_handle)
bounty_sim.step()
check("scenario: a posted bounty asks for no founder hours, loads back from a save with no version stamp as an active "
      "bountied project, and a year with only it active spends none of the founder's hours and reports none wanted",
      posted and fresh_hours == 0 and reload_error is None and bounty_id in target.active and bounty_id in target.bountied
      and "_version" not in _stamp_blob
      and bounty_sim.state.founder.director_hours_spent_founder == hours_before
      and bounty_id not in bounty_sim.active_hours_still_wanted(),
      (posted, fresh_hours, reload_error, _stamp_blob.get("_version"),
       bounty_sim.state.founder.director_hours_spent_founder - hours_before))

# --- scenario: a credit freeze refuses a start that needs credit and allows one that cash covers
frozen = sim(capital=1e9)
cheap_id = next(node_id for node_id in ORDER
                if node_id not in frozen.done and frozen.can_start(node_id)
                and 0 < frozen.project_cost(node_id) < 5000)
cheap_cost = frozen.project_cost(cheap_id)
frozen.household.credit_frozen_until = frozen.year + 3

frozen.capital = cheap_cost * 0.5
refused, why_not = frozen.start_project(cheap_id)
refused_cause = frozen.start_blockers(cheap_id)[0]["cause"]
frozen.capital = cheap_cost * 4
allowed, why_allowed = frozen.start_project(cheap_id)
check("scenario: during a credit freeze a start needing credit is refused as credit_frozen, and one fully covered by cash "
      "is allowed",
      not refused and refused_cause == "credit_frozen" and allowed, (why_not, refused_cause, why_allowed))
