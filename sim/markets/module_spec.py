"""The markets module's spec (sim/assembly).

The module owns the book, the year's flows, the agent economy's record and the money flag (`MarketsWorld`), the clearing, the
goods categories, household demand and the market ceiling's attribution. The module builds the goods market and the port over the
agent economy (they read the game through the views declared here, port_world.py), and every view it publishes is uncached: they
write the flows and the record in place."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, PhaseHook, RepriceTree, ViewSpec
from sim.demography.api import MovePeople, RecordFoodEaten
from sim.diffusion.api import NoteFirstRuns
from sim.foreign_trade.api import ResetActorTradeTallies, SettleTraderCargo
from sim.land.api import FinishWays
from sim.ledger.api import ChangeStock, PayEdge, RescaleHouseholdMoney, PayExchange, ReceiveFromEdge, ReceiveFromExchange
from sim.reporting.api import CloseRealOutput, RecordEvent
from sim.workforce.api import ClearingSettled, HoursArrived, NewcomersPlaced, NoteClearedWage, StaffArrived
from sim.resources.api import DrawDeposit, FellTimber, RegrowTimber

from .commands import (BuyMaterial, CancelMaterialOrders, FoundBankFromOutside, ForgetActorOrders, NoteActorPurchase, NoteActorSale,
                       MoveGoods, NoteDraw, RenameMarketSeat, RepriceOpeningMoney, ResetDraws,
                       SellMaterial)
from .kernels import KERNELS
from .module import Markets
from .state import MarketsWorld

READS_BY_OWNER = {
	"core": ("year", "civilisation", "game_config", "output_factor", "installed_mod_ids",
	         "household_need_data",
	         "price_index"),
	"content": ("spoilage_rates", "service_life_years", "household_work_data"),
	"seats": ("seat_list",),
	"assembly": ("registered_seats",),
	"stores": ("store_book",),
	"demography": ("population", "default_population", "regional_people_by_band"),
	"actors": ("country_literacy_figure",),
	"knowledge": ("tree_nodes", "techniques_granted", "category_trait"),
	"ventures": ("operating",),
	"prices": ("commodity_record", "material_prices", "material_pool"),
	"workforce": ("labour_market", "money_per_labour_hour"),
	"production": ("workshop_output", "concern_market", "concern_book_offer", "concern_book_inputs_cost",
	               "techniques_in_use"),
	# what the port and the goods market read of the game (port_world.py)
	"port: seats and actors": ("built_ways",
	                           "cast", "cast_state", "actor_world", "state_treasury", "state_reach", "acting_country"),
	"port: the map": ("map_for_agent_economy", "tiles_listed_by", "tile_description", "tile_climates", "mode_crews", "modes_carrying",
	                  "timber_on_tile", "deposit_catalogue", "deposits_worked_before"),
	"port: workforce": ("base_tile", "farming_technique", "settlement_tiles", "labour_need_shares", "trade_registry",
	                    "hours_per_person_year", "staff_posting", "once_posting", "wage_work_offered", "newcomers",
	                    "employed_by_trade", "trade_schools"),
	"port: money and prices": ("market_rate", "credit_line_sought", "debt_bondage_term_years", "home_coin_stock",
	                           "material_price", "material_commodity_map", "material_market_tonnes", "goods_stock",
	                           "can_pay", "spending_power",
	                           "real_output_hours", "held_techniques", "techniques_spread", "mechanic"),
	"port: foreign trade and freight": ("partner_facts", "partners_in_agent_economy", "civilisation_record",
	                                    "cargo_legs", "freight_mode_costs", "material_carriage_per_tonne"),
	"land": ("home_tiles_held",),
	"port: land, farm and resources": ("farm_sites", "farm_weather", "harvest_weather", "externality_yield_factors", "tile_owner_map",
	                                   "tiles_owned_by", "timber_felled", "found_deposits", "partner_deposits"),
}

_LIVE = dict(cached=False)

# (name, kind) of every view; the module method that computes it has the view's name
_VIEWS = (
	("goods_quote", KEYED), ("goods_categories", None), ("sale_limits", KEYED), ("purchase_quote", QUOTE), ("sale_quote", QUOTE),
	("can_be_bought", KEYED), ("material_seller", KEYED), ("home_unit_price", KEYED),
	("household_prices", None), ("commodities_sold_by_acting_party", None), ("others_trade_stamp", None), ("seat_goods_orders", None), ("seat_goods_traded", None), ("main_material_of", KEYED),
	("market_state", KEYED), ("opening_population", None),
	("nodes_in_category", KEYED),
	("agent_prices", None), ("agent_prices_at", QUOTE), ("agent_seat_sale_outlook", QUOTE),
	("agent_producers_by_good", None), ("agent_producer_runs", None), ("agent_worker_years_by_recipe", None), ("agent_wage_at", QUOTE), ("agent_hours_offered_at", QUOTE), ("agent_working_hours", None), ("agent_people_by_trade", None),
	("agent_people_by_tile_and_trade", None), ("agent_land_rent_per_hectare", None),
	("agent_land_rent_at", QUOTE), ("agent_land_rent_paid_by_tile", None), ("agent_trades_good", KEYED),
	("agent_price_response", QUOTE), ("agent_country", KEYED), ("agent_cohort_incomes", None),
	("agent_cohort_land_rents", QUOTE), ("agent_need_floor_costs", None), ("agent_output_tonnes_by_tile", None),
	("agent_idle_hours_by_trade", None), ("agent_fugitive_share_by_tile", None), ("agent_opening_basket", None),
	("agent_volume_baseline", None), ("agent_traded_volumes", None), ("agent_producer_capacity", KEYED),
	("producers_stamp", None), ("producer_capacities", None), ("goods_carried_last_year", None),
	("country_trade_book", KEYED), ("country_opening_basket", KEYED), ("country_volume_baseline", KEYED), ("country_traded_volumes", KEYED),
	("fleet_goods", QUOTE), ("economy_output_value", None), ("coin_stock_value", None),
	("market_absorption_by_category", QUOTE), ("agent_economy_store", None),
	("money_from_economy", None), ("unit_mass_kg", QUOTE), ("border_duty_per_tonne", QUOTE),
	("household_basket", None), ("home_household_tonnes", QUOTE), 
	("materials_serving", KEYED), ("material_substitutes", KEYED), ("material_serves_a_need", KEYED),
	("agent_rate", None), ("open_agent_economy", None), ("flush_agent_record", None), ("agent_spin_up_result", None),
	("agent_health", QUOTE), ("agent_last_outcome", None), ("agent_trades", None), ("agent_opening_figures", None), ("agent_stale_goods", None),
	("agent_traded_staple", None), ("agent_opening_setup", None), ("agent_credit_room", QUOTE), ("agent_fundable_amount", QUOTE), ("agent_risk_premium", QUOTE), ("agent_lender_listing", None), ("agent_economy_opened", None),
	("household_bill_per_person", None),
)


def _view(name, kind):
	return ViewSpec(name, name, **_LIVE) if kind is None else ViewSpec(name, name, kind=kind, **_LIVE)


MODULE_SPECS = (ModuleSpec(
	"markets", Markets, world_state=MarketsWorld,
	publishes=tuple(_view(name, kind) for name, kind in _VIEWS),
	applies=((ResetDraws, "reset_draws"), (NoteDraw, "note_draw"),
	         (ForgetActorOrders, "forget_actor_orders"), (NoteActorSale, "note_actor_sale"),
	         (NoteActorPurchase, "note_actor_purchase"), (MoveGoods, "move_goods"),
	         (RenameMarketSeat, "rename_market_seat"),
	         (RepriceOpeningMoney, "reprice_opening_money"), (BuyMaterial, "buy_material"),
	         (SellMaterial, "sell_material"), (CancelMaterialOrders, "cancel_material_orders"), (FoundBankFromOutside, "found_bank_from_outside")),
	phases=(PhaseHook("market", "step_market"),),
	kernels=KERNELS,
	reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
	sends=(MovePeople, RecordFoodEaten, ResetActorTradeTallies, CloseRealOutput, FinishWays, RepriceOpeningMoney, RepriceTree, RescaleHouseholdMoney, PayEdge, ReceiveFromEdge, ChangeStock, PayExchange, ReceiveFromExchange,
	       SettleTraderCargo, FellTimber, RegrowTimber, DrawDeposit, NoteFirstRuns, StaffArrived, HoursArrived, ClearingSettled, NewcomersPlaced, NoteClearedWage, RecordEvent),
),)
