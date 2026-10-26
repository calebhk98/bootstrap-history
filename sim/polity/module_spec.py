"""Polity's module spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_polity.py and the
other bridge files) under the name the owner will publish, or a view of a module that has moved. Grouped by owner."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, PhaseHook, ViewSpec
from sim.knowledge.api import ForgetTechnique
from sim.ledger.api import PayEdge
from sim.reporting.api import RecordEvent
from sim.seats.api import FounderDies

from . import commands
from .module import Polity
from .state import STANDING, PolitySeat

READS_BY_OWNER = {
	"core": ("year", "civilisation", "events_enabled", "automation", "acting_seat", "danger_lines", "legacy_dice", "legacy_said_once",
	         "legacy_game", "legacy_value_weights", "legacy_constant", "legacy_act_as", "money_text", "mass_text"),
	"actors": ("state_treasury", "legacy_actor_registry", "legacy_actors_state", "legacy_agent_world", "country_world"),
	"ledger": ("acting_balance", "legacy_acting_household", "legacy_household_actor", "transfer_listening"),
	"mechanics": ("effect_sum", "effect_values", "effect_factor", "effect_best", "running_mechanics", "mechanic",
	              "patrons_lost_to_eminence"),
	"knowledge": ("techniques_held", "techniques_granted", "tree", "tree_nodes"),
	"production": ("running", "revenue_estimate", "concern_revenue", "operating"),
	"projects": ("standing_floor", "rep_factor", "legacy_done_versions"),
	"workforce": ("headcount", "base_annual_wage", "labour_state_weights", "money_per_labour_hour"),
	"seats": ("seat_list", "legacy_seats", "founder"),
	"demography": ("population_total", "pop_scale"),
	"materials": ("material_pool", "material_substitutes"),
	"reporting": ("real_output_per_head",),
	"hazards": ("output_factor",),
}

# Everything here reads the seat's own state and, through legacy views, state written outside any command of polity (the
# techniques held, the cast, the purse), so nothing is cached yet.
_LIVE = dict(cached=False)
_SEAT = dict(seat_scoped=True, cached=False)

MODULE_SPECS = (ModuleSpec(
	"polity", Polity, channels=(STANDING,), seat_state=PolitySeat,
	publishes=(
		ViewSpec("standing", "standing", **_SEAT),
		ViewSpec("eminence", "eminence", **_SEAT),
		ViewSpec("state_reach", "state_reach", **_LIVE),
		ViewSpec("order_reach", "order_reach", **_LIVE),
		ViewSpec("inspection_reach", "inspection_reach", **_LIVE),
		ViewSpec("forest_reach", "forest_reach", **_LIVE),
		ViewSpec("state_authority", "state_authority", **_LIVE),
		ViewSpec("visible_scale", "visible_scale", kind=QUOTE),
		ViewSpec("military_leverage", "military_leverage", **_SEAT),
		ViewSpec("military_equipment_burden", "military_equipment_burden_kg_per_soldier_per_year", kind=QUOTE),
		ViewSpec("state_interest", "state_interest", kind=QUOTE),
		ViewSpec("state_trait_weights", "state_trait_weights", **_LIVE),
		ViewSpec("alarm_of", "alarm_of", kind=QUOTE, seat_scoped=True),
		ViewSpec("household_scale", "household_scale", **_SEAT),
		ViewSpec("state_notice", "state_notice", **_SEAT),
		ViewSpec("notice_over", "notice_over", kind=QUOTE),
		ViewSpec("levy_shares", "levy_shares", kind=QUOTE),
		ViewSpec("eminence_report", "eminence_report", **_SEAT),
		ViewSpec("confiscation_status", "confiscation_status", **_SEAT),
		ViewSpec("state_pressure_report", "state_pressure_report", **_SEAT),
		ViewSpec("interest_groups", "interest_groups", **_LIVE),
		ViewSpec("interest_groups_report", "interest_groups_report", **_LIVE),
		ViewSpec("state_debt", "state_debt", **_SEAT),
		ViewSpec("patron_funding_ask", "patron_funding_ask", **_SEAT),
		ViewSpec("patron_clients", "patron_clients", kind=KEYED, **_LIVE),
		ViewSpec("state_funding", "state_funding", **_SEAT),
		ViewSpec("start_gate_group_prohibition", "start_gate_group_prohibition", kind=QUOTE, seat_scoped=True),
		ViewSpec("value_weight", "value_weight", kind=KEYED, **_LIVE),
	),
	applies=(
		(commands.RaiseScandal, "raise_scandal"), (commands.AddScandal, "add_scandal"), (commands.RecordBribe, "record_bribe"),
		(commands.ScaleProtection, "scale_protection"), (commands.ScaleFamiliarity, "scale_familiarity"),
		(commands.GainReputation, "gain_reputation"), (commands.AddReputation, "add_reputation"),
		(commands.SetReputation, "set_reputation"), (commands.AddGovernance, "add_governance"),
		(commands.AnswerStateDemands, "answer_state_demands"), (commands.WithdrawFromPublicLife, "withdraw_command"),
		(commands.SettleWithState, "settle_command"), (commands.CarryOutTransfers, "transfers_command"),
		(commands.RenewStanding, "renew_command"), (commands.CloseStandingYear, "close_year_command"),
		(commands.ShiftValueWeight, "shift_value_weight"), (commands.StrikeFromForce, "strike_from_force"),
		(commands.SetLandTakenMemory, "set_land_taken_memory"), (commands.RegisterPeople, "register_people"),
		(commands.SetGrievanceReference, "set_grievance_reference"), (commands.ResetStateUnrest, "reset_state_unrest"),
		(commands.SetTileReading, "set_tile_reading"), (commands.RecordRising, "record_rising"),
		(commands.ReplaceRuler, "replace_ruler"), (commands.CloseSuccessionDispute, "close_succession_dispute"),
	),
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
	sends=(PayEdge, RecordEvent, ForgetTechnique, FounderDies),
	phases=(PhaseHook("begin_seat_year", "step_begin_seat_year"),),
),)
