"""The production module's spec (sim/assembly).

The module owns each seat's industry experience (`ProductionSeat`) and publishes what runs, what concerns earn and cost, how deep an
industry is and which techniques are in use. The projects record, the household, the tree and the economy's objects have not moved
into modules yet, so it reaches them through `legacy_game`, and nothing it publishes is cached: legacy code writes that state
directly (the record of what is done, operating and granted, the caches on the household)."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec
from sim.workforce.api import SetWageHoursSold

from .commands import AccrueExperience, LearnFromFailure
from .module import Production
from .state import ProductionSeat

READS_BY_OWNER = {
	"core": ("legacy_game",),
	"workforce": ("money_per_labour_hour", "trade_family", "staff", "staff_version", "hour_commitments"),
	"mechanics": ("capability_sets", "mechanic"),
	"knowledge": ("techniques_held", "category_trait"),
	"diffusion": ("literacy",),
	"prices": ("held_goods_prices_in_hours",),
}

_LIVE = dict(cached=False)

# (name, compute method, kind, seat scoped)
_VIEWS = (
	("running", "running", KEYED, False), ("is_venture", "is_venture", KEYED, False),
	("is_concern_node", "is_concern_node", KEYED, False), ("operating", "operating", None, False),
	("running_stamp", "running_stamp", None, False), ("practice_set", "practice_set", None, False),
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
)


def _view(name, compute, kind, seat_scoped):
	options = dict(_LIVE, seat_scoped=True) if seat_scoped else dict(_LIVE)
	return ViewSpec(name, compute, **options) if kind is None else ViewSpec(name, compute, kind=kind, **options)


MODULE_SPECS = (ModuleSpec(
	"production", Production, seat_state=ProductionSeat,
	publishes=tuple(_view(*row) for row in _VIEWS),
	applies=((AccrueExperience, "apply_accrue_experience"), (LearnFromFailure, "apply_learn_from_failure")),
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
	sends=(SetWageHoursSold,),
),)
