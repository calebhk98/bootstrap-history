"""The actors module's spec (sim/assembly).

The records of every actor beside the founder's households are saved in the world slot (`ActorsState`). Every read is a view of
an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_actors.py and the other bridge files) under the
name the owner will publish, or a view of a module that has moved. Grouped by owner. The `legacy_*` names are the owners' raw
objects the actors still hold in place: the seats' registry, the acting seat's projects and household facade, the map and the
constants `Sim` still declares."""
from sim.assembly.api import KEYED, ModuleSpec, ViewSpec
from sim.agents.api import ActorsState
from sim.coin.api import ChargeActorsTheft, ChargeKeeping
from sim.finance.api import DefaultOnDebt, RefreshLenderOffers
from sim.foreign_trade.api import NoteActorHomeTrade, NoteActorTrade, NoteCargoLeg
from sim.freight.api import PayRouteDues
from sim.markets.api import ForgetActorOrders, NoteActorPurchase, NoteActorSale
from sim.polity.api import AddScandal
from sim.production.api import AccrueExperience
from sim.reporting.api import RecordEvent
from sim.workforce.api import ReleaseStaff

from . import commands
from .module import Actors

READS_BY_OWNER = {
	"core": ("year", "civilisation", "game_setting", "shared_answers", "legacy_constant", "legacy_act_as", "actor_kinds_registered",
	         "opening_cast", "money_text", "mass_rate_text"),
	"seats": ("acting_seat", "acting_country", "seat_list", "legacy_seats", "seat_place", "seat_party", "legacy_household_actor",
	          "disclosure", "disclosures"),
	"knowledge": ("tree_nodes", "techniques_granted", "legacy_projects", "held_techniques", "legacy_world_map"),
	"diffusion": ("copy_difficulty", "knowledge_half_life_years", "literacy", "research_productivity", "diffusible_ids"),
	"polity": ("state_authority", "state_trait_weights", "visible_scale", "levy_shares", "notice_over", "patron_clients",
	           "patron_funding_ask", "military_equipment_burden", "standing"),
	"ledger": ("transfer_listening",),
	"workforce": ("trade_available", "trade_population", "reachable_trade_population", "people_who_exist", "taught_trade_people",
	              "available_trades", "is_craft_trade", "market_supply", "local_market_share", "base_tile", "trades_absent",
	              "labour_market", "money_per_labour_hour", "hours_per_person_year"),
	"projects": ("project_cost", "effective_risk", "is_venture", "seat_review", "revenue_estimate", "upkeep", "credit_limit"),
	"production": ("concern_takings", "concern_gross", "concern_upkeep", "node_output_market_factor", "concern_volume_ratio",
	               "concern_staff", "concern_baskets_now", "industry_depth", "industry_scale_ceiling", "ramp_share_at_full_depth",
	               "basket_market_factor", "unit_mass_kg"),
	"markets": ("goods_category_factor", "goods_category_factor_with_entrants", "goods_category_price_ratio", "goods_category_state",
	            "nodes_in_category", "market_state", "commodities_sold_by_acting_party", "economy_output_value", "coin_stock_value",
	            "main_material_of", "material_trade_quote", "material_purchase_cost", "household_prices", "household_basket",
	            "agent_trades_good", "agent_price_response", "agent_country", "agent_cohort_incomes", "agent_cohort_land_rents",
	            "agent_need_floor_costs", "agent_land_rent_at", "agent_land_rent_paid_by_tile", "agent_land_rent_per_hectare",
	            "agent_output_tonnes_by_tile", "agent_idle_hours_by_trade", "agent_fugitive_share_by_tile", "country_opening_basket",
	            "country_volume_baseline", "country_traded_volumes", "fleet_goods", "goods_carried_last_year"),
	"finance": ("credit_room", "state_lending", "debt_interest_rate", "debt_service_share_of_surplus", "market_rate"),
	"materials": ("material_commodity", "material_substitutes", "material_prices", "materials_serving", "materials_without_a_seller"),
	"demography": ("population_total", "working_age", "urban_fraction", "people_by_tile", "nutrition_ratio_last_year",
	               "frontier_disease_loss"),
	"land": ("home_tiles_held",),
	"agriculture": ("farm_holdings", "farm_food_demand_kg"),
	"mechanics": ("nodes_with_mechanic", "state_military_diffusion"),
	"foreign_trade": ("foreign_economies", "partner_facts", "partner_book_entry", "partner_price_per_unit", "partner_price_response",
	                  "partner_household_demand", "actor_home_trade", "landed_cost", "trade_value_in_year", "not_traded_materials",
	                  "home_household_tonnes", "border_duty_per_tonne"),
}

# Nothing here is cached: the cast is read in place and written by the actors' own turn and by legacy code behind the views.
_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
	"actors", Actors, world_state=ActorsState,
	publishes=(
		ViewSpec("cast", "cast", **_LIVE),
		ViewSpec("cast_state", "cast_state", **_LIVE),
		ViewSpec("state_treasury", "state_treasury", seat_scoped=True, **_LIVE),
		ViewSpec("seeded_actor_registry", "seeded_actor_registry", **_LIVE),
		ViewSpec("legacy_edge_account", "edge", kind=KEYED, **_LIVE),
		ViewSpec("actor_world", "actor_world", **_LIVE),
		ViewSpec("country_world", "country_world", kind=KEYED, **_LIVE),
		ViewSpec("concern_counts", "actor_concerns_in", kind=KEYED, **_LIVE),
		ViewSpec("concern_versions", "concern_versions", **_LIVE),
		ViewSpec("actor_staff", "actor_staff_fte", kind=KEYED, **_LIVE),
		ViewSpec("actor_staff_nationwide", "actor_staff_nationwide", kind=KEYED, **_LIVE),
		ViewSpec("actor_staff_total", "actor_staff_total", **_LIVE),
		ViewSpec("country_strata", "country_strata", kind=KEYED, **_LIVE),
	),
	applies=((commands.AdvanceActors, "advance_actors"), (commands.RecordConquestContact, "record_conquest_contact"),
	         (commands.RecordMigrantContact, "record_migrant_contact"), (commands.ScaleStrata, "scale_strata"), (commands.NoteTraderMargin, "note_trader_margin")),
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
	sends=(ChargeKeeping, ChargeActorsTheft, RefreshLenderOffers, DefaultOnDebt, AccrueExperience, ForgetActorOrders, NoteActorSale,
	       NoteActorPurchase, ReleaseStaff, NoteActorHomeTrade, NoteActorTrade, NoteCargoLeg, PayRouteDues, AddScandal, RecordEvent),
),)
