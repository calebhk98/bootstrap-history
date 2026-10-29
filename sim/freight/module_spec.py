"""The freight module's spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_*.py
and bridge_shared.py) under the name the owner will publish, except the `legacy_*` one: the map handle the geography
package's searches take."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec
from sim.ledger.api import PayActor

from .commands import PayRouteDues
from .module import Freight

READS_BY_OWNER = {
    "knowledge": ("civilisation", "year"),
    "workforce": ("wage", "hour_wage", "hours_per_person_year", "trade_population"),
    "finance": ("market_rate", "households_loanable_funds"),
    "prices": ("material_prices", "material_price"),
    "land": ("legacy_world_map", "held_techniques", "techniques_with_results", "built_ways", "tile_owner", "material_source_tiles", "route_km_to"),
    "markets": ("goods_carried_last_year",),
    "demography": ("working_age",),
    "foreign_trade": ("foreign_economies", "partner_market_book", "partner_route", "route_lift_years_per_tonne",
                      "route_capital_per_lift_tonne", "lift_capacity_tonnes", "opening_carriers_per_route"),
    "polity": ("holder_treasury",),
}

# not cached: the prices, wages, ways and ledgers they are worked from are still written outside their owners' commands
_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "freight", Freight,
    publishes=(
        ViewSpec("carrier_models", "carrier_models", **_LIVE),
        ViewSpec("freight_mode_costs", "freight_mode_costs", kind=QUOTE),
        ViewSpec("freight_handling_costs", "freight_handling_costs", **_LIVE),
        ViewSpec("foreign_route", "foreign_route", kind=QUOTE),
        ViewSpec("route_freight_per_tonne", "route_freight_per_tonne", kind=QUOTE),
        ViewSpec("material_route", "material_route", kind=QUOTE),
        ViewSpec("tile_haul_cost", "tile_haul_cost", kind=QUOTE),
        ViewSpec("partner_route_cost", "partner_route_cost", kind=KEYED, **_LIVE),
        ViewSpec("material_carriage_per_tonne", "material_carriage_per_tonne", kind=QUOTE),
        ViewSpec("material_freight_factor", "material_freight_factor", kind=KEYED, **_LIVE),
        ViewSpec("trader_margin_share", "trader_margin_share", kind=QUOTE),
        ViewSpec("cargo_lost_share", "cargo_lost_share", kind=QUOTE),
        ViewSpec("trader_cycle_years", "trader_cycle_years", kind=QUOTE),
        ViewSpec("trader_agent_cost", "trader_agent_cost", kind=QUOTE),
        ViewSpec("trader_cost_share", "trader_cost_share", kind=QUOTE),
    ),
    applies=((PayRouteDues, "pay_route_dues"),),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
    sends=(PayActor,),
),)
