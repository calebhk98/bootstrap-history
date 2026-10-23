"""A credit freeze still allows starts paid from cash (Complaints/150), and the save carries no version stamp
(Complaints/184).

What cash pays for during a freeze is tested on built numbers (`cash_covers_start`), the freeze check and the bounty on
stand-in games. One bounty through a save and a load is test_bounty_save_and_credit_freeze_scenario."""

QUICK_TOPIC = True
from .harness import *  # noqa: F401,F403
from sim.engine.project_funding import cash_covers_start
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


# --- the freeze check and the bounty, called on stand-in games
import types

from sim.engine import blockers
from sim.engine.projects_progress import ProgressMixin
from sim.engine.projects_starting import StartingMixin


def frozen_game(year, frozen_until, covered, end_year=None):
    household = types.SimpleNamespace(credit_frozen_until=frozen_until)
    game = types.SimpleNamespace(state=types.SimpleNamespace(scenario=types.SimpleNamespace(year=year), household=household),
                                 cfg={"start_year": 100, "horizon_years": 500}, end_year=end_year,
                                 _cash_covers_start=lambda node_id: covered)
    return game


check_frozen = StartingMixin._check_credit_frozen
check("during a freeze a start the cash does not cover is refused",
      check_frozen(frozen_game(100, 103, False), "node", {}, None, {}, True)[0] is False)
check("...and one the cash covers is allowed", check_frozen(frozen_game(100, 103, True), "node", {}, None, {}, True) is None)
check("...and once the freeze has lifted a start is not refused for it",
      check_frozen(frozen_game(103, 103, False), "node", {}, None, {}, True) is None)
check("...and a household never frozen is not refused for it", check_frozen(frozen_game(100, None, False), "node", {}, None, {}, True) is None)
check("the freeze check is a money blocker, reported under the cause credit_frozen",
      check_frozen.blocker_kind == "money"
      and blockers.classify_plain_check(check_frozen.__name__, check_frozen.blocker_kind, "text", [], None, False)["cause"] == "credit_frozen")

# the cash a start needs: its price less what is paid towards it, on top of what work in hand still owes
cash_game = types.SimpleNamespace(
    project_cost=lambda node_id: 1000.0,
    state=types.SimpleNamespace(
        projects=types.SimpleNamespace(active={"a": {"cost_left": 200.0}, "b": {"cost_left": None}}, paid_towards={"node": 300.0}),
        household=types.SimpleNamespace(capital=900.0)))
check("the cash that covers a start counts what is owed on active work and what is paid towards it",
      StartingMixin._cash_covers_start(cash_game, "node") is True)
cash_game.state.household.capital = 899.0
check("...and is not covered one unit short", StartingMixin._cash_covers_start(cash_game, "node") is False)


# a bounty pays the price, draws no poster hours, and is not counted as hours the founder still has to give
class _Poster(StartingMixin):
    def __init__(self, capital, price):
        self.nodes = {"node": {"name": "Node", "ph": 500.0, "yrs": 2.0}}
        self.state = types.SimpleNamespace(
            household=types.SimpleNamespace(capital=capital, total_spend=0.0, bounties_paid=0, log=[]),
            projects=types.SimpleNamespace(active={}, bountied=set()),
            scenario=types.SimpleNamespace(year=100))
        self._price = price
        self.paid, self.started = [], []

    def bounty_price(self, node_id):
        return self._price

    def pay_edge(self, edge, amount, cause):
        self.paid.append((amount, cause))

    def initialize_project(self, node_id, **keywords):
        self.started.append(keywords)
        self.state.projects.active[node_id] = {"ph_left": keywords["ph_left"]}


import sim.engine.projects_starting as _projects_starting
from unittest import mock

poster = _Poster(1000.0, 400.0)
with mock.patch.object(_projects_starting, "money_text", lambda amount, sim, **keywords: "money"):
    posted_ok = poster.post_bounty("node")
check("a bounty the poster can pay is posted", posted_ok is True)
check("...it pays the price under its cause and spends no poster hours or hired trades",
      poster.paid == [(400.0, "bounties posted")] and poster.started[0]["ph_left"] == 0.0
      and poster.started[0]["include_labor"] is False and poster.started[0]["cost_left"] == 0.0, (poster.paid, poster.started))
check("...and marks the project as bountied", poster.state.projects.bountied == {"node"})
check("...and a bountied project asks for no hours of the founder",
      ProgressMixin.project_hour_pace(poster, "node") == 0.0 and ProgressMixin.active_hours_still_wanted(
          types.SimpleNamespace(state=types.SimpleNamespace(projects=types.SimpleNamespace(
              active_keys_sorted=lambda: ["node"], bountied={"node"}, active=poster.state.projects.active)),
              nodes=poster.nodes, project_hour_pace=lambda node_id: ProgressMixin.project_hour_pace(poster, node_id))) == {})
broke = _Poster(300.0, 400.0)
check("a bounty beyond the purse is refused and nothing is paid", broke.post_bounty("node") is False and broke.paid == [])
check("the bounty set is saved as node ids, checked against the tree on load",
      "bountied" in _saveload_module._SET_FIELDS_OF_NODE_IDS, _saveload_module._SET_FIELDS_OF_NODE_IDS)
