"""The projects module's spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_projects.py)
under the name the owner will publish, except the `legacy_*` ones: raw state the module still mutates in place, which
go when that state moves. Grouped by the owner each is catalogued under (docs/architecture/catalogue)."""
from sim.assembly.api import FIRST, QUOTE, ExtensionPoint, ModuleSpec, PhaseHook, ViewSpec
from sim.ledger.api import PayEdge

from .commands import Bribe, PostBounty, StartProject, StopProject
from .needed_commands import (ChangeStanding, ClearMothball, CompleteProject, NoteSpend, RecordAutomation,
                              RecordAutomationSkip, RecordEvent, SettleProjectMaterials)
from .projects import ACTIVE, START, Projects

READS_BY_OWNER = {
	"knowledge": ("tree", "techniques_held", "visibility", "visible_to_player", "prerequisite_message", "needs_first"),
	"diffusion": ("foreign_only", "civ_cost_factor"),
	"ventures": ("closures", "reopen_fee"),
	"production": ("is_venture", "running", "revenue_estimate", "upkeep"),
	"projects (not moved)": ("project_cost", "calendar_floor", "effective_risk", "rebuild_work_factor", "committed_cost",
	                         "precaution_spec", "precaution_extra_cost", "precaution_extra_hours", "start_gate_running",
	                         "legacy_projects"),
	"materials": ("own_output_claim", "bounty_price", "material_upfront_refusal", "material_pool", "generation",
	              "start_gate_material_seller"),
	"finance": ("debt_status", "credit_limit", "funding_capacity", "purchase_remedies_text"),
	"polity": ("standing", "state_interest", "value_weight", "start_gate_group_prohibition"),
	"mechanics": ("approval_patron",),
	"workforce": ("hours_available", "market_supply", "trade_available", "staff_advice", "training_advice", "training_queue",
	              "project_staffing_shortfall", "living_cost", "money_per_labour_hour", "staff"),
	"resources": ("mine_operating_cost",),
	"living_stock": ("start_gate_unheld_stock",),
	"ledger": ("acting_balance", "goods_stock", "legacy_acting_household"),
	"reporting": ("money_text",),
	"seats": ("win_condition_text", "acting_seat", "automation"),
	"core": ("society_name", "year", "horizon_end_year", "legacy_order", "project_limits", "research_world"),
}

MODULE_SPECS = (ModuleSpec(
	"projects", Projects, channels=(ACTIVE, START),
	publishes=(
		# quotes: a legality test is asked with the node, so it is never cached
		ViewSpec("start_check", "start_check", kind=QUOTE, seat_scoped=True),
		ViewSpec("start_blockers", "start_blockers", kind=QUOTE, seat_scoped=True),
		ViewSpec("start_refusal", "start_refusal", kind=QUOTE, seat_scoped=True),
		ViewSpec("bounty_eligible", "bounty_eligible", kind=QUOTE, seat_scoped=True),
		# written only by the module's own start phase, which bumps START
		ViewSpec("start_hours", "start_hours", channels=(START,), seat_scoped=True),
		# not cached: read once, right after the start that set it
		ViewSpec("last_start", "last_start", seat_scoped=True, cached=False),
	),
	applies=((StartProject, "apply_start_project"), (StopProject, "apply_stop_project"), (PostBounty, "apply_post_bounty"),
	         (Bribe, "apply_bribe")),
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
	sends=(PayEdge, NoteSpend, ChangeStanding, RecordEvent, RecordAutomation, RecordAutomationSkip, SettleProjectMaterials,
	       ClearMothball, CompleteProject),
	phases=(PhaseHook("start_projects", "start_projects_hook"),),
	extension_points=(ExtensionPoint("extra_start_checks", FIRST),),
),)
