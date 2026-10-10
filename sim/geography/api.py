"""The geography package's only door: everything outside code may use from sim/geography/.

Outside code imports from here and reaches the simulation's geography through `sim.geography`
(a `Geography`, built by sim/engine/geography_port.py), never through a submodule or a private name.
"""
WALL = "two-way"  # nothing here reaches sim/engine/; the engine hands it what it needs (sim/engine/geography_port.py)

# tile_lookup and the queries first: regions pulls in sim.world modules that import them back from this module.
from sim.geography import tile_lookup
from sim.geography import queries
from sim.geography.queries import (build_requirements, built_km, carriage_rates, deposit_records, edge_key, draw_wild_stock, endowment, food_potential, freight_links, game_food_sources, hunted_kcal, regrow_wild_stock, improvement_key, train_carrier, worked_deposits, working_rate_tonnes_per_year, ore_tonnes_per_tonne,
                                   dues_hours_per_tonne, heuristic_parameters, known_deposits, layer_value, mined_before, map_of_tiles, mine_demand_goods, open_map, ore_goods, parameter_value, problems,
                                   prospect, reach, resource_ids, resources_at, route, route_costs, stand, supports,
                                   tile_facts, tile_ids, regions_of_tiles, tiles_held, tiles_of_regions, works_priced_from_deposits,
                                   usable_modes)
from sim.geography import (cargo_cost, climate_temperatures, crop_climate, freight_cost, map_data_sources, mineral_shares, provisions, regions,
                           sea_freight, settlement, territory, tile_names, transport)
from sim.geography.climate_temperatures import (KOPPEN_TROPICAL_COLDEST_MONTH_MINIMUM_CELSIUS, daily_temperatures,
                                                representative_extremes)
from sim.geography.carriage_reach import MARKET_AREA_THRESHOLD_SHARE, MEAN_DISTANCE_IN_DISC, market_radius_km, realm_span_km
from sim.geography.distance import haversine_km
from sim.geography.geography import Geography
from sim.geography.loading import load_geography

__all__ = ["Geography", "load_geography", "haversine_km", "MARKET_AREA_THRESHOLD_SHARE", "MEAN_DISTANCE_IN_DISC",
           "market_radius_km", "realm_span_km", "KOPPEN_TROPICAL_COLDEST_MONTH_MINIMUM_CELSIUS",
           "daily_temperatures", "representative_extremes", "cargo_cost", "climate_temperatures", "crop_climate",
           "freight_cost", "map_data_sources", "mineral_shares", "provisions", "regions", "sea_freight", "settlement", "territory", "tile_lookup",
           "tile_names", "transport",
           # the contract (sim/geography/INTERFACE.md); everything above is older surface outside it
           "queries", "build_requirements", "built_km", "carriage_rates", "open_map", "tile_ids", "tiles_held", "tiles_of_regions", "regions_of_tiles", "tile_facts", "layer_value", "food_potential", "hunted_kcal", "game_food_sources", "draw_wild_stock", "regrow_wild_stock", "usable_modes", "dues_hours_per_tonne", "route", "improvement_key", "train_carrier", "worked_deposits", "working_rate_tonnes_per_year", "ore_tonnes_per_tonne",
           "reach", "route_costs", "map_of_tiles", "freight_links", "edge_key", "resource_ids", "resources_at", "endowment", "known_deposits",
           "deposit_records", "mined_before", "prospect", "supports", "stand", "problems", "heuristic_parameters", "ore_goods",
           "works_priced_from_deposits", "mine_demand_goods", "parameter_value"]
