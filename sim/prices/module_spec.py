"""The prices module's spec (sim/assembly).

Every read is a view of an owner that has not moved yet, published by the engine bridge (sim/engine/bridge_prices.py and the
files it names) under the name the owner will publish. No view of the module is cached: the techniques, the projects and the
economy behind them are written outside any command of the owners."""
from sim.assembly.api import KEYED, QUOTE, ModuleSpec, ViewSpec

from .module import Prices

READS_BY_OWNER = {
    "knowledge": ("civilisation", "year", "techniques_granted", "legacy_projects", "operating"),
    "production": ("techniques_in_use", "price_epoch", "is_venture", "concern_baskets_now", "venture_ramp"),
    "finance": ("market_rate",),
    "workforce": ("money_per_labour_hour", "hour_wage", "farm_land_hectares"),
    "markets": ("household_prices", "material_seller", "agent_wage", "agent_land_rent", "producers_stamp"),
    "materials": ("material_pool",),
}

# not cached: the techniques, the projects and the economy are written by code outside the owners' commands
_LIVE = dict(cached=False)

MODULE_SPECS = (ModuleSpec(
    "prices", Prices,
    publishes=(
        ViewSpec("material_prices", "material_prices", **_LIVE),
        ViewSpec("material_price", "material_price", kind=KEYED, **_LIVE),
        ViewSpec("price_tables", "price_tables", **_LIVE),
        ViewSpec("material_price_basis", "material_price_basis", kind=KEYED, **_LIVE),
        ViewSpec("price_index", "price_index", **_LIVE),
        ViewSpec("commodity_record", "commodity_record", kind=KEYED, **_LIVE),
        ViewSpec("material_commodity_map", "material_commodity_map", **_LIVE),
        ViewSpec("commodity_country_output", "commodity_country_output", kind=QUOTE, **_LIVE),
        ViewSpec("commodity_floor_ratio", "commodity_floor_ratio", kind=KEYED, **_LIVE),
        ViewSpec("concern_offers", "concern_offers", kind=QUOTE, **_LIVE),
        ViewSpec("done_memo", "done_memo", kind=QUOTE, **_LIVE),
        ViewSpec("producers_memo", "producers_memo", kind=QUOTE, **_LIVE),
    ),
    reads=tuple(name for names in READS_BY_OWNER.values() for name in names),
),)
