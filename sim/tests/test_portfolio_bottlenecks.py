"""Complaint 88: portfolio groups running work by what blocks it, in the shared blocker kinds."""
from .harness import *  # noqa: F401,F403

from sim.engine.blockers import BLOCKER_KINDS


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


crowded = sim(capital=5_000_000.0)
crowded.end_year = crowded.cfg["start_year"] + crowded.cfg["horizon_years"]
for node_id in list(crowded.order):
    if len(crowded.active) >= 6:
        break
    if node_id not in crowded.done and crowded.can_start(node_id):
        ask(crowded, cmd="start", id=node_id)
check("the scenario has several active projects", len(crowded.active) >= 3, len(crowded.active))
ask(crowded, cmd="step", years=1)

portfolio = ask(crowded, cmd="portfolio")
groups = portfolio.get("bottlenecks")
check("portfolio leads with bottleneck groups", isinstance(groups, list) and groups, portfolio.keys())
check("every group is named by a shared blocker kind",
      all(group["kind"] in BLOCKER_KINDS for group in groups), [group["kind"] for group in groups])
grouped_ids = [project_id for group in groups for project_id in group["projects"]]
check("every active project is in exactly one group",
      sorted(grouped_ids) == sorted(crowded.active), (grouped_ids, sorted(crowded.active)))
check("a group counts its projects", all(group["count"] == len(group["projects"]) for group in groups), groups)
check("each project row carries the same kind",
      all(row["blocker_kind"] in BLOCKER_KINDS for row in portfolio["projects"]), portfolio["projects"][:1])
check("each group says what to do about it", all(group.get("what_it_means") for group in groups), groups)

supply_by_trade = crowded.trade_demand_vs_supply()
pool_rows = [pool for group in groups for pool in group.get("pools", []) if "trade" in pool]
check("pools come from the engine's own trade demand and supply",
      all(pool["trade"] in supply_by_trade
          and pool["demand_hours_this_year"] == supply_by_trade[pool["trade"]]["demand_hours_this_year"]
          for pool in pool_rows), pool_rows[:2])

from sim.ui.proto.render_typed import _RENDERERS
text = _RENDERERS["portfolio"](portfolio)
check("the printed screen shows the bottlenecks before the project list",
      "BOTTLENECKS" in text and text.index("BOTTLENECKS") < text.index(portfolio["projects"][0]["name"]), text[:300])

empty = ask(sim(capital=1_000_000.0), cmd="portfolio")
check("an empty portfolio has no groups", empty.get("bottlenecks") == [], empty)
