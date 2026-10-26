"""The foreign-trade module's spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_foreign_trade.py and
the other bridge files) under the name the owner will publish, except the `legacy_*` ones: raw state the module still reads or
writes in place (the cast of actors, the agent economy's record where the traders' cargo legs are kept, the map handle)."""
from sim.actors.api import NoteTraderMargin
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec
from sim.ledger.api import PayActorFromEdge, PayEdgeFrom

from .commands import (CloseMarketsTo, ClosePartnerBooks, NoteActorHomeTrade, NoteActorTrade, NoteCargoLeg, RecordStockTaken,
                       SettleFlow, SettleTraderCargo)
from .module import ForeignTrade
from .payments import BOOKS
from .state import ForeignTradeWorld

READS_BY_OWNER = {
    "knowledge": ("civilisation", "year", "techniques_held", "partner_reached", "civilisation_record"),
    "seats": ("acting_seat",),
    "prices": ("material_prices", "home_unit_price", "household_prices", "partner_own_economy"),
    "materials": ("material_commodity", "commodity_record", "national_output", "partner_household_demand"),
    "markets": ("market_floor_ratio",),
    "land": ("legacy_world_map", "tracked_materials", "mineral_share_of_tiles"),
    "freight": ("foreign_route", "route_freight_per_tonne", "carrier_models", "material_route", "trader_cost_share",
                "trader_agent_cost", "cargo_lost_share"),
    "coin": ("home_coin_stock", "coin_carriage_units", "partner_coin_opening", "partner_price_level"),
    "finance": ("market_rate",),
    "actors": ("cast", "legacy_agent_economy"),
    "mods": ("foreign_economy_records",),
}

# not cached: the prices, ledgers and cast they are worked from are still written outside their owners' commands, and a few
# of them open a book entry on first use
_LIVE = dict(cached=False, channels=(BOOKS,))

MODULE_SPECS = (ModuleSpec(
    "foreign_trade", ForeignTrade, channels=(BOOKS,), world_state=ForeignTradeWorld,
    publishes=(
        ViewSpec("partners", "partners", **_LIVE),
        ViewSpec("partners_in_agent_economy", "partners_in_agent_economy", **_LIVE),
        ViewSpec("foreign_economies", "foreign_economies", **_LIVE),
        ViewSpec("partner", "partner", kind=KEYED, **_LIVE),
        ViewSpec("partner_coin_standard", "partner_coin_standard", kind=KEYED, **_LIVE),
        ViewSpec("partner_opening_facts", "partner_opening_facts", kind=KEYED, **_LIVE),
        ViewSpec("partner_gate", "partner_gate", kind=QUOTE),
        ViewSpec("partner_refusal", "partner_refusal", kind=QUOTE),
        ViewSpec("partner_facts", "partner_facts", kind=KEYED, **_LIVE),
        ViewSpec("partner_route", "partner_route", kind=KEYED, **_LIVE),
        ViewSpec("commodity_materials", "commodity_materials", kind=KEYED, **_LIVE),
        ViewSpec("foreign_supply_tonnes", "foreign_supply_tonnes", kind=QUOTE),
        ViewSpec("partner_market_book", "partner_market_book", kind=KEYED, **_LIVE),
        ViewSpec("partner_book_entry", "partner_book_entry", kind=QUOTE),
        ViewSpec("route_lift_years_per_tonne", "route_lift_years_per_tonne", kind=QUOTE),
        ViewSpec("route_capital_per_lift_tonne", "route_capital_per_lift_tonne", kind=QUOTE),
        ViewSpec("lift_capacity_tonnes", "lift_capacity_tonnes", kind=QUOTE),
        ViewSpec("lift_left_tonnes", "lift_left_tonnes", kind=QUOTE),
        ViewSpec("opening_carriers_per_route", "opening_carriers_per_route", **_LIVE),
        ViewSpec("foreign_coin_home_units", "foreign_coin_home_units", **_LIVE),
        ViewSpec("foreign_coin_partner_units", "foreign_coin_partner_units", kind=KEYED, **_LIVE),
        ViewSpec("trade_value_in_year", "trade_value_in_year", kind=QUOTE),
        ViewSpec("actor_home_trade", "actor_home_trade", kind=KEYED, **_LIVE),
        ViewSpec("actors_carry", "actors_carry", kind=QUOTE),
        ViewSpec("landed_cost", "landed_cost", kind=QUOTE),
        ViewSpec("partner_price_per_unit", "partner_price_per_unit", kind=QUOTE),
        ViewSpec("partner_price_response", "partner_price_response", kind=QUOTE),
        ViewSpec("partner_landed_price", "partner_landed_price", kind=QUOTE),
        ViewSpec("partner_carry", "partner_carry", kind=QUOTE),
        ViewSpec("cargo_legs", "cargo_legs", **_LIVE),
    ),
    applies=((SettleFlow, "apply_settle_flow"), (RecordStockTaken, "apply_record_stock_taken"),
             (CloseMarketsTo, "apply_close_markets_to"), (NoteActorTrade, "apply_note_actor_trade"),
             (NoteActorHomeTrade, "apply_note_actor_home_trade"), (NoteCargoLeg, "apply_note_cargo_leg"),
             (SettleTraderCargo, "apply_settle_trader_cargo"), (ClosePartnerBooks, "apply_close_partner_books")),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
    sends=(PayActorFromEdge, PayEdgeFrom, NoteTraderMargin),
),)
