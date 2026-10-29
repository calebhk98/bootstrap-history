"""The production module for a test: built with `module_harness`, every view it reads a plain value the test supplies.

    module = production_host.build(seat=ProductionSeat(), tree_nodes=nodes, staff={"employees": {}})
    module.held_trade()

A method the module calls on itself can be replaced on the instance (`module.industry_depth = lambda node_id: 0.5`). A view given as a plain
value is that value; as a function it is called with the view's arguments (see `module_harness`). Defaults are the quiet answers: an
empty tree, nothing done, granted or operating, no mechanics, one unit of money per labour hour, every trade a craft, no staff, no
economy prices. The commands the module sent are in `module_harness.sent(module)`."""
from typing import Any, Dict, Optional

from sim.production.module import Production
from sim.production.state import ProductionSeat
from sim.tests import module_harness


def defaults() -> Dict[str, Any]:
	return {
		"year": 100, "game_setting": {"revenue_ramp_years": 3}, "civilisation": {}, "tree_nodes": {}, "techniques_held": frozenset(),
		"techniques_granted": frozenset(), "operating": set(), "done_year": {}, "techniques_version": 0, "operating_version": 0, "institution_units_version": 0,
		"price_index": 1.0, "output_factor": 1.0, "venture_opened_year": lambda node_id, default: default,
		"venture_size": lambda node_id: 1.0, "running_mechanics": lambda name: [], "effect_sum": lambda channel, base: base,
		"money_per_labour_hour": 1.0, "trade_family": lambda trade: "craft",
		"staff": {"employees": {}, "freedmen": 0.0, "slaves": 0.0, "directors_extra": 0.0}, "staff_version": 0,
		"hour_commitments": {"wage_hours": 0.0}, "hours_available": lambda pool: 0.0, "wage_signature": 0,
		"market_annual_wage": lambda trade: 0.0, "standing_job_pay": lambda trade: 0.0, "capability_sets": (frozenset(), frozenset(), {}),
		"mechanic": lambda name: {}, "category_trait": lambda category, trait: False,
		"literacy": lambda field, country=None: 0.1, "held_goods_prices_in_hours": lambda held: {},
		"agent_prices_at": lambda tile=None: None,"agent_trades_good": lambda material: False, "agent_seat_sale_outlook": lambda seat, material, quantity: None,
		"commodity_record": lambda material: {}, "material_prices": {}, "home_unit_price": lambda material: None,
		"pop_scale": 1.0, "real_output_per_head": 1.0, "state_funding": 0.0, "home_price_level": 1.0, "founder": {"alive": True},
		"standing": {"governance": 0.0, "reputation": 0.0}, "debt_status": {"bondage_years_left": 0.0}, "farm_holdings": {"hectares": 0.0},
		"done_memo": lambda name, key, compute: compute(), "producers_memo": lambda name, key, compute: compute(),
		"base_tile": "base", "held_techniques": lambda include_starting=True: frozenset(), "built_ways": {},
		"agent_producers_by_good": lambda: None, "agent_worker_years_by_recipe": lambda: None, "techniques_spread": frozenset(),
		"headcount": 0.0, "hours_per_person_year": 2000.0, "people_who_exist": lambda trade: 0.0,
		"venture_hands_founder_staffed": lambda node_id: (0.0, 0.0), "venture_foreman": lambda node_id: (None, 0.0),
		"concern_versions": (0, 0), "concerns_of_active_firms": set(), "firm_concern_holdings": [],
	}


def build(seat: Optional[ProductionSeat] = None, answers: Optional[Dict[type, Any]] = None, **views: Any) -> Production:
	"""The module over the quiet defaults and `views`, a fresh seat unless given, and `answers`, the replies of owners to commands."""
	every_view = defaults()
	every_view.update(views)
	module = module_harness.build(Production, views=every_view, answers=answers, seat=seat or ProductionSeat(), module_id="production")
	module.clock.acting_seat = "founder"
	return module
