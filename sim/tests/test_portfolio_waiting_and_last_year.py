"""Complaint 293: portfolio also groups startable-but-blocked work, and sets last year's hours against this year's.
`waiting_to_start` and `_add_last_year_hours` are called on stubs the test builds."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.engine.blockers import BLOCKER_KINDS
from sim.ui.proto.economy import _add_last_year_hours
from sim.ui.proto.portfolio_waiting import SHOWN_PER_GROUP, waiting_to_start
from sim.ui.proto.render_screens_economy import render_portfolio
from sim.tests.ui_stand_in import Game, ui_state

nodes = {"root": {"pre": []}, "built": {"pre": []}, "running": {"pre": []}, "needs_root": {"pre": ["missing"]},
         "hidden": {"pre": []}, "unknown": {"pre": []}, "free": {"pre": []},
         "poor_a": {"pre": []}, "poor_b": {"pre": []}, "short_a": {"pre": []}}
costs = {"poor_a": 9.0, "poor_b": 3.0, "short_a": 5.0}
blockers_of = {
    "root": [{"kind": "knowledge"}],
    "needs_root": [{"kind": "money"}],
    "hidden": [{"kind": "money"}],
    "unknown": [{"kind": "somethingnew"}, {"kind": "money"}],
    "free": [],
    "poor_a": [{"kind": "money"}, {"kind": "specialists"}],
    "poor_b": [{"kind": "money"}],
    "short_a": [{"kind": "specialists"}],
}
stub_game = Game(
    done={"built"}, active={"running": {}},
    start_blockers=lambda node_id: blockers_of.get(node_id, []),
    project_cost=lambda node_id: costs.get(node_id, 0.0),
    _visible_to_player=lambda node_id: node_id != "hidden")
groups = waiting_to_start(stub_game, nodes)
by_kind = {group["kind"]: group for group in groups}
check("each waiting group is a shared blocker kind with its projects",
      all(group["kind"] in BLOCKER_KINDS and group["count"] >= len(group["projects"]) and group["projects"]
          for group in groups if group["kind"] != "somethingnew"), groups)
check("a group's kind is the gate's first blocker for each member",
      by_kind["money"]["projects"] == ["poor_b", "poor_a"] and by_kind["specialists"]["projects"] == ["short_a"], groups)
members = [project for group in groups for project in group["projects"]]
check("built, running, prerequisite-missing, hidden, knowledge-blocked and unblocked work is not waiting work",
      not set(members) & {"built", "running", "needs_root", "hidden", "root", "free"}, members)
check("a member is listed cheapest first", costs[by_kind["money"]["projects"][0]] <= costs[by_kind["money"]["projects"][1]])
check("groups come most fixable first, a kind not in the order last",
      [group["kind"] for group in groups] == ["specialists", "money", "somethingnew"], groups)
many = {"m%d" % i: {"pre": []} for i in range(SHOWN_PER_GROUP + 3)}
crowded_game = Game(done=set(), active={}, start_blockers=lambda node_id: [{"kind": "money"}],
                               project_cost=lambda node_id: float(node_id[1:]), _visible_to_player=lambda node_id: True)
crowded = waiting_to_start(crowded_game, many)[0]
check("a group counts every member but lists a limited number",
      crowded["count"] == len(many) and len(crowded["projects"]) == SHOWN_PER_GROUP, crowded)

text = render_portfolio({"projects": [], "waiting_to_start": groups, "paging": {"more": 0}, "active_project_count": 0})
# presentation: the printed screen carries the waiting section under its heading
check("the printed screen names the waiting work", "WAITING TO START" in text, text[:400])

history = [{"project_hours_effective": {"p": 1.0}}, {"project_hours_effective": {"p": 7.0}}, {"project_hours_effective": {"p": 9.0}}]
rows = [{"id": "p"}, {"id": "q"}]
_add_last_year_hours(Game(state=ui_state(dashboard_history=history)), rows)
check("last year's figure is the earlier snapshot's, not this year's", rows[0]["hours_effective_last_year"] == 7.0, rows)
check("a project the earlier snapshot lacks has no last-year figure", rows[1]["hours_effective_last_year"] is None, rows)
young = [{"id": "p"}]
_add_last_year_hours(Game(state=ui_state(dashboard_history=history[:2])), young)
check("with fewer than three snapshots there is no last-year figure", young[0]["hours_effective_last_year"] is None, young)
