"""Scenario (Complaint 88): the portfolio reply of a running game groups every active project, and its pools read the engine's
own trade demand and supply. The grouping rules are in test_portfolio_bottlenecks."""
from .harness import *  # noqa: F401,F403


def ask(test_sim, **command):
    return S._agent_dispatch(test_sim, NODES, command)


crowded = unopened_sim(capital=5_000_000.0)
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
grouped_ids = [project_id for group in groups for project_id in group["projects"]]
check("every active project is in exactly one group",
      sorted(grouped_ids) == sorted(crowded.active), (grouped_ids, sorted(crowded.active)))

supply_by_trade = crowded.trade_demand_vs_supply()
pool_rows = [pool for group in groups for pool in group.get("pools", []) if "trade" in pool]
check("pools come from the engine's own trade demand and supply",
      all(pool["trade"] in supply_by_trade
          and pool["demand_hours_this_year"] == supply_by_trade[pool["trade"]]["demand_hours_this_year"]
          for pool in pool_rows), pool_rows[:2])
