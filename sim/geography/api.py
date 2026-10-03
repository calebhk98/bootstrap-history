"""The geography package's only door: everything outside code may use from sim/geography/.

Outside code imports from here and reaches the simulation's geography through `sim.geography`
(port.GeographyPort), never through a submodule or a private name.
"""
# tile_lookup first: regions pulls in sim.world modules that import tile_lookup back from this module.
from sim.geography import tile_lookup
from sim.geography import (cargo_cost, climate_temperatures, crop_climate, freight_cost, regions, sea_freight,
                           settlement, territory, tile_names, trade_routes, transport)
from sim.geography.climate_temperatures import (KOPPEN_TROPICAL_COLDEST_MONTH_MINIMUM_CELSIUS, daily_temperatures,
                                                representative_extremes)
from sim.geography.distance import haversine_km
from sim.geography.geography import GeographyMixin
from sim.geography.port import GeographyPort

__all__ = ["GeographyMixin", "GeographyPort", "haversine_km", "KOPPEN_TROPICAL_COLDEST_MONTH_MINIMUM_CELSIUS",
           "daily_temperatures", "representative_extremes", "cargo_cost", "climate_temperatures", "crop_climate",
           "freight_cost", "regions", "sea_freight", "settlement", "territory", "tile_lookup",
           "tile_names", "trade_routes", "transport"]
