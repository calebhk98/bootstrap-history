"""Builds the agent economy's setup from a simulation's opening state. Part of the port: with
economy_port.py, the only engine modules that import `sim.economy`.

The tree's knowledge stays here: which production entries the society can run is decided by the
nodes it holds; the economy only receives the recipes.
"""
import json
import os

from sim.economy import households, taxes, tile_costs
from sim.economy.currency import currency_from_coin_standard
from sim.economy.setup import EconomySetup, TradeSpec, goods_specs
from sim.world import demand, land, settlement

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
FREIGHT_MODE_OF_CARRIER = {"cart": tile_costs.DRAUGHT_MODE, "caravan": tile_costs.PACK_MODE,
                           "sea": tile_costs.SEA_MODE}


def _load(*parts):
    with open(os.path.join(DATA_DIR, *parts), encoding="utf-8") as handle:
        return json.load(handle)


def civilisation_tiles(civ):
    """The tiles a civilisation holds (through its home regions until civilisations hold tiles)."""
    geography = _load("world", "geography.json")
    return land._tile_ids_for_home_regions(list(civ.get("home_regions") or []), geography.get("land_tiles", {})), geography


def allowed_entries(production, held_nodes):
    """Production entries the society can run: those needing no node, or a node it holds."""
    return sorted(entry_id for entry_id, entry in production.items()
                  if not entry_id.startswith("_") and isinstance(entry, dict)
                  and (entry.get("requires_node") is None or entry.get("requires_node") in held_nodes))


def opening_values(sim):
    """What the setup takes from the engine at the opening: kept in the save so a resumed game rebuilds
    the same markets, producers and price base however the engine's own tables have moved since."""
    civ = sim.civ
    tile_ids, _geography = civilisation_tiles(civ)
    home = list(civ.get("home_regions") or [])
    people = float(sim.population.total)
    production = demand.production_data()
    trades_data = _load("world", "trades.json").get("trades", {})
    allowed = allowed_entries(production, set(sim.state.projects.granted))
    labour_trades = sorted({trade for entry_id in allowed for trade in (production[entry_id].get("labour_hours") or {})}
                           | {"labourer"})
    modes = sim._freight_mode_costs()
    return {
        "population_by_tile": {tile: people * settlement.population_share(home, tile) for tile in tile_ids},
        "working_share": sim.population.working_age / people if people > 0.0 else 0.0,
        "recipes": allowed,
        "prices": {good: price for good, price in sim.economy.material_prices().items() if price > 0.0},
        "wages": {trade: sim.economy.labour.quote(trade) for trade in labour_trades if trade in trades_data},
        "rate": float(sim.economy.base_rate()),
        "carriage": {FREIGHT_MODE_OF_CARRIER[mode]: rate for mode, rate in modes.items()
                     if mode in FREIGHT_MODE_OF_CARRIER},
    }


def build_setup(sim, opening=None):
    """The economy's setup from the opening values (`opening_values(sim)` when none are given)."""
    opening = opening or opening_values(sim)
    civ = sim.civ
    tile_ids, geography = civilisation_tiles(civ)
    tiles = tile_costs.tiles_from_geography(geography, tile_ids)
    population_by_tile = {tile: float(opening["population_by_tile"].get(tile, 0.0)) for tile in tile_ids}
    production = demand.production_data()
    from sim.economy.recipes import recipes_from_production_data
    recipes = recipes_from_production_data(production, opening["recipes"])
    need_data = _load("world", "needs.json")
    basket = households.make_basket(need_data, production)
    goods = set()
    for recipe in recipes.values():
        goods.update(recipe.outputs, recipe.inputs, recipe.plant_goods)
    for need in basket.needs:
        goods.update(good for good, _effect in need.goods)
    spoilage = _load("world", "spoilage.json").get("rates_per_year", {})
    specs = goods_specs({good: "" for good in goods}, spoilage)
    prices = {good: price for good, price in opening["prices"].items() if good in specs and price > 0.0}
    trades_data = _load("world", "trades.json").get("trades", {})
    trades = {trade: TradeSpec(trade, float(spec.get("training_years", 0.0)))
              for trade, spec in sorted(trades_data.items())}
    wages = dict(opening["wages"])
    by_people = sorted(tile_ids, key=lambda tile: (-population_by_tile[tile], tile))
    coastal = [tile for tile in by_people if tiles[tile].coastal]
    return EconomySetup(
        civ_id=str(civ["id"]),
        currency=currency_from_coin_standard(str(civ["id"]), civ["coin_standard"], str(civ.get("currency", "")),
                                             issuer="state:" + str(civ["id"])),
        state_agent="state:" + str(civ["id"]), tiles=tiles, edges=tile_costs.build_edges(tiles),
        carriage_rates=dict(opening["carriage"]),
        handling_rates=tile_costs.handling_money_per_tonne_by_mode(wages.get("labourer", 0.0)),
        specs=specs, recipes=recipes, basket=basket, trades=trades,
        tax_forms=taxes.forms_from_civ_data(civ.get("state_revenue") or []),
        state_capacity=min(1.0, max(0.0, float(civ.get("state_capacity", 1.0)))),
        working_hours_per_year=float(sim.HOURS_PER_PERSON_YEAR), working_share=float(opening["working_share"]),
        gini=demand.GINI_COEFFICIENT_PREINDUSTRIAL_AGRARIAN, opening_population_by_tile=population_by_tile,
        opening_prices=prices, opening_wages=wages, opening_rate=float(opening["rate"]),
        capital_tile=by_people[0], port_tile=(coastal or by_people)[0],
        land_per_run={recipe_id: float(production[recipe_id].get("land_hectare_years") or 0.0)
                      for recipe_id in recipes if production[recipe_id].get("land_hectare_years")})
