"""The partner countries that are part of the agent economy: their tiles, people and techniques.

Part of the port. A partner is derived the way the home country is: its people sit on the tiles it holds
(its census when it has one, else its civilisation's population over the tiles by food capacity), its
producers are placed by the economy's own opening from what its people demand and what its techniques
allow, and its prices and wages are the economy's. Nothing about output or wages is authored here."""
from sim.constants import declare
from sim.geography.api import haversine_km, tile_facts, tiles_held
from sim.geography import settlement
from sim.world import census as census_module, demand

from .data import load_civ
from .economy_port_setup import allowed_entries

SPREAD_BY_FOOD_CAPACITY = declare(
    "PARTNER_POPULATION_SPREAD_BY_FOOD_CAPACITY", 1.0, kind="temporary_heuristic",
    unit="share of a census-less partner's population placed by food capacity", source=None, confidence="D",
    why="A partner with no census has its civilisation's population spread over the tiles it holds in "
        "proportion to their food capacity, all of it; real settlement also follows rivers, cities and "
        "ports. Replaced per country by a sourced census (data/world/census) as one is found.")
POPULATION_BY_FOOD_CAPACITY = "food capacity (heuristic)"


def partner_opening(sim, partner_id):
    """What the setup takes from one partner at the opening: its tiles (those the home country does not
    hold), the people on each, the recipes its techniques allow and its goods priced where the home has none."""
    civ = load_civ(partner_id)
    home_tiles = set(tiles_held(sim.civ, sim.world_map))
    tile_ids = [tile for tile in tiles_held(civ, sim.world_map) if tile not in home_tiles]
    people, farthest, source = _people_by_tile(sim, civ, tile_ids)
    production = demand.production_data()
    return {"tiles": tile_ids, "population_by_tile": people, "population_source": source,
            "farthest_seat_km": farthest,
            "recipes": allowed_entries(production, set(civ["starting_techs"])),
            "prices": _partner_prices(sim, partner_id)}


def _people_by_tile(sim, civ, tile_ids):
    census_id = civ.get("population_census")
    if census_id and tile_ids:
        entries = census_module.load_census(census_id)["entries"]
        located = {tile: (tile_facts(tile, sim.world_map)["lat"], tile_facts(tile, sim.world_map)["lon"]) for tile in tile_ids}
        people, farthest = census_module.place_on_nearest_tile(entries, located, haversine_km)
        return {tile: people.get(tile, 0.0) for tile in tile_ids}, farthest, census_id
    total = float(civ.get("population") or 0.0) * SPREAD_BY_FOOD_CAPACITY
    return ({tile: total * settlement.population_share(tile_ids, tile) for tile in tile_ids}, 0.0,
            POPULATION_BY_FOOD_CAPACITY)


def _partner_prices(sim, partner_id):
    """The partner's solved prices in home money, for the goods only it can price."""
    facts = sim._foreign_economy_facts(partner_id)
    home = sim.economy.material_prices()
    return {good: price for good, price in facts["prices_in_home_money"].items()
            if price > 0.0 and not home.get(good)}
