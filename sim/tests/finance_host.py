"""The finance module for a test: built with `module_harness`, every view it reads answering a quiet default unless the test gives its own.

    module = finance_host.build(seat=FinanceSeat(insolvent_years=9), acting_balance=-500.0)
    module.stall_diagnosis()

A view given as a plain value is that value (None means the view is absent: give `lambda: None` for a view that answers None); as a function it is called with the view's arguments; a keyed view is a dict or a
function of the key. Defaults are the quiet answers: an empty purse, no income and no costs, a household with no standing, an agent
economy that has not opened. The commands the module sent are in `module_harness.sent(module)`."""
from types import SimpleNamespace
from typing import Any, Dict, Optional

from sim.finance import purchase_rules
from sim.finance.module import Finance
from sim.finance.state import FinanceSeat
from sim.tests import module_harness


def _household(capital: float = 0.0) -> SimpleNamespace:
	return SimpleNamespace(capital=capital, slaves=0, freedmen=0, artisans=0, scholars=0)


def defaults() -> Dict[str, Any]:
	return {
		"year": 100, "civilisation": {"id": "rome", "starting_interest_rate": 0.1, "starting_tax_share": 0.0},
		"game_config": {"founder_hours_per_year": 3000.0}, "legacy_game": SimpleNamespace(),
		"money_text": lambda amount, grouped=False, short=False: "%d money" % round(amount), "price_index": 1.0,
		"cast": SimpleNamespace(actors={}, active_firms=lambda: [], purse_lenders=lambda: []), "cast_state": SimpleNamespace(),
		"state_treasury": SimpleNamespace(actor_id="state"), "actor_world": SimpleNamespace(), "legacy_edge_account": {},
		"legacy_seats": {}, "seat_party": {}, "dealing_party": SimpleNamespace(money=0.0),
		"acting_balance": 0.0, "legacy_acting_household": _household(), "legacy_household_actor": SimpleNamespace(),
		"effect_sum": lambda channel, start=0.0: start, "effect_values": lambda channel: [], "nodes_with_mechanic": lambda name: (),
		"standing": {"reputation": 0.0}, "forest_hectares": 0.0, "mine_operating_cost": 0.0,
		"money_per_labour_hour": 1.0, "labour_market": SimpleNamespace(quote=lambda trade: 1.0), "wage_bill": 0.0,
		"household_bill_per_person": 0.0, "household_dependant_people": 0.0, "held_trade": lambda: None,
		"revenue_capacity": 0.0, "revenue_estimate": 0.0, "upkeep": 0.0, "operating": set(), "cash_remedies": [],
		"committed_cost": 0.0, "legacy_projects": SimpleNamespace(active={}), "tree_nodes": {},
		"agent_rate": lambda: None, "agent_credit_room": lambda borrower_id: (False, None), "agent_economy_opened": False,
		"agent_economy": lambda: None,
	}


def build(answers: Optional[Dict[type, Any]] = None, seat: Optional[FinanceSeat] = None, **views: Any) -> Finance:
	"""The module with `views` over the quiet defaults, a fresh seat unless given, and `answers`, the replies of owners to
	commands keyed by command class."""
	every_view = defaults()
	every_view.update(views)
	module = module_harness.build(Finance, views=every_view, answers=answers, seat=seat or FinanceSeat(), module_id="finance")
	module.clock.acting_seat = "founder"
	return module


def purchase_views(spending_power):
	"""A game's `view` for the purchase views, over a stand-in's own `spending_power(kind)`."""
	def budget():
		return spending_power("buy")
	views = {"purchase_budget": budget, "can_pay": lambda cost: purchase_rules.can_pay(cost, budget()),
	         "affordable_units": lambda unit_cost, decimals=1: purchase_rules.affordable_units(budget(), unit_cost, decimals)}
	return lambda name: views[name]
