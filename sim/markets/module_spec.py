"""The markets module's spec (sim/assembly).

The module owns the book, the year's flows, the agent economy's record and the money flag (`MarketsWorld`), the clearing, the
goods categories, household demand and the market ceiling's attribution. The module builds the goods market and the port over the
agent economy (they read the game through the views declared here, port_world.py), and every view it publishes is uncached: they
write the flows and the record in place."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, PhaseHook, ViewSpec
from sim.demography.api import RecordFoodEaten
from sim.diffusion.api import NoteFirstRuns
from sim.foreign_trade.api import ClosePartnerBooks, SettleFlow, SettleTraderCargo
from sim.land.api import FinishWays
from sim.ledger.api import ChangeStock, PayEdge, PayExchange, ReceiveFromEdge, ReceiveFromExchange
from sim.reporting.api import CloseRealOutput
from sim.resources.api import DrawDeposit, FellTimber, RegrowTimber

from .commands import (BuyMaterial, FoundBankFromOutside, ForgetActorOrders, MarkMoneyPricedAtEconomy, NoteActorPurchase, NoteActorSale,
                       NoteDraw, NotePurchase, OpenMarketBook, RenameMarketSeat, RepriceOpeningMoney, ResetDraws, ResetMarketCaches,
                       SellMaterial)
from .kernels import KERNELS
from .module import Markets
from .state import MarketsWorld

READS_BY_OWNER = {
	"core": ("year", "civilisation", "game_config", "legacy_tree", "output_factor", "opening_farmed_hectares", "installed_mod_ids",
	         "household_need_data",
	         "price_index", "acting_as"),
	"seats": ("seat_list",),
	"demography": ("population", "population_total", "pop_scale", "default_population", "farm_holdings"),
	"actors": ("concern_versions", "concern_counts"),
	"mechanics": ("effect_factor",),
	"knowledge": ("tree_nodes", "done_year", "techniques_held", "techniques_granted"),
	"projects": ("held_and_running_versions", "operating", "venture_opened_year"),
	"prices": ("society_output", "concern_offers", "commodity_record", "commodity_floor_ratio", "material_prices", "material_pool",
	           "calculated_goods_prices"),
	"materials": ("material_commodity",),
	"reporting": ("real_output_per_head",),
	"workforce": ("labour_market", "money_per_labour_hour"),
	"production": ("workshop_output", "concern_market", "concern_book_offer", "concern_book_inputs_cost", "concern_takings",
	               "node_output_market_factor", "techniques_in_use"),
	# what the port and the goods market read of the game (port_world.py)
	"port: seats and actors": ("legacy_seats", "legacy_projects", "built_ways", "legacy_world_map", "legacy_edge_account",
	                           "cast", "cast_state", "actor_world", "state_treasury", "state_reach", "acting_country"),
	"port: workforce": ("base_tile", "farming_technique", "wage", "settlement_tiles", "labour_need_shares", "trade_registry",
	                    "hours_per_person_year"),
	"port: money and prices": ("market_rate", "credit_room", "credit_line_sought", "debt_bondage_term_years", "home_coin_stock",
	                           "price_tables", "material_price", "material_commodity_map", "material_market_tonnes", "goods_stock",
	                           "commodity_materials", "not_traded_materials", "can_pay", "project_cost",
	                           "real_output_hours", "literacy", "held_techniques", "techniques_spread", "mechanic"),
	"port: foreign trade and freight": ("foreign_economies", "partner", "partner_facts", "partners_in_agent_economy", "civilisation_record",
	                                    "foreign_supply_tonnes", "lift_left_tonnes", "partner_price_per_unit", "actors_carry",
	                                    "cargo_legs", "foreign_route", "freight_mode_costs", "material_carriage_per_tonne",
	                                    "trader_margin_share", "cargo_lost_share", "trader_cycle_years", "trader_agent_cost",
	                                    "partner_price_level", "partner_coin_opening", "foreign_coin_partner_units", "border_terms", "partner_own_economy"),
	"port: land, farm and resources": ("farm_sites", "farm_weather", "harvest_weather", "externality_yield_factors", "tile_owner_map",
	                                   "tiles_owned_by", "timber_felled", "found_deposits", "partner_deposits"),
}

_LIVE = dict(cached=False)

# (name, kind) of every view; the module method that computes it has the view's name
_VIEWS = (
	("goods_quote", KEYED), ("sale_limits", KEYED), ("material_trade_quote", KEYED), ("material_purchase_cost", QUOTE), ("purchase_quote", QUOTE),
	("can_be_bought", KEYED), ("material_seller", KEYED), ("partner_import", KEYED), ("home_unit_price", KEYED),
	("household_prices", None), ("commodities_sold_by_acting_party", None), ("main_material_of", KEYED),
	("market_state", KEYED), ("market_floor_ratio", KEYED), ("opening_population", None), ("new_goods_units", None),
	("goods_category_factor", QUOTE), ("goods_category_factor_with_entrants", QUOTE), ("goods_category_price_ratio", KEYED),
	("goods_category_state", KEYED), ("nodes_in_category", KEYED), ("actor_supply", KEYED), ("actor_demand", KEYED),
	("agent_prices", None), ("agent_prices_at", QUOTE), ("agent_seat_sale_outlook", QUOTE),
	("agent_producers_by_good", None), ("agent_worker_years_by_recipe", None), ("agent_wage", KEYED), ("agent_unskilled_wage", None), ("agent_people_by_trade", None),
	("agent_people_by_tile_and_trade", None), ("agent_land_rent", None), ("agent_land_rent_per_hectare", None),
	("agent_land_rent_at", QUOTE), ("agent_land_rent_paid_by_tile", None), ("agent_trades_good", KEYED),
	("agent_price_response", QUOTE), ("agent_country", KEYED), ("agent_cohort_incomes", None),
	("agent_cohort_land_rents", QUOTE), ("agent_need_floor_costs", None), ("agent_output_tonnes_by_tile", None),
	("agent_idle_hours_by_trade", None), ("agent_fugitive_share_by_tile", None), ("agent_opening_basket", None),
	("agent_volume_baseline", None), ("agent_traded_volumes", None), ("agent_producer_capacity", KEYED),
	("producers_stamp", None), ("producer_capacities", None), ("goods_carried_last_year", None),
	("country_opening_basket", KEYED), ("country_volume_baseline", KEYED), ("country_traded_volumes", KEYED),
	("fleet_goods", QUOTE), ("economy_output_value", None), ("coin_stock_value", None),
	("market_entry", KEYED), ("goods_category_ratios", QUOTE), ("essential_price_ratio", None),
	("market_absorption_by_category", QUOTE), ("legacy_market_flows", None), ("legacy_agent_economy", None),
	("money_from_economy", None), ("unit_mass_kg", QUOTE), ("border_duty_per_tonne", QUOTE),
	("household_demand_units", QUOTE), ("household_basket", None), ("home_household_tonnes", QUOTE), ("partner_household_demand", KEYED),
	("materials_serving", KEYED), ("material_substitutes", KEYED), ("material_serves_a_need", KEYED),
	("agent_rate", None), ("agent_credit_room", QUOTE), ("agent_economy_opened", None),
	("household_need_floors_per_person", None), ("household_bill_per_person", None),
)


def _view(name, kind):
	return ViewSpec(name, name, **_LIVE) if kind is None else ViewSpec(name, name, kind=kind, **_LIVE)


MODULE_SPECS = (ModuleSpec(
	"markets", Markets, world_state=MarketsWorld,
	publishes=tuple(_view(name, kind) for name, kind in _VIEWS),
	applies=((ResetDraws, "reset_draws"), (NoteDraw, "note_draw"), (NotePurchase, "note_purchase"),
	         (ForgetActorOrders, "forget_actor_orders"), (NoteActorSale, "note_actor_sale"),
	         (NoteActorPurchase, "note_actor_purchase"), (ResetMarketCaches, "reset_market_caches"),
	         (OpenMarketBook, "open_market_book_command"), (RenameMarketSeat, "rename_market_seat"),
	         (MarkMoneyPricedAtEconomy, "mark_money_priced_at_economy"), (BuyMaterial, "buy_material"),
	         (SellMaterial, "sell_material"), (FoundBankFromOutside, "found_bank_from_outside")),
	phases=(PhaseHook("market", "step_market"),),
	kernels=KERNELS,
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
	sends=(RecordFoodEaten, ClosePartnerBooks, CloseRealOutput, FinishWays, RepriceOpeningMoney, PayEdge, ReceiveFromEdge, ChangeStock, PayExchange, ReceiveFromExchange,
	       SettleFlow, SettleTraderCargo, FellTimber, RegrowTimber, DrawDeposit, NoteFirstRuns),
),)
