"""Complaint 421: the automatic project start and the mine order record what they skipped, and why."""
from .harness import *  # noqa: F401,F403


def skip_rows(test_sim):
    return [row for row in test_sim.state.household.automation_audit if row["action"] == "skipped"]


def fresh():
    test_sim = sim(capital=2_000_000.0, manual=False)
    test_sim.state.household.automation_audit = []
    return test_sim


blocked = fresh()
blocked.can_start = lambda node_id, _memo=None: False
blocked._step_start_projects()
rows = skip_rows(blocked)
check("a year where nothing can start leaves one row naming the first blocked candidate and its refusal",
      len(rows) == 1 and rows[0]["policy"] == "auto_start" and rows[0]["reason"], rows)

dear = fresh()
dear.can_start = lambda node_id, _memo=None: True
dear.initialize_project = lambda node_id: None
dear.project_cost = lambda node_id: 1e18
dear._step_start_projects()
rows = skip_rows(dear)
check("a candidate dearer than the room left is recorded with the cost and the room",
      rows and "room" in rows[0]["reason"] and rows[0]["policy"] == "auto_start", rows[:1])
check("the too-dear candidates make one row a year, not one each", len(rows) == 1 and "candidates in all" in rows[0]["reason"], len(rows))

capped = fresh()
capped.can_start = lambda node_id, _memo=None: True
capped.initialize_project = lambda node_id: None
capped.MAX_ACTIVE_PROJECTS_BASE = -10_000
capped._step_start_projects()
rows = skip_rows(capped)
check("hitting the active-project cap is recorded once", len(rows) == 1 and "active" in rows[0]["reason"], rows)

poor = sim(capital=0.0, manual=False)
poor.state.household.automation_audit = []
poor.state.founder.policy["auto_mine"] = True
poor.annual_material_demand = lambda: {"coal_kg": 1_000_000.0}
poor.resource_throttle = lambda: 0.3
poor.state.holdings.binding = "coal"
poor.spending_power = lambda kind: 1e12
poor._step_materials()
rows = [row for row in skip_rows(poor) if row["policy"] == "auto_mine"]
check("an auto-mine that orders nothing says why", len(rows) == 1 and rows[0]["reason"], rows)
