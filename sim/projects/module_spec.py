"""The projects module's spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_projects.py and
the other bridge files) under the name the owner will publish, or a view of a module that has moved, except the `legacy_*`
ones: raw state the module still mutates in place, which go when that state moves. Grouped by the owner each is
catalogued under (docs/architecture/catalogue). Every view the module publishes is uncached: the record of what is in hand,
built and running is written by unmoved code, so no channel can say when it changed."""
from sim.assembly.api import FIRST, KEYED, QUOTE, ExtensionPoint, ModuleSpec, PhaseHook, ViewSpec
from sim.diffusion.api import ApplyTechEffects
from sim.knowledge.api import LearnTechnique, RevealFrom
from sim.ledger.api import NoteSpend, PayEdge, ReceiveFromEdge
from sim.living_stock.api import ChangeHeld
from sim.materials.api import ApplyThrottle, SettleProjectMaterials
from sim.polity.api import AddGovernance, AddScandal, CarryOutTransfers, GainReputation, RecordBribe
from sim.production.api import LearnFromFailure
from sim.reporting.api import RecordAutomation, RecordAutomationSkip, RecordEvent
from sim.seats.api import RecordGoalReached
from sim.ventures.api import ClearMothball, OpenVenture
from sim.workforce.api import DrawTradeHours, GrantStaff, LoseCrew, ReleaseHours, ResetTradeHours, SpendDirectorHours

from .commands import (AdvanceProjects, AutoOpenVentures, Bribe, CloseLapsedDependents, CloseUnstaffedVentures, CloseWork,
                       CompleteProject, Exclude, Include, KeepStaffed, MothballWork, NoteVentureYear, PostBounty, ReopenRestaffedVentures, ResetProjectProgress,
                       RestoreWork, ReviewVentures, StartProject, StopProject)
from .needed_commands import NoteConcernChange, NoteYearSpend
from .projects import ACTIVE, START, Projects
from .state import ProjectsSeat

READS_BY_OWNER = {
	"knowledge": ("tree", "tree_nodes", "tree_closure", "techniques_held", "techniques_forgotten", "visibility", "visible_to_player",
	              "prerequisite_message", "needs_first", "corpus_hedge", "never_abandon"),
	"diffusion": ("foreign_only", "civ_cost_factor", "literacy_ceiling", "staff_sources", "tech_effects"),
	"ventures": ("closures", "reopen_fee", "reopen_units", "venture_capex", "venture_hands", "venture_foreman", "venture_foreman_free",
	             "venture_staff_free", "venture_staff_used", "venture_real_earnings", "venture_real_upkeep", "opening_fee"),
	"production": ("is_venture", "running", "operating", "revenue_estimate", "upkeep", "institution_units", "institution_unit_ceiling",
	               "institution_places", "institution_upkeep", "industry_depth", "failed_attempts_trial"),
	"projects (not moved)": ("legacy_projects",),
	"materials": ("own_output_claim", "bounty_price", "material_upfront_refusal", "material_pool", "generation", "material_binding",
	              "resource_throttle", "failure_loss", "start_gate_material_seller", "project_material_parts",
	              "project_cost_without_materials"),
	"finance": ("debt_status", "credit_limit", "funding_capacity", "purchase_remedies_text", "living_cost", "spending_power",
	            "bearable_part_of", "concern_rows_stopped"),
	"polity": ("standing", "state_interest", "value_weight", "alarm_of", "start_gate_group_prohibition"),
	"mechanics": ("approval_patron", "mechanic", "capability_sets"),
	"workforce": ("hours_available", "hours_you_can_call_on", "market_supply", "trade_available", "staff_advice", "training_advice",
	              "training_queue", "project_staffing_shortfall", "money_per_labour_hour", "staff", "hour_commitments",
	              "effective_scholars", "headcount"),
	"resources": ("mine_operating_cost",),
	"living_stock": ("start_gate_unheld_stock", "stock_held", "venture_garrison"),
	"ledger": ("acting_balance", "goods_stock", "legacy_acting_household", "legacy_household_actor"),
	"reporting": ("money_text",),
	"seats": ("win_condition_text", "win_condition_value", "acting_seat", "automation", "founder", "goal", "automatic_policy"),
	"actors": ("actor_world",),
	"land": ("built_way_km", "material_cost_factor"),
	"prices": ("price_index",),
	"core": ("society_name", "year", "horizon_end_year", "legacy_order", "project_limits", "game_config", "legacy_dice", "legacy_fog",
	         "category_trait", "plain_number"),
}

_LIVE = dict(cached=False)

# (name, the method that answers it, kind, seat scoped): a legality test or a figure is asked with the node, so it is never cached
_VIEWS = (
	("start_check", "start_check", QUOTE, True), ("start_blockers", "start_blockers", QUOTE, True),
	("start_refusal", "start_refusal", QUOTE, True), ("bounty_eligible", "bounty_eligible", QUOTE, True),
	("calendar_floor", "calendar_floor", QUOTE, True), ("effective_risk", "effective_risk", QUOTE, True),
	("payment_schedule_years", "payment_schedule_years", QUOTE, True),
	("earliest_completion_years", "earliest_completion_years", QUOTE, True),
	("expected_calendar_years", "expected_calendar_years", QUOTE, True), ("precaution_quote", "precaution_quote", QUOTE, True),
	("rebuild_work_factor", "rebuild_work_factor", QUOTE, True), ("rebuild_explanation", "rebuild_explanation", QUOTE, True),
	("rebuild_retained_share", "rebuild_retained_share", QUOTE, True),
	("relied_on_running", "relied_on_running", KEYED, False), ("gate_blocked", "gate_blocked", QUOTE, True),
	("running_gate_refusal", "running_gate_refusal", QUOTE, True),
	("exclusion_reason", "exclusion_reason", KEYED, True), ("exclusion_entry_known", "exclusion_entry_known", QUOTE, True),
	("closure_record", "closure_of", KEYED, True), ("closed_by_choice", "closed_by_choice", None, False),
	("staff_closure_age", "staff_closure_age", KEYED, True),
	("active_hours_still_wanted", "active_hours_still_wanted", None, True), ("project_hour_pace", "project_hour_pace", QUOTE, True),
	("project_useful_hours", "project_useful_hours", QUOTE, True), ("trade_demand_vs_supply", "trade_demand_vs_supply", None, True),
	("trade_draw_plan", "trade_draw_plan", QUOTE, True), ("trade_shortage_kind", "trade_shortage_kind", QUOTE, True),
	("lab_max_span", "lab_max_span", QUOTE, True), ("trades_the_project_waits_for", "trades_the_project_waits_for", QUOTE, True),
	("hour_priority_queue", "hour_priority_queue", None, True), ("hour_standing", "hour_standing", QUOTE, True),
	("goal_snapshot", "goal_snapshot", None, True), ("opening_shortfall", "opening_shortfall", QUOTE, True),
	("reputation_gain_of", "reputation_gain_of_node", QUOTE, True),
	("open_refusal", "open_refusal", QUOTE, True), ("staffing_open_refusal", "staffing_open_refusal", QUOTE, True),
	("staffing_draw", "_staffing_draw_of", QUOTE, True), ("staffing_held_totals", "staffing_held_totals", None, True),
	("staffing_shortfalls", "_staffing_shortfalls", QUOTE, True), ("staffing_missing_to_open", "staffing_missing_to_open", QUOTE, True),
	("staffing_closed_hand_shortfall", "staffing_closed_hand_shortfall", None, True),
	("concerns_to_close_for_staffing", "concerns_to_close_for_staffing", None, True),
	("staffing_closure_summary", "staffing_closure_summary", None, True), ("staffing_closure_warnings", "staffing_closure_warnings", QUOTE, True),
	("staffing_shut_count", "staffing_shut_count", None, True),
	("seat_review", "seat_review", QUOTE, True), ("committed_cost", "committed_cost", None, True),
	("active_projects", "active_projects", None, True), ("exclusions", "exclusions", None, True),
	("mothballed", "mothballed_works", None, True), ("bountied", "bountied_nodes", None, True),
	("failed_attempts", "failed_attempt_counts", None, True), ("paid_towards", "paid_towards_projects", None, True),
	("bounties_paid", "bounties_paid_total", None, True),
	("shut_for_staff", "shut_for_staff", None, True), ("spend_last_year", "spend_last_year", None, True),
	("keep_staffed", "keep_staffed", None, True), ("ever_closed_for_staff", "ever_closed_for_staff", None, True),
)


def _view(name, compute, kind, seat_scoped):
	options = dict(_LIVE, seat_scoped=True) if seat_scoped else dict(_LIVE)
	return ViewSpec(name, compute, **options) if kind is None else ViewSpec(name, compute, kind=kind, **options)


MODULE_SPECS = (ModuleSpec(
	"projects", Projects, channels=(ACTIVE, START), seat_state=ProjectsSeat,
	publishes=tuple(_view(*row) for row in _VIEWS) + (
		# the active record is written outside the module's commands (the screens, hazards, the credit freeze): never cached
		ViewSpec("project_cost", "project_cost", kind=QUOTE, seat_scoped=True, cached=False),
		ViewSpec("project_cost_now", "project_cost_now", kind=QUOTE, seat_scoped=True, cached=False),
		ViewSpec("opposition_factor", "opposition_factor", kind=QUOTE, seat_scoped=True, cached=False),
		ViewSpec("cost_money_factor", "cost_money_factor", seat_scoped=True, cached=False),
		# written only by the module's own start phase, which bumps START
		ViewSpec("start_hours", "start_hours", channels=(START,), seat_scoped=True),
		# not cached: read once, right after the start that set it
		ViewSpec("last_start", "last_start", seat_scoped=True, cached=False),
	),
	applies=((StartProject, "apply_start_project"), (StopProject, "apply_stop_project"), (PostBounty, "apply_post_bounty"),
	         (Bribe, "apply_bribe"), (ResetProjectProgress, "apply_reset_project_progress"), (AdvanceProjects, "apply_advance_projects"), (CompleteProject, "apply_complete_project"),
	         (CloseWork, "apply_close_work"), (CloseLapsedDependents, "apply_close_lapsed_dependents"),
	         (CloseUnstaffedVentures, "apply_close_unstaffed_ventures"), (ReopenRestaffedVentures, "apply_reopen_restaffed_ventures"),
	         (AutoOpenVentures, "apply_auto_open_ventures"), (NoteVentureYear, "apply_note_venture_year"),
	         (ReviewVentures, "apply_review_ventures"), (MothballWork, "apply_mothball_work"), (RestoreWork, "apply_restore_work"),
	         (Exclude, "apply_exclude"), (Include, "apply_include"), (KeepStaffed, "apply_keep_staffed")),
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
	sends=(PayEdge, NoteSpend, ReceiveFromEdge, RecordBribe, RecordEvent, RecordAutomation, RecordAutomationSkip, SettleProjectMaterials,
	       ClearMothball, NoteConcernChange, NoteYearSpend, OpenVenture, ReleaseHours, LearnTechnique, RevealFrom, ChangeHeld,
	       CarryOutTransfers, ApplyTechEffects, GainReputation, AddScandal, AddGovernance, GrantStaff, RecordGoalReached, LoseCrew,
	       LearnFromFailure, ApplyThrottle, DrawTradeHours, ResetTradeHours, SpendDirectorHours),
	phases=(PhaseHook("start_projects", "start_projects_hook"),),
	extension_points=(ExtensionPoint("extra_start_checks", FIRST),),
),)
