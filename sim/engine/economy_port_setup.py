"""Builds the agent economy's setup from a simulation's opening state. Part of the port: with
economy_port.py, the only engine modules that import `sim.economy`.

The tree's knowledge stays here: which production entries the society can run is decided by the
nodes it holds; the economy only receives the recipes.
"""
import dataclasses
import json
import os
from typing import Dict

from sim.economy.api import (EconomySetup, carriage_wear, SiteLimit, TradeSpec, currency_from_coin_standard, goods_specs, households, households_work,
                             plant_builds, recipe_tile_key,
                             recipes_from_production_data, taxes, tile_costs, with_tool_wear)
from sim.agents import api as agents_api
from sim.world import demand, need_basket
from sim.geography.api import carriage_rates, layer_value, sea_freight, settlement, tiles_held
from sim.labour import api as labour_api

from . import economy_port_closure, economy_port_costs, economy_port_sites
from .economy_port_stores import opening_store_values
from .foreign_routes import SEA_MODE

ARABLE_SOURCE = "arable land"   # the production entries' `extracted_from` for crops (some add a note after it)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")


def _load(*parts):
    with open(os.path.join(DATA_DIR, *parts), encoding="utf-8") as handle:
        return json.load(handle)


_UNIT_MASS_KG: Dict[str, float] = {}


def unit_mass_kg(material: str) -> float:
    """Kilograms in one unit of a material, as the freight model reads it (stated, then inferred from the id)."""
    if material not in _UNIT_MASS_KG:
        _UNIT_MASS_KG[material] = goods_specs({material: ""}, {})[material].unit_mass_kg
    return _UNIT_MASS_KG[material]


def civilisation_tiles(civ, world_map):
    """The tiles a civilisation holds on the engine's map, and that map."""
    return tiles_held(civ, world_map), world_map


def _runnable(entry, held_nodes):
    return entry.get("requires_node") is None or entry.get("requires_node") in held_nodes


def allowed_entries(production, held_nodes):
    """Production entries the society's producers can run: those needing no node, or a node it holds.
    An entry whose `actor` is the mint is the mint's way of striking coin, not a firm's."""
    return sorted(entry_id for entry_id, entry in production.items()
                  if not entry_id.startswith("_") and isinstance(entry, dict)
                  and entry.get("actor") != "mint" and _runnable(entry, held_nodes))


def mint_recipe_id(civ, production, held_nodes):
    """The production entry the coin standard names for striking its coin, when the society can run it."""
    entry_id = civ.get("coin_standard", {}).get("mint_recipe")
    entry = production.get(entry_id) if entry_id else None
    return entry_id if isinstance(entry, dict) and entry.get("actor") == "mint" and _runnable(entry, held_nodes) else None


def unskilled_trade(trades_data):
    """The trade anyone can take up at once, which the labour package names from the trade registry."""
    return labour_api.fallback_trade(labour_api.trade_specs(trades_data))


def partner_openings(sim):
    """{partner id: its tiles, people and recipes} for the partners that are part of the agent economy."""
    from .economy_port_partners import partner_opening
    return {partner: partner_opening(sim, partner) for partner in sim.partners_in_agent_economy()}


LITERACY_FIELDS = ("literacy_general", "literacy_elite")


def opening_values(sim):
    """What the setup takes from the engine at the opening: kept in the save so a resumed game rebuilds
    the same markets, producers and price base however the engine's own tables have moved since."""
    civ = sim.civ
    tile_ids, _world_map = civilisation_tiles(civ, sim.world_map)
    people = float(sim.population.total)
    production = demand.production_data()
    trades_data = _load("world", "trades.json").get("trades", {})
    allowed = allowed_entries(production, set(sim.state.projects.granted))
    mint_recipe = mint_recipe_id(civ, production, set(sim.state.projects.granted))
    unskilled = unskilled_trade(trades_data)
    partners = partner_openings(sim)
    partner_prices = {}
    for opened in partners.values():
        partner_prices.update(opened.pop("prices"))
    everyone_runs = sorted(set(allowed).union(*(opened["recipes"] for opened in partners.values())))
    labour_trades = sorted({trade for entry_id in everyone_runs + ([mint_recipe] if mint_recipe else [])
                            for trade in (production[entry_id].get("labour_hours") or {})}
                           | {unskilled})
    modes = sim._freight_mode_costs(cargo="goods")
    rates = carriage_rates(sorted(modes), sim.world_map)
    prices = dict(partner_prices)
    prices.update(economy_port_costs.opening_costs(sim))
    return {
        "partners": partners,
        "population_by_tile": {tile: people * settlement.population_share(tile_ids, tile) for tile in tile_ids},
        "working_share": sim.population.working_age / people if people > 0.0 else 0.0,
        "recipes": allowed,
        "mint_recipe": mint_recipe,
        "prices": prices,
        "wages": {trade: sim.economy.labour.quote(trade) for trade in labour_trades if trade in trades_data},
        "unskilled_trade": unskilled,
        "need_shares": sim.labour.need_shares(),
        "rate": float(sim.economy.base_rate()),
        "carriage": dict(modes),
        "carriage_balanced": sim._freight_mode_costs(0.0, cargo="goods"),
        "carriage_wage": sim.labour.wage_per_hour(sim.FREIGHT_DRIVER_WAGE_TRADE),
        "carriage_crew": {mode: [rate["crew_trade"], rate["crew_hours_per_tonne_km"]]
                          for mode, rate in rates.items()},
        "carriage_handling_trade": {mode: rate["handling_trade"] for mode, rate in rates.items() if rate.get("handling_trade")},
        "carriage_feed_good": sim.FREIGHT_FEED_PRICE_MATERIAL,
        "carriage_teams": {mode: {key: rate[key] for key in ("carriers", "tonne_km_per_team_day", "team_payload_tonnes", "animal_feed_kg_per_tonne_km")}
                           for mode, rate in rates.items()},
        "held_nodes": sorted(sim.held_and_running(include_starting=False)),
        "ways": {key: dict(way) for key, way in sorted(sim.state.economy.improvements.items())},
        "site_limits": [[limit.recipe_id, limit.tile, limit.capacity_runs_per_year, limit.yield_factor]
                        for limit in economy_port_sites.site_limits(
                            sim, {entry_id: production[entry_id]["outputs"] for entry_id in allowed},
                            list(tile_ids) + [tile for opened in partners.values() for tile in opened["tiles"]])],
        "stores": opening_store_values(sim.world_map, tile_ids, int(sim.cfg["start_year"])),
        "literacy": {field: sim.literacy(field) for field in LITERACY_FIELDS},
    }


def society_at_opening(civ, opening):
    """The civilisation's fields with the literacy the opening saved, so a setup rebuilt after literacy has moved scales the
    needs as the first setup did."""
    return dict(civ, **opening["literacy"])


def baskets_by_tile(basket, need_data, world_map, tile_ids):
    """The household basket on each tile, with the floors its climate sets (sim/world/climate_needs.py)
    for every need whose data names one in `subsistence_from_climate`."""
    if not need_basket.climate_floor_fields(basket):
        return {}
    return {tile: need_basket.climate_basket(basket, {
        "lat": layer_value(tile, "lat", world_map),
        "koppen_class": layer_value(tile, "koppen_class", world_map),
        "koppen_sample_mix": layer_value(tile, "koppen_sample_mix", world_map)}) for tile in tile_ids}


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
    counted["carriage_wage"] = _counted(opening["carriage_wage"] / unit)
    counted["carriage_balanced"] = {mode: _counted(rate / unit) for mode, rate in opening["carriage_balanced"].items()}
    return counted


def _counted(value):
    """A money figure in the economy's unit, to twelve significant digits: dividing by a different
    coin leaves the last digits different, and the economy amplifies any difference over the years."""
    return float("%.12g" % value)


def build_setup(sim, opening=None, production=None):
    """The economy's setup from the opening values (`opening_values(sim)` when none are given), with
    money counted in the economy's unit (`coin_per_unit`). `production` is the catalogue the recipes are
    read from (the shared production data when none is given)."""
    opening = opening or opening_values(sim)
    unit = coin_per_unit(opening)
    opening = in_units(opening)
    civ = sim.civ
    tile_ids, world_map = civilisation_tiles(civ, sim.world_map)
    partners = opening.get("partners") or {}
    all_tile_ids = list(tile_ids) + [tile for opened in partners.values() for tile in opened["tiles"]]
    cropped_share = 1.0 - sim.labour.farming_technique().rotation.fallow_share_of_holding
    tiles = tile_costs.tiles_from_map(world_map, all_tile_ids, cropped_share)
    for partner_id, opened in partners.items():
        for tile in opened["tiles"]:
            tiles[tile] = dataclasses.replace(tiles[tile], country=partner_id)
    population_by_tile = {tile: float(opening["population_by_tile"].get(tile, 0.0)) for tile in tile_ids}
    for opened in partners.values():
        population_by_tile.update({tile: float(people) for tile, people in opened["population_by_tile"].items()})
    production = production or demand.production_data()
    every_recipe = sorted(set(opening["recipes"]).union(*(opened["recipes"] for opened in partners.values())))
    recipes = recipes_from_production_data(production, every_recipe)
    trades_data = _load("world", "trades.json").get("trades", {})
    life_years = {good: float(entry["years"]) for good, entry in _load("world", "service_lives.json").get("years", {}).items()}
    recipes = tool_wear_recipes(recipes, trades_data, life_years, float(sim.HOURS_PER_PERSON_YEAR))
    mint_recipe = (recipes_from_production_data(production, [opening["mint_recipe"]])[opening["mint_recipe"]]
                   if opening.get("mint_recipe") else None)
    need_data = _load("world", "needs.json")
    basket = households.make_basket(need_data, production, civ_values=society_at_opening(civ, opening))
    goods = set()
    for recipe in recipes.values():
        goods.update(recipe.outputs, recipe.inputs, recipe.plant_goods)
    for need in basket.needs:
        goods.update(good for good, _effect in need.goods)
    spoilage = _load("world", "spoilage.json").get("rates_per_year", {})
    service_lives = {good: float(entry["years"])
                     for good, entry in _load("world", "service_lives.json").get("years", {}).items()}
    specs = goods_specs({good: "" for good in goods}, spoilage, service_lives)
    prices = {good: price for good, price in opening["prices"].items() if good in specs and price > 0.0}
    prices = economy_port_closure.makeable_prices(prices, production, recipes)
    recipes = {recipe_id: plant_builds.with_plant_from(recipe, prices) for recipe_id, recipe in recipes.items()}
    trades = {trade: TradeSpec(trade, float(spec.get("training_years", 0.0)),
                               float(spec.get("fatality_risk_per_year", 0.0)), str(spec.get("family", "")))
              for trade, spec in sorted(trades_data.items())}
    wages = dict(opening["wages"])
    by_people = sorted(tile_ids, key=lambda tile: (-population_by_tile[tile], tile))   # the home country's tiles
    coastal = [tile for tile in by_people if tiles[tile].coastal]
    return EconomySetup(
        civ_id=str(civ["id"]),
        currency=_counted_currency(civ, unit),
        state_agent="state:" + str(civ["id"]), tiles=tiles,
        carriage_rates=dict(opening["carriage"]), carriage_rates_balanced=dict(opening["carriage_balanced"]),
        handling_rates={SEA_MODE: sea_freight.PORT_HANDLING_HOURS_PER_TONNE * wages.get(opening["unskilled_trade"], 0.0)},
        carriage_wage=float(opening["carriage_wage"]),
        carriage_crew={mode: (str(crew[0]), float(crew[1])) for mode, crew in opening["carriage_crew"].items()},
        carriage_carriers=carriage_wear.table(
            opening["carriage_teams"],
            {good: production[good]["carrier_use"] for good in sorted(specs) if production.get(good, {}).get("carrier_use")},
            {good: spec.service_life_years for good, spec in specs.items()},
            (opening["carriage_feed_good"], specs[opening["carriage_feed_good"]].unit_mass_kg) if opening["carriage_feed_good"] in specs else None),
        carriage_handling={SEA_MODE: sea_freight.PORT_HANDLING_HOURS_PER_TONNE},
        carriage_handling_trade={mode: str(trade) for mode, trade in opening["carriage_handling_trade"].items()},
        held_nodes=tuple(opening["held_nodes"]),
        specs=specs, recipes=recipes, mint_recipe=mint_recipe, basket=basket, trades=trades,
        tax_forms=taxes.forms_from_civ_data(civ.get("state_revenue") or []),
        state_capacity=1.0,   # follows the officials: `run_year` sets it from `Sim.state_reach()` before each year
        hiding=agents_api.evasion.hidden_share,   # the one hiding rule the actor layer uses (Complaint 657)
        working_hours_per_year=float(sim.HOURS_PER_PERSON_YEAR), working_share=float(opening["working_share"]),
        gini=demand.GINI_COEFFICIENT_PREINDUSTRIAL_AGRARIAN, opening_population_by_tile=population_by_tile,
        need_share_by_trade={trade: float(share) for trade, share in (opening.get("need_shares") or {}).items()},
        unskilled_trade=opening["unskilled_trade"], debt_bondage_years=sim.debt_bondage_term_years(), opening_prices=prices, opening_wages=wages, opening_rate=float(opening["rate"]),
        capital_tile=by_people[0], port_tile=(coastal or by_people)[0],
        land_per_run={recipe_id: float(production[recipe_id].get("land_hectare_years") or 0.0)
                      for recipe_id in recipes if production[recipe_id].get("land_hectare_years")},
        yield_factor_by_recipe_tile=cropland_yields(production, recipes, tiles),
        basket_by_tile=baskets_by_tile(basket, need_data, world_map, all_tile_ids), coin_per_unit=unit,
        household_work=households_work.load_household_work(), ready_to_eat=households_work.ready_to_eat_goods(need_data),
        opening_income_per_head=opening.get("opening_income_per_head"),
        recipes_by_country=recipes_by_country(str(civ["id"]), opening["recipes"], partners),
        tile_owners=sim.tile_owner_map(),
        world_map=world_map, improvements=dict(opening["ways"]),
        site_limits=tuple(SiteLimit(*limit) for limit in opening["site_limits"]),
        opening_store_output={good: tuple(tuple(working) for working in entry["workings"])
                              for good, entry in sorted(opening["stores"].items()) if entry["workings"]},
        opening_store_gaps={good: entry["gap"] for good, entry in sorted(opening["stores"].items()) if entry["gap"]})


def tool_wear_recipes(recipes, trades_data, life_years, hours_per_worker_year):
    """The recipes with the tools their hired hours wear out added as inputs: each trade's basket and stock
    (data/world/trades.json) over the goods' service lives, per hour a worker works. The first basket good a
    recipe in the society makes is the tool; the later ones are what a short supply falls back to, and then
    working by hand (each with its hours factor in the data). A tool no recipe makes is left out."""
    wear_per_hour, order, factors = {}, {}, {}
    for trade in sorted(trades_data):
        draw = labour_api.tool_draw(trades_data, trade, 1.0, life_years)
        if draw:
            wear_per_hour[trade] = {good: row["wear_per_year"] / hours_per_worker_year for good, row in draw.items()}
            order[trade] = labour_api.tool_order(trades_data, trade)
            factors[trade] = labour_api.tool_hours_factors(trades_data, trade)
    makeable = {good for recipe in recipes.values() for good in recipe.outputs}
    return {recipe_id: with_tool_wear(recipe, wear_per_hour, makeable, order, factors) for recipe_id, recipe in recipes.items()}


def cropland_yields(production, recipes, tiles):
    """{recipe@tile: yield factor} for the recipes that grow on arable land: the tile's soil, climate and water
    (geography's crop_site) against the reference field. Pasture, forest and mines do not read it."""
    return {recipe_tile_key(recipe_id, tile_id): tile.fertility
            for recipe_id in sorted(recipes) if str(production[recipe_id].get("extracted_from") or "").startswith(ARABLE_SOURCE)
            for tile_id, tile in sorted(tiles.items())}


def recipes_by_country(home_id, home_recipes, partners):
    """Which recipes each country's producers can run; empty when there is only the home country."""
    if not partners:
        return {}
    by_country = {home_id: tuple(sorted(home_recipes))}
    by_country.update({partner: tuple(sorted(opened["recipes"])) for partner, opened in partners.items()})
    return by_country


def _counted_currency(civ, unit):
    """The civilisation's money as the economy counts it: one unit is `unit` coins, so it holds that
    many coins' metal."""
    spec = currency_from_coin_standard(str(civ["id"]), civ["coin_standard"], str(civ.get("currency", "")),
                                       issuer="state:" + str(civ["id"]))
    return dataclasses.replace(spec, backing_per_unit=spec.backing_per_unit * unit)
