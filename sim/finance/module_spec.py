"""The finance module's spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_finance.py and the other
bridge files) under the name the owner will publish, or a view of a module that has moved. Grouped by owner. The `legacy_*` names
are the owners' raw objects the module still holds in place: the household's state and actor, the projects record, the seats'
registry and the game itself (the ventures' review and the labour market's quotes, until production and workforce publish them).

Nothing it publishes is cached: the agents' shared arrears rule writes `interest_arrears` and `arrears_years` behind the module
through the household's `arrears_book`, and every answer reads the economy, the actors' book and the household directly."""
from sim.assembly.api import QUOTE, ModuleSpec, PhaseHook, ViewSpec
from sim.ledger.api import SettleWithEdge, WithdrawHouseholdMoney
from sim.polity.api import SetReputation
from sim.reporting.api import RecordEvent
from sim.resources.api import MothballMines
from sim.workforce.api import BleedStaff, DisperseDependants

from . import commands
from .module import Finance
from .state import FinanceSeat

READS_BY_OWNER = {
	"core": ("year", "civilisation", "game_config", "legacy_game", "money_text"),
	"prices": ("price_index",),
	"actors": ("cast", "cast_state", "state_treasury", "actor_world", "legacy_edge_account"),
	"seats": ("legacy_seats", "seat_party", "dealing_party"),
	"ledger": ("acting_balance", "legacy_acting_household", "legacy_household_actor"),
	"mechanics": ("effect_sum", "effect_values", "nodes_with_mechanic"),
	"polity": ("standing",),
	"resources": ("forest_hectares", "mine_operating_cost"),
	"workforce": ("staff", "money_per_labour_hour", "labour_market", "wage_bill", "household_dependant_people",
	              "held_trade"),
	"production": ("revenue_capacity", "revenue_estimate", "upkeep", "operating", "cash_remedies"),
	"projects": ("committed_cost", "legacy_projects"),
	"knowledge": ("tree_nodes",),
	"markets": ("agent_rate", "agent_credit_room", "agent_economy_opened", "agent_economy", "household_bill_per_person"),
}

_LIVE = dict(cached=False)
_SEAT = dict(cached=False, seat_scoped=True)

MODULE_SPECS = (ModuleSpec(
	"finance", Finance, seat_state=FinanceSeat,
	publishes=(
		ViewSpec("market_rate", "market_rate", **_LIVE),
		ViewSpec("credit_room", "credit_room", kind=QUOTE),
		ViewSpec("state_lending", "state_lending", **_LIVE),
		ViewSpec("households_loanable_funds", "households_loanable_funds", **_LIVE),
		ViewSpec("lent_share", "lent_share", **_LIVE),
		ViewSpec("capital_market_report", "capital_market_report", **_SEAT),
		ViewSpec("debt_status", "debt_status", **_SEAT),
		ViewSpec("debt_interest_rate", "debt_interest_rate", **_SEAT),
		ViewSpec("debt_service_share_of_surplus", "debt_service_share_of_surplus", **_LIVE),
		ViewSpec("credit_limit", "credit_limit", kind=QUOTE, seat_scoped=True),
		ViewSpec("credit_line_sought", "credit_line_sought", kind=QUOTE, seat_scoped=True),
		ViewSpec("bearable_part_of", "bearable_part_of", kind=QUOTE, seat_scoped=True),
		ViewSpec("spending_power", "spending_power", kind=QUOTE, seat_scoped=True),
		ViewSpec("funding_capacity", "funding_capacity", **_SEAT),
		ViewSpec("funding_breakdown", "funding_breakdown", **_SEAT),
		ViewSpec("living_cost", "living_cost", kind=QUOTE, seat_scoped=True),
		ViewSpec("dependants_beyond_means", "dependants_beyond_means", kind=QUOTE, seat_scoped=True),
		ViewSpec("recurring_living_cost", "recurring_living_cost", kind=QUOTE, seat_scoped=True),
		ViewSpec("recurring_net", "recurring_net", **_SEAT),
		ViewSpec("interest_on_arrears", "interest_on_arrears", **_SEAT),
		ViewSpec("sustainable_debt", "sustainable_debt", **_SEAT),
		ViewSpec("debt_service_forecast", "debt_service_forecast", kind=QUOTE, seat_scoped=True),
		ViewSpec("stall_diagnosis", "stall_diagnosis", **_SEAT),
		ViewSpec("debt_bondage_term_years", "debt_bondage_term_years", **_LIVE),
		ViewSpec("purchase_budget", "purchase_budget", **_SEAT),
		ViewSpec("can_pay", "can_pay", kind=QUOTE, seat_scoped=True),
		ViewSpec("affordable_units", "affordable_units", kind=QUOTE, seat_scoped=True),
		ViewSpec("afford_means", "afford_means", **_LIVE),
		ViewSpec("purchase_refusal", "purchase_refusal", kind=QUOTE, seat_scoped=True),
		ViewSpec("purchase_remedies_text", "purchase_remedies_text", kind=QUOTE, seat_scoped=True),
	),
	applies=(
		(commands.RefreshLenderOffers, "refresh_lender_offers"), (commands.DefaultOnDebt, "apply_default_on_debt"),
		(commands.ChargeInterest, "apply_charge_interest"), (commands.ShedLossMakers, "apply_shed_loss_makers"),
		(commands.WarnNearLimit, "apply_warn_near_limit"), (commands.EnforceCreditLimit, "apply_enforce_credit_limit"),
		(commands.JudgeInsolvency, "judge_insolvency"), (commands.ServeBondageYear, "serve_bondage_year"),
		(commands.NoteLenderPosting, "note_lender_posting"), (commands.FoundBank, "found_bank"),
	),
	phases=(PhaseHook("credit_limit", "step_credit_limit"),),
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
	sends=(RecordEvent, SetReputation, SettleWithEdge, WithdrawHouseholdMoney, MothballMines, BleedStaff, DisperseDependants),
),)
