"""The actors module's spec (sim/assembly).

The records of every actor beside the founder's households are saved in the world slot (`ActorsState`). Every read is a view of
an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_*.py) under the
name the owner will publish, or a view of a module that has moved. Grouped by owner. The `legacy_*` names are the owners' raw
objects the actors still hold in place: the seats' registry, the acting seat's projects, the map and the constants `Sim` still declares.
The module builds the seats as parties to the exchange (seat_parties.py) from the views and commands of the modules that own what a seat
holds, and applies the commands that address the exchange to a seat (seat_exchange.py)."""
from sim.assembly.api import FIRST, KEYED, LIST, QUOTE, ExtensionPoint, ModuleSpec, Provision, ViewSpec
from sim.agents.api import ActorsState
from sim.coin.api import ChargeActorsTheft, ChargeKeeping
from sim.finance.api import DefaultOnDebt, RefreshLenderOffers
from sim.foreign_trade.api import NoteActorHomeTrade, NoteActorTrade, NoteCargoLeg
from sim.freight.api import PayRouteDues
from sim.knowledge.api import ReceiveTechniques
from sim.ledger.api import CreditSeat, DebitSeat, NoteSeatCash, PayActor, RestorePurse
from sim.markets.api import ForgetActorOrders, NoteActorPurchase, NoteActorSale
from sim.polity.api import AddScandal
from sim.production.api import AccrueExperience
from sim.reporting.api import RecordEvent
from sim.seats.api import AnswerOffer, ApplyForPatent, MakeOffer, SetDealing
from sim.ventures.api import AdoptPlant, ReleasePlant
from sim.workforce.api import ReleaseStaff

from . import commands
from .module import Actors

READS_BY_OWNER = {
	"markets": ("unit_mass_kg", "goods_categories", "goods_category_factor", "goods_category_factor_with_entrants",
	            "goods_category_price_ratio", "goods_category_state", "nodes_in_category", "market_state", "commodities_sold_by_acting_party",
	            "economy_output_value", "coin_stock_value", "main_material_of", "material_trade_quote", "material_purchase_cost",
	            "household_prices", "household_basket", "agent_trades_good", "agent_price_response", "agent_country", "agent_cohort_incomes",
	            "agent_cohort_land_rents", "agent_need_floor_costs", "agent_land_rent_at", "agent_land_rent_paid_by_tile",
	            "agent_land_rent_per_hectare", "agent_output_tonnes_by_tile", "agent_idle_hours_by_trade", "agent_fugitive_share_by_tile",
	            "country_opening_basket", "country_volume_baseline", "country_traded_volumes", "fleet_goods", "goods_carried_last_year",
	            "material_substitutes", "materials_serving", "partner_household_demand", "home_household_tonnes", "border_duty_per_tonne"),
	"workforce": ("staff", "trade_available", "trade_population", "reachable_trade_population", "people_who_exist", "taught_trade_people",
	              "available_trades", "is_craft_trade", "market_supply", "local_market_share", "base_tile", "labour_market",
	              "money_per_labour_hour", "hours_per_person_year", "staff_on_all_books"),
	"production": ("is_venture", "revenue_estimate", "upkeep", "concern_takings", "concern_gross", "concern_upkeep",
	               "node_output_market_factor", "concern_volume_ratio", "concern_baskets_now", "industry_depth", "industry_scale_ceiling",
	               "ramp_share_at_full_depth", "basket_market_factor"),
	"polity": ("state_funding_terms", "state_authority", "state_trait_weights", "visible_scale", "levy_shares", "notice_over",
	           "patron_clients", "patron_funding_ask", "military_equipment_burden", "standing"),
	"foreign_trade": ("partners", "foreign_economies", "partner_facts", "partner_book_entry", "partner_price_per_unit",
	                  "partner_price_response", "actor_home_trade", "landed_cost", "trade_value_in_year"),
	"diffusion": ("disclosure", "disclosures", "copy_difficulty", "knowledge_half_life_years", "literacy", "research_productivity",
	              "diffusible_ids", "diffusion_index"),
	"seats": ("acting_seat", "acting_country", "seat_list", "seat_country", "seats_holding_patent", "seat_place", "seat_dealings", "dealings_listing"),
	"demography": ("pop_scale_for", "population_total", "working_age", "urban_fraction", "people_by_tile", "nutrition_ratio_last_year", "farm_holdings"),
	"scenario": ("year", "civilisation", "game_setting", "opening_civilisation", "civilisation_record", "money_text", "mass_rate_text"),
	"finance": ("credit_limit", "credit_room", "state_lending", "debt_interest_rate", "debt_service_share_of_surplus", "market_rate"),
	"ventures": ("operating", "operating_by_seat", "venture_opened_year", "venture_size", "concern_staff"),
	"knowledge": ("tree_nodes", "techniques_held", "techniques_granted", "techniques_by_seat"),
	"projects": ("substitute_quality_discount", "project_cost", "effective_risk", "seat_review"),
	"content": ("declared_actor_kinds", "trades_absent", "not_traded_materials"),
	"land": ("home_tiles_held", "home_modes", "reach_days"),
	"ledger": ("transfer_listening", "seat_balance", "acting_balance"),
	"materials": ("material_commodity", "materials_without_a_seller"),
	"agriculture": ("farm_food_demand_kg",),
	"disease": ("frontier_disease_loss",),
	"mechanics": ("mechanic",),
	"prices": ("material_prices",),
	"sharing": ("shared_answers",),
}

# Nothing here is cached: the cast is read in place and written by the actors' own turn and by legacy code behind the views.
_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
	"actors", Actors, world_state=ActorsState,
	publishes=(
		ViewSpec("cast", "cast", **_LIVE),
		ViewSpec("cast_state", "cast_state", **_LIVE),
		ViewSpec("cast_recorded", "cast_recorded", **_LIVE),
		ViewSpec("society_techs", "society_techs", seat_scoped=True, **_LIVE),
		ViewSpec("government_figures", "government_figures", kind=KEYED, **_LIVE),
		ViewSpec("lender_offers_made", "lender_offers_made", **_LIVE),
		ViewSpec("cash_and_deposit", "cash_and_deposit", kind=KEYED, **_LIVE),
		ViewSpec("loans_out", "loans_out", kind=QUOTE, **_LIVE),
		ViewSpec("debt_owed", "debt_owed", kind=KEYED, **_LIVE),
		ViewSpec("state_treasury", "state_treasury", seat_scoped=True, **_LIVE),
		ViewSpec("seeded_actor_registry", "seeded_actor_registry", **_LIVE),
		ViewSpec("actor_world", "actor_world", **_LIVE),
		ViewSpec("country_world", "country_world", kind=KEYED, **_LIVE),
		ViewSpec("concern_counts", "actor_concerns_in", kind=KEYED, **_LIVE),
		ViewSpec("concern_versions", "concern_versions", **_LIVE),
		ViewSpec("concerns_of_active_firms", "concerns_of_active_firms", **_LIVE),
		ViewSpec("firm_concern_holdings", "firm_concern_holdings", **_LIVE),
		ViewSpec("actor_staff", "actor_staff_fte", kind=KEYED, **_LIVE),
		ViewSpec("actor_staff_nationwide", "actor_staff_nationwide", kind=KEYED, **_LIVE),
		ViewSpec("actor_staff_total", "actor_staff_total", **_LIVE),
		ViewSpec("country_strata", "country_strata", kind=KEYED, **_LIVE),
		ViewSpec("has_state", "has_state", kind=KEYED, **_LIVE),
		ViewSpec("countries", "countries", **_LIVE),
		ViewSpec("organised_factions", "organised_factions", kind=KEYED, **_LIVE),
		ViewSpec("home_country", "home_country", **_LIVE),
		ViewSpec("state_knowledge", "state_knowledge", **_LIVE),
		ViewSpec("holder_treasury", "holder_treasury", kind=KEYED, **_LIVE),
		ViewSpec("teaching_knowledge", "teaching_knowledge", **_LIVE),
		ViewSpec("country_literacy_figure", "country_literacy_figure", kind=QUOTE, **_LIVE),
		ViewSpec("country_literacy_ceiling", "country_literacy_ceiling", kind=QUOTE, **_LIVE),
		ViewSpec("literacy_after_schooling", "literacy_after_schooling", kind=QUOTE, **_LIVE),
		ViewSpec("state_budget_figures", "state_budget_figures", seat_scoped=True, **_LIVE),
		ViewSpec("army_figures", "army_figures", seat_scoped=True, **_LIVE),
		ViewSpec("state_knows", "state_knows", kind=QUOTE, seat_scoped=True),
		ViewSpec("home_strata_rows", "home_strata_rows", **_LIVE),
		ViewSpec("partner_catch_chance", "partner_catch_chance", kind=QUOTE, **_LIVE),
		ViewSpec("harvest_share_taken", "harvest_share_taken", kind=KEYED, **_LIVE),
		ViewSpec("concern_sale_terms", "concern_sale_terms", kind=QUOTE, seat_scoped=True, **_LIVE),
	),
	applies=((commands.AdvanceActors, "advance_actors"), (commands.AddActor, "add_actor"), (commands.RecordConquestContact, "record_conquest_contact"),
	         (commands.RecordMigrantContact, "record_migrant_contact"), (commands.ScaleStrata, "scale_strata"), (commands.MoveStratumPeople, "move_stratum_people"), (commands.NoteTraderMargin, "note_trader_margin"), (commands.HoldEdgeGoods, "hold_edge_goods"), (commands.DrawDownActorStore, "draw_down_actor_store"),
	         (commands.TeachLiteracy, "teach_literacy"), (commands.SchoolLiteracy, "school_literacy"),
	         (commands.FollowTileTransfer, "follow_tile_transfer"),
	         (commands.SetLenderOffers, "set_lender_offers"), (commands.SettleLenderInterest, "settle_lender_interest"),
	         (ApplyForPatent, "apply_for_patent"), (MakeOffer, "make_offer"), (AnswerOffer, "answer_offer"),
	         (commands.GrantLicence, "grant_licence"), (commands.SellSeatConcern, "sell_seat_concern")),
	extension_points=(
		ExtensionPoint("actor_kinds", LIST),           # () -> {kind: the class that builds its actors}; a later answer replaces a kind
		ExtensionPoint("actor_spawners", LIST),        # () -> [(name, function(registry, world) -> ids founded)], run after the actors' turns
		ExtensionPoint("actor_world_scope", FIRST),    # () -> function(world, profile, registry): the world a foreign country's actors see
		ExtensionPoint("actor_policies", LIST),        # () -> {policy kind: factory}
		ExtensionPoint("player_commands", LIST),       # () -> {command name: function(player, order, world) -> detail text}
	),
	provides=(
		Provision("actor_kinds", "shipped_actor_kinds", "kinds"),
		Provision("actor_kinds", "provide_declared_kinds", "declared_kinds"),
		Provision("actor_spawners", "shipped_actor_spawners", "spawners"),
		Provision("actor_world_scope", "shipped_actor_world_scope", "world_scope"),
		Provision("actor_policies", "shipped_actor_policies", "policies"),
		Provision("player_commands", "shipped_player_commands", "commands"),
	),
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
	sends=(ChargeKeeping, ChargeActorsTheft, RefreshLenderOffers, DefaultOnDebt, AccrueExperience, ForgetActorOrders, NoteActorSale,
	       NoteActorPurchase, ReleaseStaff, NoteActorHomeTrade, NoteActorTrade, NoteCargoLeg, PayRouteDues, AddScandal, RecordEvent, PayActor,
	       CreditSeat, DebitSeat, NoteSeatCash, RestorePurse, ReceiveTechniques, SetDealing, ReleasePlant, AdoptPlant),
),)
