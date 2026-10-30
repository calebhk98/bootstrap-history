"""The finance module for a test: built with `module_harness`, every view it reads answering a quiet default unless the test gives its own.

    module = finance_host.build(seat=FinanceSeat(insolvent_years=9), acting_balance=-500.0)
    module.stall_diagnosis()

A view given as a plain value is that value (None means the view is absent: give `lambda: None` for a view that answers None); as a function it is called with the view's arguments; a keyed view is a dict or a
function of the key. Defaults are the quiet answers: an empty purse, no income and no costs, a household with no standing, an agent
economy that has not opened. The commands the module sent are in `module_harness.sent(module)`."""
from types import SimpleNamespace
from typing import Any, Dict, Optional

from sim.finance import purchase_rules
from sim.agents.api import Purses
from sim.projects.api import HaltActiveProjects, ReviewVentures
from sim.finance.module import Finance
from sim.finance.state import FinanceSeat
from sim.tests import event_stand_in, module_harness
from sim.workforce.api import BleedStaff, DisperseDependants


def _household(capital: float = 0.0) -> SimpleNamespace:
	return SimpleNamespace(capital=capital, slaves=0, freedmen=0, artisans=0, scholars=0)


def defaults() -> Dict[str, Any]:
	return {
		"year": 100, "civilisation": {"id": "rome", "starting_interest_rate": 0.1, "starting_tax_share": 0.0},
		"game_config": {"founder_hours_per_year": 3000.0},
		"money_text": lambda amount, grouped=False, short=False: "%d money" % round(amount), "price_index": 1.0,
		"cast": SimpleNamespace(actors={}, active_firms=lambda: [], purse_lenders=lambda: []),
		"state_treasury": SimpleNamespace(actor_id="state"), "actor_world": SimpleNamespace(), "lender_offers_made": {},
		"cash_and_deposit": lambda account: 0.0, "loans_out": lambda lender=None: 0.0, "debt_owed": lambda account: 0.0,
		"cast_state": SimpleNamespace(purses=Purses()), "acting_balance": 0.0,
		"hours_for_sale": 0.0, "best_wage_trade": None, "work_for_wages_dry_run": lambda trade, hours: (0.0, None),
		"standing_job_pay": lambda trade: 0.0,
		"effect_sum": lambda channel, start=0.0: start, "effect_values": lambda channel: [], "mechanic": {},
		"standing": {"reputation": 0.0}, "forest_hectares": 0.0, "mine_operating_cost": 0.0,
		"money_per_labour_hour": 1.0, "labour_market": SimpleNamespace(quote=lambda trade: 1.0, quote_annual=lambda trade: 1.0), "wage_bill": 0.0,
		"household_bill_per_person": 0.0, "household_dependant_people": 0.0, "held_trade": lambda: None,
		"revenue_capacity": 0.0, "revenue_estimate": 0.0, "upkeep": 0.0, "operating": set(),
		"held_goods": lambda: [], "goods_stock": {}, "material_commodity": lambda material: material, "sale_quote": lambda material, tonnes: (None, 0.0, 0.0),
		"techniques_held": lambda: set(), "techniques_granted": lambda: set(), "venture_real_upkeep": lambda node_id: 0.0,
		"mine_capacity": lambda: {}, "mine_workings": lambda: [], "mine_working_cost": lambda working: 0.0,
		"committed_cost": 0.0, "tree_nodes": {},
		"agent_rate": lambda: None, "agent_credit_room": lambda borrower_id: (False, None), "agent_economy_opened": False,
	}


def build(answers: Optional[Dict[type, Any]] = None, seat: Optional[FinanceSeat] = None, household: Optional[Any] = None,
          **views: Any) -> Finance:
	"""The module with `views` over the quiet defaults, a fresh seat unless given, and `answers`, the replies of owners to
	commands keyed by command class. `household` is a stand-in whose `capital` is the purse and whose people the staff view
	counts (the workforce module's handlers of the commands that change them change it too)."""
	every_view = defaults()
	household = household if household is not None else _household()
	every_view["acting_balance"] = lambda: household.capital
	every_view.update(views)
	every_view.setdefault("staff", lambda: dict({key: getattr(household, key, 0) for key in ("slaves", "freedmen", "artisans", "scholars")}, employees={}))
	answers = dict(answers or {})
	answers.setdefault(HaltActiveProjects, ([], 0.0))
	answers.setdefault(ReviewVentures, [])
	for command in (BleedStaff, DisperseDependants):   # the workforce module's own handlers change the household's people
		answers.setdefault(command, lambda command, household=household: event_stand_in.workforce_command(household, command))
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
