"""The ventures module's spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge under the name the owner will publish, or a
view of a module that has moved. Every view it publishes is uncached: the businesses and their plants are shared with the exchange
(the seat as a party to a deal), which changes them without a command of this module."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec
from sim.ledger.api import PayEdge
from sim.production.api import RefreshOperatingCaches
from sim.projects.api import NoteConcernChange

from .channels import INSTITUTION_UNITS_CHANGES, OPERATING_CHANGES
from .commands import (ClearMothball, CloseConcern, ForgetClosureReason, MothballConcern, NoteConcernYear, NoteOperatingChanged, OpenVenture,
                       RestoreConcern, ReviewConcerns, ReviewReopening, RollOut, SellConcern, ShutForgotten, StopOperating, WatchBusiness)
from .module import Ventures
from .state import VenturesSeat

READS_BY_OWNER = {
	"knowledge": ("tree_nodes", "techniques_held", "techniques_granted"),
	"production": ("running", "is_venture", "practisable", "institution_units", "institution_unit_ceiling", "institution_unit_cost",
	               "institution_upkeep", "concern_runs_without_founder", "venture_ramp", "node_output_market_factor", "concern_takings",
	               "concern_goods_have_market", "concern_sale_basis"),
	"projects": ("project_cost", "open_refusal", "staff_closure_age"),
	"workforce": ("staff", "effective_scholars", "hours_per_person_year", "money_per_labour_hour", "unskilled_trade"),
	"mechanics": ("capability_sets", "mechanic"),
	"living_stock": ("venture_garrison",),
	"seats": ("founder", "seat_party_with_margins", "seat_list"),
	"actors": ("actor_world", "cast"),
	"finance": ("spending_power",),
	"ledger": ("acting_balance", "legacy_household_actor"),
	"prices": ("price_index",),
	"demography": ("population_total",),
	"core": ("year", "game_config", "money_text"),
}

_LIVE = dict(cached=False)

# (name, the method that answers it, kind, seat scoped)
_VIEWS = (
	("mothballed", "mothballed", None, True), ("closure_records", "closure_records", None, True),
	("operating", "operating", None, True), ("operating_by_seat", "operating_by_seat", None, False), ("reopen_fee", "reopen_fee_at_prior_size", QUOTE, False), ("opening_fee", "opening_fee", QUOTE, False),
	("reopen_units", "reopen_units", KEYED, False), ("venture_capex", "venture_capex", KEYED, False),
	("venture_hands", "venture_hands", KEYED, False), ("venture_hands_founder_staffed", "venture_hands_founder_staffed", KEYED, False),
	("venture_foreman", "venture_foreman", KEYED, False), ("venture_foremen_used", "venture_foremen_used", QUOTE, False),
	("venture_foreman_free", "venture_foreman_free", QUOTE, False), ("venture_staff_used", "venture_staff_used", None, False),
	("venture_staff_free", "venture_staff_free", None, False),
	("venture_staff_who_is_watching_what", "venture_staff_who_is_watching_what", None, False),
	("concern_staff", "concern_staff", KEYED, False), ("venture_opened_year", "venture_opened_year", QUOTE, False),
	("venture_size", "venture_size", KEYED, False),
	("venture_real_earnings", "venture_real_earnings", QUOTE, False), ("venture_real_upkeep", "venture_real_upkeep", QUOTE, False),
	("venture_upkeep_quote", "venture_upkeep_quote", QUOTE, False), ("venture_forecast_basis", "venture_forecast_basis", KEYED, False),
	("venture_sale_basis", "venture_sale_basis", KEYED, False), ("concern_sale_quote", "quote_concern_sale", QUOTE, True),
	("coverage", "coverage_nodes", None, False), ("coverage_share", "coverage_share", KEYED, False), ("coverage_row", "coverage_row", KEYED, False),
	("units_for_coverage", "units_for_coverage", QUOTE, False), ("people_per_unit", "people_per_unit", KEYED, False),
	("people_who_can_use", "people_who_can_use", KEYED, False),
	("operating_version", "operating_version", None, True), ("institution_units_version", "institution_units_version", None, True),
)


def _view(name, compute, kind, seat_scoped):
	options = dict(_LIVE, seat_scoped=True) if seat_scoped else dict(_LIVE)
	return ViewSpec(name, compute, **options) if kind is None else ViewSpec(name, compute, kind=kind, **options)


MODULE_SPECS = (ModuleSpec(
	"ventures", Ventures, channels=(OPERATING_CHANGES, INSTITUTION_UNITS_CHANGES), seat_state=VenturesSeat,
	publishes=tuple(_view(*row) for row in _VIEWS),
	applies=((OpenVenture, "apply_open_venture"), (ClearMothball, "apply_clear_mothball"), (SellConcern, "apply_sell_concern"),
	         (RollOut, "apply_roll_out"), (NoteOperatingChanged, "apply_note_operating_changed"), (WatchBusiness, "apply_watch_business"),
	         (ShutForgotten, "apply_shut_forgotten"), (StopOperating, "apply_stop_operating"), (MothballConcern, "apply_mothball_concern"),
	         (RestoreConcern, "apply_restore_concern"), (CloseConcern, "apply_close_concern"),
	         (ForgetClosureReason, "apply_forget_closure_reason"), (ReviewConcerns, "apply_review_concerns"),
	         (ReviewReopening, "apply_review_reopening"), (NoteConcernYear, "apply_note_concern_year")),
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
	sends=(PayEdge, NoteConcernChange, RefreshOperatingCaches),
),)
