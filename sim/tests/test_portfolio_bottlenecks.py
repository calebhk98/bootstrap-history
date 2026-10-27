"""Complaint 88: portfolio groups running work by what blocks it, in the shared blocker kinds.
`bottleneck_groups` and `_portfolio_rows` are called on rows and stubs the test builds;
the portfolio reply of a game is test_game_port_and_portfolio_smoke."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.engine.blockers import BLOCKER_KINDS
from sim.ui.proto.economy import _portfolio_rows
from sim.ui.proto.portfolio_bottlenecks import bottleneck_groups
from sim.ui.proto.render_screens_economy import render_portfolio
from sim.tests.ui_stand_in import Game

stub_game = Game(spending_power=lambda purpose: 500.0)
nodes = {name: {"yrs": 4} for name in ("a", "b", "c", "d", "e")}
active = {
    "a": {"name": "A", "waiting_on": "nobody to do the work: smiths", "founder_hours_left": 100.0, "still_to_pay": 10.0},
    "b": {"name": "B", "waiting_on": "trade hours already booked: smiths", "founder_hours_left": 50.0, "still_to_pay": 20.0},
    "c": {"name": "C", "waiting_on": "materials: iron", "founder_hours_left": 30.0, "still_to_pay": 5.0},
    "d": {"name": "D", "waiting_on": "money for the next stage", "founder_hours_left": 20.0, "still_to_pay": 40.0},
    "e": {"name": "E", "waiting_on": None, "founder_hours_left": 10.0, "still_to_pay": 1.0},
}
rows = _portfolio_rows(nodes, active)
check("each project row carries a shared blocker kind", all(row["blocker_kind"] in BLOCKER_KINDS for row in rows),
      [row["blocker_kind"] for row in rows])
check("a project with no named cause is idle", next(row for row in rows if row["id"] == "e")["blocker_kind"] == "idle")

trade_rows = [{"trade": "smiths", "demand_hours_this_year": 900.0, "supply_hours_this_year": 400.0, "oversubscribed": True,
               "projects_drawing_on_it": ["a", "b"]},
              {"trade": "weavers", "demand_hours_this_year": 10.0, "supply_hours_this_year": 40.0, "oversubscribed": False,
               "projects_drawing_on_it": ["z"]}]
groups = bottleneck_groups(stub_game, rows, trade_rows, 1000.0, 0.5, "iron")
check("every group is named by a shared blocker kind", groups and all(group["kind"] in BLOCKER_KINDS for group in groups),
      [group["kind"] for group in groups])
grouped_ids = [project_id for group in groups for project_id in group["projects"]]
check("every project is in exactly one group", sorted(grouped_ids) == sorted(active), grouped_ids)
check("a group counts its projects", all(group["count"] == len(group["projects"]) for group in groups), groups)
check("each group says what to do about it", all(group.get("what_it_means") for group in groups), groups)
specialists = next(group for group in groups if group["kind"] == "specialists")
check("a group sums the hours its projects still have to work", specialists["hours_still_to_work"] == 150.0, specialists)
check("pools come from the trade demand and supply handed in, only for trades the group's projects draw on",
      [pool["trade"] for pool in specialists["pools"]] == ["smiths"]
      and specialists["pools"][0]["demand_hours_this_year"] == 900.0 and specialists["pools"][0]["projects_affected"] == 2,
      specialists["pools"])
money = next(group for group in groups if group["kind"] == "money")
check("the money pool is what the bill is against what could be raised",
      money["pools"][0]["demand"] == 40.0 and money["pools"][0]["supply"] == 500.0, money["pools"])
check("groups come most fixable first", [group["kind"] for group in groups][:2] == ["specialists", "supply"], groups)
check("no running work has no groups", bottleneck_groups(stub_game, [], trade_rows, 1000.0, None, None) == [])

text = render_portfolio({"projects": rows, "bottlenecks": groups, "paging": {"more": 0}, "active_project_count": len(rows)})
# presentation: screen order, the bottlenecks come before the project list
check("the printed screen shows the bottlenecks before the project list",
      "BOTTLENECKS" in text and text.index("BOTTLENECKS") < text.index(rows[0]["name"]), text[:300])
