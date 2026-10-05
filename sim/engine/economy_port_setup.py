"""Builds the agent economy's setup from a simulation's opening state. Part of the port: with
economy_port.py, the only engine modules that import `sim.economy`.

The tree's knowledge stays here: which production entries the society can run is decided by the
nodes it holds; the economy only receives the recipes.
"""
import dataclasses
import json
import os

from sim.economy.api import (EconomySetup, TradeSpec, currency_from_coin_standard, goods_specs, households,
                             recipes_from_production_data, taxes, tile_costs)
from sim.world import demand
from sim.geography.api import layer_value, sea_freight, settlement, tiles_of_regions
from sim.labour import api as labour_api

from .foreign_routes import SEA_MODE

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")


def _load(*parts):
    with open(os.path.join(DATA_DIR, *parts), encoding="utf-8") as handle:
        return json.load(handle)


def civilisation_tiles(civ, world_map):
    """The tiles a civilisation holds on the engine's map (through its home regions until civilisations
    hold tiles), and that map."""
    return tiles_of_regions(list(civ.get("home_regions") or []), world_map), world_map


def allowed_entries(production, held_nodes):
    """Production entries the society can run: those needing no node, or a node it holds."""
    return sorted(entry_id for entry_id, entry in production.items()
                  if not entry_id.startswith("_") and isinstance(entry, dict)
                  and (entry.get("requires_node") is None or entry.get("requires_node") in held_nodes))


def unskilled_trade(trades_data):
    """The trade anyone can take up at once, which the labour package names from the trade registry."""
    return labour_api.fallback_trade(labour_api.trade_specs(trades_data))


def opening_values(sim):
    """What the setup takes from the engine at the opening: kept in the save so a resumed game rebuilds
    the same markets, producers and price base however the engine's own tables have moved since."""
    civ = sim.civ
    tile_ids, _world_map = civilisation_tiles(civ, sim.world_map)
    home = list(civ.get("home_regions") or [])
    people = float(sim.population.total)
    production = demand.production_data()
    trades_data = _load("world", "trades.json").get("trades", {})
    allowed = allowed_entries(production, set(sim.state.projects.granted))
    unskilled = unskilled_trade(trades_data)
    labour_trades = sorted({trade for entry_id in allowed for trade in (production[entry_id].get("labour_hours") or {})}
                           | {unskilled})
    modes = sim._freight_mode_costs()
    return {
        "population_by_tile": {tile: people * settlement.population_share(home, tile) for tile in tile_ids},
        "working_share": sim.population.working_age / people if people > 0.0 else 0.0,
        "recipes": allowed,
        "prices": {good: price for good, price in sim.economy.material_prices().items() if price > 0.0},
        "wages": {trade: sim.economy.labour.quote(trade) for trade in labour_trades if trade in trades_data},
        "unskilled_trade": unskilled,
        "rate": float(sim.economy.base_rate()),
        "carriage": dict(modes),
        "held_nodes": sorted(sim.state.projects.done | sim.state.projects.granted),
    }


def baskets_by_tile(basket, need_data, world_map, tile_ids):
    """The household basket on each tile, with the floors its climate sets (sim/world/climate_needs.py)
    for every need whose data names one in `subsistence_from_climate`."""
    from sim.world import climate_needs
    climate_field = {need_id: spec.get("subsistence_from_climate")
                     for need_id, spec in need_data.get("needs", {}).items() if spec.get("subsistence_from_climate")}
    if not climate_field:
        return {}
    baskets = {}
    for tile in tile_ids:
        floors = climate_needs.floors_for_tile({
            "lat": layer_value(tile, "lat", world_map),
            "koppen_class": layer_value(tile, "koppen_class", world_map),
            "koppen_sample_mix": layer_value(tile, "koppen_sample_mix", world_map)})
        needs = tuple(dataclasses.replace(need, subsistence_per_person=float(floors[climate_field[need.need_id]]))
                      if need.need_id in climate_field else need for need in basket.needs)
        baskets[tile] = dataclasses.replace(basket, needs=needs)
    return baskets


def coin_per_unit(opening):
    """The economy counts money in opening unskilled labour hours: one unit is what an hour of it paid
    at the opening, in coin. So the economy is the same whatever the coin, and the port converts."""
    return float(opening["wages"][opening["unskilled_trade"]])


def in_units(opening):
    """The opening values with every money figure counted in the economy's unit; the spun-up economy
    is cached under these, so games that differ only in their coin share one."""
    unit = coin_per_unit(opening)
    counted = dict(opening)
    counted["prices"] = {good: _counted(price / unit) for good, price in opening["prices"].items()}
    counted["wages"] = {trade: _counted(wage / unit) for trade, wage in opening["wages"].items()}
    counted["carriage"] = {mode: _counted(rate / unit) for mode, rate in opening["carriage"].items()}
    return counted


def _counted(value):
    """A money figure in the economy's unit, to twelve significant digits: dividing by a different
    coin leaves the last digits different, and the economy amplifies any difference over the years."""
    return float("%.12g" % value)


def build_setup(sim, opening=None):
    """The economy's setup from the opening values (`opening_values(sim)` when none are given), with
    money counted in the economy's unit (`coin_per_unit`)."""
    opening = opening or opening_values(sim)
    unit = coin_per_unit(opening)
    opening = in_units(opening)
    civ = sim.civ
    tile_ids, world_map = civilisation_tiles(civ, sim.world_map)
    tiles = tile_costs.tiles_from_map(world_map, tile_ids)
    population_by_tile = {tile: float(opening["population_by_tile"].get(tile, 0.0)) for tile in tile_ids}
    production = demand.production_data()
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
        currency=_counted_currency(civ, unit),
        state_agent="state:" + str(civ["id"]), tiles=tiles,
        carriage_rates=dict(opening["carriage"]),
        handling_rates={SEA_MODE: sea_freight.PORT_HANDLING_HOURS_PER_TONNE * wages.get(opening["unskilled_trade"], 0.0)},
        held_nodes=tuple(opening["held_nodes"]),
        specs=specs, recipes=recipes, basket=basket, trades=trades,
        tax_forms=taxes.forms_from_civ_data(civ.get("state_revenue") or []),
        state_capacity=min(1.0, max(0.0, float(civ.get("state_capacity", 1.0)))),
        working_hours_per_year=float(sim.HOURS_PER_PERSON_YEAR), working_share=float(opening["working_share"]),
        gini=demand.GINI_COEFFICIENT_PREINDUSTRIAL_AGRARIAN, opening_population_by_tile=population_by_tile,
        unskilled_trade=opening["unskilled_trade"], opening_prices=prices, opening_wages=wages, opening_rate=float(opening["rate"]),
        capital_tile=by_people[0], port_tile=(coastal or by_people)[0],
        land_per_run={recipe_id: float(production[recipe_id].get("land_hectare_years") or 0.0)
                      for recipe_id in recipes if production[recipe_id].get("land_hectare_years")},
        basket_by_tile=baskets_by_tile(basket, need_data, world_map, tile_ids), coin_per_unit=unit,
        world_map=world_map)


def _counted_currency(civ, unit):
    """The civilisation's money as the economy counts it: one unit is `unit` coins, so it holds that
    many coins' metal."""
    spec = currency_from_coin_standard(str(civ["id"]), civ["coin_standard"], str(civ.get("currency", "")),
                                       issuer="state:" + str(civ["id"]))
    return dataclasses.replace(spec, backing_per_unit=spec.backing_per_unit * unit)
