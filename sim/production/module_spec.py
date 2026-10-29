"""The production module's spec (sim/assembly).

The module owns each seat's industry experience (`ProductionSeat`) and publishes what runs, what concerns earn and cost, how deep an
industry is and which techniques are in use. The projects record, the household and the tree have not moved into modules yet, so it
reads them through the views of their owners (the engine bridge answers `running_versions`; ventures publishes `operating`), and nothing it
publishes is cached: legacy code writes that state directly (the record of what is done, operating and granted)."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec
from sim.diffusion.api import NoteFirstRuns
from sim.workforce.api import SetWageHoursSold

from .commands import (AccrueExperience, BumpHouseholdVersion, ForgetRevenueCaches, LearnFromFailure, RefreshDoneCaches,
                       RefreshOperatingCaches)
from .module import Production
from .state import ProductionSeat

READS_BY_OWNER = {
	"core": ("year", "game_setting", "civilisation", "category_trait", "trade_family", "running_versions"),
	"workforce": ("money_per_labour_hour", "staff", "staff_version", "hour_commitments", "hours_available", "wage_signature",
	              "market_annual_wage", "standing_job_pay", "headcount", "base_tile", "people_who_exist", "hours_per_person_year",
	              "literacy_references"),
	"mechanics": ("capability_sets", "mechanic", "running_mechanics", "effect_sum"),
	"knowledge": ("techniques_held", "techniques_granted", "done_year", "tree_nodes"),
	"diffusion": ("literacy", "techniques_spread"),
	"prices": ("held_goods_prices_in_hours", "price_index", "done_memo", "producers_memo", "material_prices", "commodity_record"),
	"markets": ("agent_prices_at", "agent_seat_sale_outlook", "agent_trades_good", "agent_producers_by_good",
	            "agent_worker_years_by_recipe", "home_unit_price"),
	"ventures": ("operating", "venture_opened_year", "venture_size", "venture_capex", "venture_real_earnings", "venture_real_upkeep",
	             "venture_foreman", "venture_hands_founder_staffed", "coverage", "units_for_coverage"),
	"actors": ("concern_versions", "concerns_of_active_firms", "firm_concern_holdings"),
	"projects": ("gate_blocked",),
	"demography": ("pop_scale", "population", "farm_holdings"),
	"reporting": ("real_output_per_head",),
	"finance": ("debt_status",),
	"polity": ("standing", "state_funding"),
	"hazards": ("output_factor",),
	"coin": ("home_price_level",),
	"seats": ("acting_seat", "founder"),
	"land": ("built_ways", "held_techniques"),
}

_LIVE = dict(cached=False)

# (name, compute method, kind, seat scoped)
_VIEWS = (
	("running", "running", KEYED, False), ("is_venture", "is_venture", KEYED, False),
	("is_concern_node", "is_concern_node", KEYED, False), 
	("done_in_order", "done_in_order", None, True), ("running_stamp", "running_stamp", None, False), ("practice_set", "practice_set", None, False),
	("practisable", "practisable", KEYED, False), ("capability_gaps", "capability_gaps", None, False),
	("institution_units", "institution_units", KEYED, False), ("institution_places", "institution_places", KEYED, False),
	("institution_unit_ceiling", "institution_unit_ceiling", KEYED, False),
	("institution_unit_cost", "institution_unit_cost", QUOTE, False),
	("institution_upkeep", "institution_upkeep", QUOTE, False),
	("revenue_estimate", "revenue", None, True), ("revenue_capacity", "revenue_capacity", None, True),
	("estimated_revenue", "estimated_revenue", None, True), ("revenue_sources", "revenue_sources", None, True),
	("founder_wage_income", "founder_wage_income", None, True), ("still_ramping", "still_ramping", None, True),
	("capability_factor", "capability_factor", None, True), ("upkeep", "upkeep", None, True),
	("upkeep_by_concern", "upkeep_by_concern", None, True), ("concern_revenue", "concern_revenue", KEYED, True),
	("workshop_output", "workshop_output", None, False), ("concern_market", "ledger_concern_rows", None, False),
	("held_trade", "held_trade", None, False), ("venture_ramp", "venture_ramp", KEYED, False),
	("concern_goods_have_market", "concern_goods_have_market", KEYED, False),
	("node_output_market_factor", "node_output_market_factor", QUOTE, False),
	("basket_market_factor", "basket_market_factor", QUOTE, False),
	("concern_sale_basis", "concern_sale_basis", KEYED, False), ("concern_takings", "concern_takings", QUOTE, False),
	("concern_gross", "concern_gross", QUOTE, False), ("concern_upkeep", "concern_upkeep", QUOTE, False),
	("concern_book_offer", "concern_book_offer", KEYED, False), ("concern_book_inputs_cost", "concern_book_inputs_cost", KEYED, False),
	("concern_volume_ratio", "concern_volume_ratio", QUOTE, False), ("concern_value_ratio", "concern_value_ratio", KEYED, False),
	("concern_learning_ratio", "concern_learning_ratio", KEYED, False), ("concern_baskets_now", "concern_baskets_now", KEYED, False),
	("industry_depth", "industry_depth", KEYED, False), ("industry_scale_ceiling", "industry_scale_ceiling", KEYED, False),
	("industry_experience", "industry_experience", KEYED, False),
	("concern_runs_without_founder", "concern_runs_without_founder", KEYED, False),
	("founding_worker_years", "founding_worker_years", KEYED, False),
	("failed_attempts_trial", "failed_attempts_trial", QUOTE, False), ("techniques_in_use", "techniques_in_use", None, True),
	("techniques_epoch", "techniques_epoch", None, False), ("price_epoch", "price_epoch", None, False),
	("ramp_share_at_full_depth", "ramp_share_at_full_depth", None, False),
	("institution_expansion_convexity", "institution_expansion_convexity", None, False),
)


def _view(name, compute, kind, seat_scoped):
	options = dict(_LIVE, seat_scoped=True) if seat_scoped else dict(_LIVE)
	return ViewSpec(name, compute, **options) if kind is None else ViewSpec(name, compute, kind=kind, **options)


MODULE_SPECS = (ModuleSpec(
	"production", Production, seat_state=ProductionSeat,
	publishes=tuple(_view(*row) for row in _VIEWS),
	applies=((AccrueExperience, "apply_accrue_experience"), (LearnFromFailure, "apply_learn_from_failure"),
	         (RefreshDoneCaches, "apply_refresh_done_caches"), (RefreshOperatingCaches, "apply_refresh_operating_caches"),
	         (ForgetRevenueCaches, "apply_forget_revenue_caches")),
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
	sends=(SetWageHoursSold, NoteFirstRuns, BumpHouseholdVersion),
),)
