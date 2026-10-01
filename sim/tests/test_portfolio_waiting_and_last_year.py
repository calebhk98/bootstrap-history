"""Complaint 293: portfolio also groups startable-but-blocked work, and sets last year's hours against this year's."""
from .harness import *  # noqa: F401,F403

from sim.engine.blockers import BLOCKER_KINDS


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


poor = sim(capital=2_000.0)
poor.end_year = poor.cfg["start_year"] + poor.cfg["horizon_years"]
ask(poor, cmd="step", years=1)
screen = ask(poor, cmd="portfolio")
waiting = screen.get("waiting_to_start")
check("portfolio has a waiting-to-start section", isinstance(waiting, list) and waiting, screen.keys())
if waiting:
    check("each waiting group is a shared blocker kind with its projects",
          all(group["kind"] in BLOCKER_KINDS and group["count"] >= len(group["projects"]) and group["projects"]
              for group in waiting), waiting[:2])
    members = [project for group in waiting for project in group["projects"]]
    check("a waiting project is not done, not active, and the gate refuses it",
          all(project not in poor.done and project not in poor.active
              and poor.start_blockers(project) for project in members), members[:3])
    check("a waiting group's kind is the gate's first blocker for each member",
          all(poor.start_blockers(project)[0]["kind"] == group["kind"]
              for group in waiting for project in group["projects"]), waiting[:1])
    check("prerequisite-missing work is not waiting work",
          all(group["kind"] != "knowledge" for group in waiting), [group["kind"] for group in waiting])

from sim.engine.proto.render_typed import _RENDERERS
text = _RENDERERS["portfolio"](screen)
check("the printed screen names the waiting work", "WAITING TO START" in text, text[:400])

rich = sim(capital=5_000_000.0)
rich.end_year = rich.cfg["start_year"] + rich.cfg["horizon_years"]
for node_id in list(rich.order):
    if len(rich.active) >= 6:
        break
    if node_id not in rich.done and NODES[node_id]["yrs"] >= 6 and rich.can_start(node_id):
        ask(rich, cmd="start", id=node_id)
ask(rich, cmd="step", years=2)  # arrival snapshot plus two years
rows = ask(rich, cmd="portfolio")["projects"]
check("a project running two years carries last year's effective hours",
      rows and all("hours_effective_last_year" in row for row in rows), rows[:1])
snapshots = rich._dashboard_history
check("last year's figure is the earlier snapshot's, not this year's",
      all(row["hours_effective_last_year"] == snapshots[-2]["project_hours_effective"].get(row["id"])
          for row in rows), (rows[:1], snapshots[-2].get("project_hours_effective")))
