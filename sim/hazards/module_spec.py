"""Hazards' module spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_hazards.py and
bridge_shared.py) under the name the owner will publish, or a view of a module that has moved. Grouped by the owner each is
catalogued under (docs/architecture/catalogue)."""
from sim.assembly.api import QUOTE, ModuleSpec, PhaseHook, ViewSpec
from sim.coin.api import PlunderHousehold
from sim.demography.api import CutPopulation, KillPeople, RefreshDemographicIndexes
from sim.knowledge.api import ForgetTechnique
from sim.ledger.api import PayEdge
from sim.polity.api import RaiseScandal, ScaleProtection, ShiftValueWeight
from sim.projects.api import ResetProjectProgress
from sim.ventures.api import ShutForgotten
from sim.reporting.api import ErodeMoney, NoteWageShock, RecordEvent
from sim.workforce.api import ReportStaffReduction, ScaleDeputies, SurviveStaff

from .commands import LoseCapital, RecordWorldEvent, RecoverOutput, SayOnce
from .module import Hazards
from .state import OUTPUT, WORLD_EVENTS, HazardsSeat, HazardsWorld

READS_BY_OWNER = {
	"core": ("year", "civilisation", "opening_civilisation", "events_enabled", "game_random",
	         "money_text"),
	"seats": ("seat_list", "ended_seats", "founder", "goal", "automation"),
	"knowledge": ("techniques_held", "techniques_granted", "tree", "tree_nodes", "visible_to_player", "losable_node_ids",
	              "tree_closure", "critical_path", "corpus_hedge", "visibility", "techniques_forgotten", "fog_of_war"),
	"mechanics": ("hazard_counter_rows", "corpus_hedge_tiers", "corpus_nodes", "mechanic", "running_mechanics"),
	"production": ("running", "capability_gaps"),
	"disease": ("epidemic_risk",),
	"demography": ("population_total", "nutrition_ratio_last_year"),
	"land": ("tiles_listed_by",),
	"projects": ("start_check", "project_cost", "active_projects", "closure_record", "closed_by_choice"),
	"diffusion": ("civ_diffusion", "diffusible_ids", "diffusion_relief", "literacy"),
	"defence_stores": ("counter_supply_gap",),
	"resources": ("mine_capacity",),
	"polity": ("military_leverage", "standing"),
	"workforce": ("staff", "staff_snapshot", "wage_index", "money_per_labour_hour"),
	"ledger": ("acting_balance",),
	"reporting": ("money_real", "event_log", "real_output_hours"),
	"markets": ("price_index",),
	"foreign_trade": ("partners_in_agent_economy",),
	"agriculture": ("weather_seed",),
	"actors": ("country_strata", "state_budget_figures", "army_figures", "state_knows", "home_strata_rows"),
}

# The figures read the seat's techniques, the mines, the diffusion and the held stores, all written outside any command of
# theirs, and a quote is never cached. The output factor is written only by this module, so it is cached.
_QUOTE = dict(kind=QUOTE, seat_scoped=True)

MODULE_SPECS = (ModuleSpec(
	"hazards", Hazards, channels=(OUTPUT, WORLD_EVENTS), world_state=HazardsWorld, seat_state=HazardsSeat,
	publishes=(
		ViewSpec("output_factor", "output_factor", channels=(OUTPUT,)),
		ViewSpec("world_events", "world_events", kind=QUOTE, channels=(WORLD_EVENTS,)),
		ViewSpec("effective_hazard", "effective_hazard", **_QUOTE),
		ViewSpec("event_cause_report", "event_cause_report", **_QUOTE),
		ViewSpec("hazard_figure", "hazard_figure", **_QUOTE),
		ViewSpec("hazard_relief_entries", "hazard_relief_entries", **_QUOTE),
		ViewSpec("hazard_relief", "hazard_relief", **_QUOTE),
		ViewSpec("hazard_relief_detail", "hazard_relief_detail", **_QUOTE),
		ViewSpec("hazard_effect_preview", "hazard_effect_preview", **_QUOTE),
		ViewSpec("hazard_advice", "hazard_advice", **_QUOTE),
		ViewSpec("hazard_timeline", "hazard_timeline", **_QUOTE),
		ViewSpec("knowledge_risk", "knowledge_risk", **_QUOTE),
		ViewSpec("staff_loss_exposure", "staff_loss_exposure", **_QUOTE),
		ViewSpec("national_public_health_sources", "national_public_health_sources", **_QUOTE),
		ViewSpec("live_hazard_kinds", "live_hazard_kinds", kind=QUOTE),
		ViewSpec("disaster_this_year", "disaster", cached=False),
		ViewSpec("countries_in_game", "countries_in_game", cached=False),
	),
	applies=((RecordWorldEvent, "record_world_event"), (LoseCapital, "lose_capital_command"), (RecoverOutput, "recover_output"),
	         (SayOnce, "say_once")),
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
	sends=(PayEdge, PlunderHousehold, ErodeMoney, RecordEvent, RaiseScandal, ScaleProtection, ShiftValueWeight, SurviveStaff,
	       ScaleDeputies, ReportStaffReduction, NoteWageShock, CutPopulation, RefreshDemographicIndexes, KillPeople,
	       ForgetTechnique, ResetProjectProgress, ShutForgotten),
	phases=(PhaseHook("dated_shocks", "step_dated_shocks"), PhaseHook("random_events", "step_random_events"),
	        PhaseHook("world_hazards", "step_world_hazards"), PhaseHook("famine_watch", "step_famine_watch")),
),)
