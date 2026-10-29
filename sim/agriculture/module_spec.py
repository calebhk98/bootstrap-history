"""Agriculture's module spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge
under the name the owner will publish, except the game's dice (`game_random`, used in place) and the game itself (`provider_game`, handed to the mods' externality providers)."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, PhaseHook, ViewSpec
from sim.demography.api import ChangeFarmland
from sim.ledger.api import PayEdge, ReceiveFromEdge

from .commands import InvestFarm, RecordOpeningFarm, SellFarm, SetFarmLand, SetFarmTechnique, SetFarmTerritory
from .food import WILD_STOCK
from .module import Agriculture
from .state import AgricultureWorld

READS_BY_OWNER = {
    "knowledge": ("civilisation",),
    "land": ("held_tile_geometry", "crop_sites", "food_kcal_by_source", "game_food_sources", "huntable_kcal", "take_hunt",
             "regrow_wild_stock", "tile_soil_nitrogen_factors", "soil_nitrogen_after_year"),
    "workforce": ("farming_technique", "society_labour_hours", "trade_registry", "money_per_labour_hour"),
    "living_stock": ("society_herds",),
    "demography (externalities)": ("externality",),
    "prices": ("price_index",),
    "ledger": ("acting_balance",),
    "seats": ("game_random",),
    "core": ("provider_game",),
    "demography": ("farm_holdings", "population"),
}

# not cached: they read the engine's household state, the held land or the mods' externalities, written outside any command
_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "agriculture", Agriculture, channels=(WILD_STOCK,), world_state=AgricultureWorld,
    publishes=(
        ViewSpec("farm_weather", "farm_weather", kind=KEYED, **_LIVE),
        ViewSpec("harvest_weather", "harvest_weather", kind=QUOTE),
        ViewSpec("externality_yield_factors", "externality_yield_factors", kind=QUOTE),
        ViewSpec("weather_seed", "weather_seed", kind=QUOTE),   # the first call draws the game's salt from its dice
        ViewSpec("farm_weather_cells", "weather_cells", **_LIVE),
        ViewSpec("farm_sites", "farm_sites", **_LIVE),
        ViewSpec("farm_territory", "farm_territory", **_LIVE),
        ViewSpec("food_potential", "food_potential", **_LIVE),
        ViewSpec("wild_stock", "wild_stock", channels=(WILD_STOCK,)),
        ViewSpec("farm_land_price", "farm_land_price", **_LIVE),
        ViewSpec("farm_land", "farm_land", **_LIVE),
        ViewSpec("farm_technique_this_year", "farm_technique_this_year", **_LIVE),
        ViewSpec("farm_ladder", "farm_ladder", **_LIVE),
        ViewSpec("farm_arable_ceiling", "farm_arable_ceiling", **_LIVE),
        ViewSpec("farm_food_demand_kg", "farm_food_demand_kg", **_LIVE),
        ViewSpec("opening_farmed_hectares", "opening_farmed_hectares", **_LIVE),
    ),
    applies=((InvestFarm, "invest_farm"), (SellFarm, "sell_farm"), (SetFarmLand, "set_farm_land"),
             (SetFarmTechnique, "set_farm_technique"), (SetFarmTerritory, "set_farm_territory"),
             (RecordOpeningFarm, "record_opening_farm")),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
    sends=(ChangeFarmland, PayEdge, ReceiveFromEdge),
    phases=(PhaseHook("wild_stock", "step_wild_stock"), PhaseHook("soil_nitrogen", "step_soil_nitrogen")),
),)
