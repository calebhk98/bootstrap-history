"""The geography contract: every question the rest of the game asks about places, in plain data.

Arguments and answers are ids, numbers, strings, lists and dicts, so another implementation (a
finer map, a fantasy map, another language) can answer the same calls. `sim/geography/INTERFACE.md`
describes each answer's shape. Every call takes an optional `world_map` from `open_map`; without
one it uses the base map.
"""
import copy
import math
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from sim.geography import (food_capacity, map_source, mechanisms, parameters, resource_links, resources_biotic,
                           resources_catalogue, resources_endowment, resources_mined, resources_prospecting,
                           resources_summary, routes_carriage, routes_graph, routes_modes, routes_search, tile_holdings, tile_layers,
                           ways_build, ways_works)

WorldMap = map_source.WorldMap


def open_map(mods: Iterable[Tuple[str, str]] = ()) -> WorldMap:
    """The base map with each mod's overlay merged, mods given as (mod_id, mod_root) in load order."""
    return map_source.load_map(tuple(mods))


def _map(world_map: Optional[WorldMap]) -> WorldMap:
    return world_map if world_map is not None else map_source.load_map()


def tile_ids(world_map: Optional[WorldMap] = None) -> List[str]:
    return sorted(_map(world_map).tiles)


def tile_facts(tile_id: str, world_map: Optional[WorldMap] = None) -> Dict[str, Any]:
    """{id, lat, lon, land_area_km2, coastal, neighbours, climate_class, region}."""
    world_map = _map(world_map)
    tile = world_map.tiles[tile_id]
    return {"id": tile_id, "lat": tile["lat"], "lon": tile["lon"], "land_area_km2": tile["land_area_km2"],
            "coastal": bool(tile.get("coastal")), "neighbours": list(tile.get("borders", [])),
            "climate_class": tile_layers.value(world_map, tile_id, "koppen_class"),
            "region": tile_layers.value(world_map, tile_id, "region")}


def layer_value(tile_id: str, layer_id: str, world_map: Optional[WorldMap] = None) -> Any:
    """A per-tile value by name (measured layer, tile field or derived rule), or None."""
    return tile_layers.value(_map(world_map), tile_id, layer_id)


def food_potential(tile_id: str, technique_factors: Optional[Mapping[str, float]] = None,
                   world_map: Optional[WorldMap] = None) -> Dict[str, Any]:
    """Sustainable food energy of a tile by source, and the people it feeds."""
    return food_capacity.food_potential(_map(world_map), tile_id, dict(technique_factors or {}) or None)


def tiles_held(civilisation: Mapping[str, Any], world_map: Optional[WorldMap] = None) -> List[str]:
    """The tiles a civilisation holds: its `home_tiles` when it lists them, else the tiles its `home_regions`
    labels name. Sorted; a tile the map lacks is not held."""
    return tile_holdings.tiles_held(civilisation, _map(world_map))


def tiles_of_regions(region_labels: Iterable[str], world_map: Optional[WorldMap] = None) -> List[str]:
    """Sorted tiles carrying any of these region labels (unknown labels add none)."""
    return tile_holdings.tiles_of_regions(region_labels, _map(world_map))


def regions_of_tiles(tile_ids: Iterable[str], world_map: Optional[WorldMap] = None) -> List[str]:
    """Sorted region labels the tiles carry (labels only; a region owns no data)."""
    return tile_holdings.regions_of_tiles(tile_ids, _map(world_map))


def usable_modes(known_nodes_per_party: Iterable[Iterable[str]], world_map: Optional[WorldMap] = None) -> List[str]:
    """Route modes every party can use, from the tech nodes each holds."""
    return sorted(routes_modes.usable_modes(_map(world_map), known_nodes_per_party))


def dues_hours_per_tonne(world_map: Optional[WorldMap] = None) -> Dict[str, float]:
    """{mode_id: labour-hours of tolls or port dues per tonne, charged each time a haul changes to the mode}."""
    return {mode_id: float(mode.get("dues_hours_per_tonne", 0.0))
            for mode_id, mode in sorted(routes_modes.modes(_map(world_map)).items())}


def carriage_rates(mode_ids: Iterable[str], world_map: Optional[WorldMap] = None) -> Dict[str, Dict[str, Any]]:
    """{mode_id: {crew_trade, crew_hours_per_tonne_km, handling_hours_per_tonne, edge_classes}} on level ground
    for the modes that name a crew trade."""
    return routes_carriage.carriage_rates(_map(world_map), mode_ids)


def route(origin_tiles: Iterable[str], destination_tiles: Iterable[str], modes: Iterable[str],
          improvements: Optional[Mapping[str, Mapping[str, Any]]] = None,
          mode_costs: Optional[Mapping[str, float]] = None, handling_costs: Optional[Mapping[str, float]] = None,
          held_nodes: Optional[Iterable[str]] = None, world_map: Optional[WorldMap] = None,
          fastest: bool = False) -> Optional[Dict[str, Any]]:
    """The least-cost haul between two sets of tiles (the fewest-days one with `fastest`), or None when
    nothing joins them."""
    return routes_search.route(_map(world_map), origin_tiles, destination_tiles, modes, improvements,
                               mode_costs, handling_costs, held_nodes, fastest)


def route_costs(origin_tiles: Iterable[str], modes: Iterable[str],
                improvements: Optional[Mapping[str, Mapping[str, Any]]] = None,
                mode_costs: Optional[Mapping[str, float]] = None, handling_costs: Optional[Mapping[str, float]] = None,
                held_nodes: Optional[Iterable[str]] = None, world_map: Optional[WorldMap] = None) -> Dict[str, float]:
    """{tile: least cost per tonne} from any origin tile to every tile a haul reaches, as `route` prices it."""
    return routes_search.costs_from(_map(world_map), origin_tiles, modes, improvements,
                                    mode_costs, handling_costs, held_nodes)


def map_of_tiles(tile_records: Mapping[str, Mapping[str, Any]], world_map: Optional[WorldMap] = None) -> WorldMap:
    """A map of just these tiles ({id: {lat, lon, coastal, borders, ...}}) with the base map's carriage
    modes, sea lanes and parameters, for a scenario or test that places its own tiles."""
    return map_source.map_of_tiles(tile_records, _map(world_map))


def reach(origin_tiles: Iterable[str], modes: Iterable[str], days_budget: float,
          improvements: Optional[Mapping[str, Mapping[str, Any]]] = None, held_nodes: Optional[Iterable[str]] = None,
          world_map: Optional[WorldMap] = None) -> Dict[str, float]:
    """{tile: fewest days} within a travel-time budget."""
    return routes_search.reach(_map(world_map), origin_tiles, modes, days_budget, improvements,
                               held_nodes=held_nodes)


def freight_links(mode_ids: Iterable[str], world_map: Optional[WorldMap] = None) -> List[Tuple[str, str, str, float]]:
    """(tile_a, tile_b, mode, km) for every edge these modes use without anything built."""
    return routes_graph.links(_map(world_map), tuple(mode_ids))


def build_requirements(tile_a: str, tile_b: Optional[str], improvement: str,
                       world_map: Optional[WorldMap] = None) -> Optional[Dict[str, Any]]:
    """What building `improvement` ("road", "rail", "canal", "bridge") over the land edge between two
    bordering tiles takes, or a "port" on one coastal tile (`tile_b` the same tile or None):
    {km, grade, trade, labour_hours, materials: {material: tonnes}, node, build_years, engineered,
    crew_people, crew_hours_per_year}, or None when it cannot be built. Ground steeper than the way's
    natural limit is built `engineered` at more earthwork."""
    return ways_build.requirements(_map(world_map), tile_a, tile_b, improvement)


def improvement_key(improvement: str, tile_a: str, tile_b: str, world_map: Optional[WorldMap] = None) -> str:
    """The key a built `improvement` is recorded under: the tile id for a port, else the edge key."""
    return ways_works.key_of(_map(world_map), improvement, tile_a, tile_b)


def built_km(improvements: Mapping[str, Mapping[str, Any]], improvement: str,
             world_map: Optional[WorldMap] = None) -> float:
    """Kilometres of `improvement` ("road", "rail", "canal"; a bridge's span or a port's quay for those works)
    the caller's `improvements` record holds."""
    return ways_build.built_km(_map(world_map), improvements, improvement)


def edge_key(tile_a: str, tile_b: str) -> str:
    """The key an improvement (a built road or track) between two tiles is stored under."""
    return routes_graph.edge_key(tile_a, tile_b)


def resource_ids(world_map: Optional[WorldMap] = None) -> List[str]:
    return sorted(_map(world_map).catalogue("resources"))


def resources_at(tile_id: str, world_map: Optional[WorldMap] = None) -> Dict[str, Dict[str, Any]]:
    """What lies in or grows on a tile: endowment of each deposit resource and each stand."""
    return resources_summary.resources_at(_map(world_map), tile_id)


def endowment(tile_id: str, resource_id: str, world_map: Optional[WorldMap] = None) -> Dict[str, Any]:
    """Known and expected undiscovered quantity of a resource in a tile."""
    return resources_endowment.endowment(_map(world_map), tile_id, resource_id)


def known_deposits(resource_id: str, world_map: Optional[WorldMap] = None) -> List[Dict[str, Any]]:
    return resources_catalogue.known_deposits(_map(world_map), resource_id)


def deposit_records(resource_id: Optional[str] = None, world_map: Optional[WorldMap] = None) -> List[Dict[str, Any]]:
    """Catalogue rows of the known deposits as copied dicts, every field the data carries, for one resource or all.

    Sorted by the row's `order` field (rows without one after those with one), then by id.
    """
    rows = [copy.deepcopy(row) for row in _map(world_map).catalogue("deposits").values()
            if resource_id is None or row.get("resource") == resource_id]
    return sorted(rows, key=lambda row: (row.get("order", math.inf), row["id"]))


def ore_goods(world_map: Optional[WorldMap] = None) -> Dict[str, Dict[str, Tuple[str, ...]]]:
    """{resource id: {ore good: smelting recipe ids in order of preference}} for the resources that yield ore goods."""
    return resource_links.ore_goods(_map(world_map))


def mine_demand_goods(world_map: Optional[WorldMap] = None) -> Dict[str, Tuple[str, ...]]:
    """{resource id: goods whose demand a mine of it supplies}, from the catalogue rows that name them."""
    return resource_links.mine_demand_goods(_map(world_map))


def works_priced_from_deposits(world_map: Optional[WorldMap] = None) -> Tuple[str, ...]:
    """Resource ids whose mine running cost comes from the deposits' physical works."""
    return resource_links.works_priced_from_deposits(_map(world_map))


def parameter_value(parameter_id: str, world_map: Optional[WorldMap] = None) -> Any:
    """The value of one of the map's parameters."""
    return parameters.parameter(_map(world_map), parameter_id)


def mined_before(tile_ids: Iterable[str], resource_id: str, year: int,
                 world_map: Optional[WorldMap] = None) -> Dict[str, Any]:
    """What the known deposits of a resource in these tiles had yielded by `year`: {workings, unworked,
    deposits_in_tiles, unit}, a working being {id, tile_id, output_per_year, years_worked, years_since_last_output}
    in the resource's unit. Deposits with no working date are listed in `unworked`, never guessed."""
    return resources_mined.mined_before(_map(world_map), tile_ids, resource_id, year)


def prospect(tile_id: str, resource_id: str, effort: float, seed: Any,
             world_map: Optional[WorldMap] = None) -> List[Dict[str, Any]]:
    """Hidden deposits found with `effort` person-days; the same seed and effort give the same finds."""
    return resources_prospecting.prospect(_map(world_map), tile_id, resource_id, effort, seed)


def supports(tile_id: str, resource_id: str, world_map: Optional[WorldMap] = None) -> float:
    """0 to 1: how well a tile suits a living resource (a forest, a fibre plant)."""
    return resources_biotic.supports(_map(world_map), tile_id, resource_id)


def stand(tile_id: str, resource_id: str, world_map: Optional[WorldMap] = None) -> Dict[str, Any]:
    """Area, standing stock and regrowth of a living resource on a tile."""
    return resources_biotic.stand(_map(world_map), tile_id, resource_id)


def problems(world_map: Optional[WorldMap] = None) -> List[str]:
    """Everything wrong with the map's data, as messages; empty when sound."""
    world_map = _map(world_map)
    found = ["parameter %r lacks a value, kind, source or reason" % parameter_id
             for parameter_id in parameters.invalid_entries(world_map)]
    found += ["resource %r names an unknown mechanism" % row_id for row_id in mechanisms.unknown_rows(world_map)]
    found += ["route mode %r is incomplete" % mode_id for mode_id in routes_modes.invalid_entries(world_map)]
    found += resources_catalogue.validate(world_map)
    return found


def heuristic_parameters(world_map: Optional[WorldMap] = None) -> List[str]:
    """Ids of the map's parameters still marked as heuristics, for the burndown."""
    return [entry["id"] for entry in parameters.heuristics(_map(world_map))]
