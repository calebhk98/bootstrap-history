"""A credit freeze still allows starts paid from cash (Complaints/150), and the save carries no version stamp
(Complaints/184).

What cash pays for during a freeze is tested on built numbers (`cash_covers_start`), the freeze check and the bounty on
stand-in games."""

QUICK_TOPIC = True
from .harness import *  # noqa: F401,F403
from sim.projects.api import funding
cash_covers_start = funding.cash_covers_start
import sim.engine.saveload as _saveload_module

# --- 150: a credit freeze allows what cash in hand covers
check("a start the cash covers, on top of nothing owed, is allowed", cash_covers_start(1000.0, 0.0, 0.0, 1000.0))
check("a start needing credit is not covered by cash", not cash_covers_start(1000.0, 0.0, 0.0, 999.0))
check("cash already owed to work in hand is not spent twice", not cash_covers_start(600.0, 0.0, 500.0, 1000.0)
      and cash_covers_start(500.0, 0.0, 500.0, 1000.0))
check("what is already paid towards a start comes off its price", cash_covers_start(1000.0, 400.0, 0.0, 600.0)
      and not cash_covers_start(1000.0, 400.0, 0.0, 599.0))
check("what is paid towards a start never reduces the price below nothing, nor does a negative payment raise it",
      cash_covers_start(1000.0, 5000.0, 0.0, 0.0) and not cash_covers_start(1000.0, -50.0, 0.0, 999.0))
check("a household in arrears covers no start with cash but a free one", not cash_covers_start(1.0, 0.0, 0.0, -5.0)
      and cash_covers_start(0.0, 0.0, 0.0, 0.0))
check("saveload has no SAVE_VERSION", not hasattr(_saveload_module, "SAVE_VERSION"))


# --- the freeze check and the bounty, called on the projects module built with what they read
import types

from sim.agents.api import edges
from sim.ledger.api import PayEdge
from sim.projects.api import PostBounty, blocker_rules
from sim.tests import module_harness, projects_host
from sim.projects.state import ProjectsSeat


def frozen_game(year, frozen_until, covered, end_year=1000):
    module = projects_host.build(year=year, debt_status={"credit_frozen_until": frozen_until, "insolvent_years": 0},
                                 horizon_end_year=end_year)
    module._cash_covers_start = lambda node_id: covered
    return module


def check_frozen(module):
    return module._check_credit_frozen("node", {}, False, None, True)


check("during a freeze a start the cash does not cover is refused", check_frozen(frozen_game(100, 103, False))[0] is False)
check("...and one the cash covers is allowed", check_frozen(frozen_game(100, 103, True)) is None)
check("...and once the freeze has lifted a start is not refused for it", check_frozen(frozen_game(103, 103, False)) is None)
check("...and a household never frozen is not refused for it", check_frozen(frozen_game(100, None, False)) is None)
frozen_check = next(entry for entry in blocker_rules.START_CHECKS if entry.cause == "credit_frozen")
check("the freeze check is a money blocker, reported under the cause credit_frozen",
      frozen_check.kind == "money"
      and blocker_rules.classify_plain_check(frozen_check.cause, frozen_check.kind, "text", [], None, False)["cause"] == "credit_frozen")

# the cash a start needs: its price less what is paid towards it, on top of what work in hand still owes
cash_state = projects_host.projects_state(active={"a": {"cost_left": 200.0}, "b": {"cost_left": None}})
cash_module = projects_host.build(project_cost=lambda node_id: 1000.0, legacy_projects=cash_state, acting_balance=900.0,
                                  seat=ProjectsSeat(paid_towards={"node": 300.0}))
check("the cash that covers a start counts what is owed on active work and what is paid towards it",
      cash_module._cash_covers_start("node") is True)
cash_module = projects_host.build(project_cost=lambda node_id: 1000.0, legacy_projects=cash_state, acting_balance=899.0,
                                  seat=ProjectsSeat(paid_towards={"node": 300.0}))
check("...and is not covered one unit short", cash_module._cash_covers_start("node") is False)


# a bounty pays the price, draws no poster hours, and is not counted as hours the founder still has to give
def poster(capital, price):
    state = projects_host.projects_state()
    module = projects_host.build(
        tree={"node": {"name": "Node", "ph": 500.0, "yrs": 2.0}}, legacy_projects=state, bounty_price=lambda node_id: price,
        acting_balance=capital)
    module.started = []

    def initialize_project(node_id, **keywords):
        module.started.append(keywords)
        state.active[node_id] = {"ph_left": keywords["ph_left"]}
    module.initialize_project = initialize_project
    return module, module.seat


poster_module, poster_seat = poster(1000.0, 400.0)
posted_ok = poster_module.post_bounty(PostBounty("node"))
check("a bounty the poster can pay is posted", posted_ok is True)
paid = [command for command in module_harness.sent(poster_module) if isinstance(command, PayEdge)]
check("...it pays the price under its cause and spends no poster hours or hired trades",
      paid == [PayEdge(edges.EDGE_WORKERS, 400.0, "bounties posted")] and poster_module.started[0]["ph_left"] == 0.0
      and poster_module.started[0]["include_labour"] is False and poster_module.started[0]["cost_left"] == 0.0,
      (paid, poster_module.started))
check("...and marks the project as bountied", poster_seat.bountied == {"node"})
check("...and counts the bounty among those the seat has posted", poster_seat.bounties_paid == 1)
def _wanting():
    module = projects_host.build(legacy_projects=types.SimpleNamespace(active_keys_sorted=lambda: ["a", "b"]), tree={"a": {}, "b": {}})
    module.project_hour_pace = lambda node_id: {"a": 40.0, "b": 0.0}[node_id]
    return module


bounty_projects = types.SimpleNamespace(active={"node": {"ph_left": 500.0}})
bounty_module = projects_host.build(legacy_projects=bounty_projects, tree={"node": {"ph": 500.0, "yrs": 2.0}}, seat=ProjectsSeat(bountied={"node"}))
check("a bountied project asks for no hours of the founder", bounty_module.project_hour_pace("node") == 0.0)
check("a project asking for hours is listed with them and one asking for none is not",
      _wanting().active_hours_still_wanted() == {"a": 40.0})
broke_module, _broke_state = poster(300.0, 400.0)
check("a bounty beyond the purse is refused and nothing is paid",
      broke_module.post_bounty(PostBounty("node")) is False and module_harness.sent(broke_module) == [])
check("the bounty set is saved as node ids, checked against the tree on load",
      "bountied" in _saveload_module._SET_FIELDS_OF_NODE_IDS, _saveload_module._SET_FIELDS_OF_NODE_IDS)
