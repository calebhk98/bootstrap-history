"""The sites an ore-extracting firm of the agent economy works: the deposits the seat has found, tile by tile.

Part of the port. For each ore recipe (a production entry whose output is the ore of a resource the
catalogue lists), a tile that holds a deposit of that resource gets a limit: the runs a year the deposits'
room allows (their working rate, less what the seat's own mines name on them), in ore. A tile whose deposits
are worked out keeps a limit of nothing, so the recipe does not fall back to running anywhere. What the firms
raise is read back each year and drawn from the tile's deposits, the same ledger the seat's mines draw on
(`state.holdings.deposit_drawn`, sim/engine/mine_deposits.py).

Recipes that fell standing timber are limited by the tile's stock instead (economy_port_timber.py).

Recipes for resources the catalogue lists no ore for (coal, salt, quarries) declare no limit and keep the
economy's labelled fallback (`UNSITED_EXTRACTION_ANYWHERE`).
"""
from sim.economy import api as economy_api
from sim.economy.api import SiteLimit, recipe_tile_key
from sim.geography.api import ore_goods, ore_tonnes_per_tonne
from sim.unit_conversions import KILOGRAMS_PER_TONNE

from . import economy_port_timber

SITE_YIELD_FACTOR = 1.0   # an ore recipe's output per run is ore, whatever its grade


def _ore_recipes(sim, outputs_by_recipe):
    """{recipe id: (resource id, ore kg a run)} for the recipes whose output is a catalogue resource's ore."""
    ore_of = {ore: resource for resource, by_ore in ore_goods(sim.world_map).items() for ore in by_ore}
    return {recipe_id: (ore_of[recipe_id], outputs[recipe_id]) for recipe_id, outputs in sorted(outputs_by_recipe.items())
            if recipe_id in ore_of and outputs.get(recipe_id, 0.0) > 0.0}


def _worked_by_firms(sim, resource_id, tile_ids):
    """The deposits of a resource the economy's firms work: those the seat has found, and the catalogue's on
    the partner economies' tiles among `tile_ids`."""
    return sim.found_deposits(resource_id) + sim.partner_deposits(resource_id, tile_ids)


def site_limits(sim, outputs_by_recipe, tile_ids=()):
    """[SiteLimit] for the ore recipes among `outputs_by_recipe` ({recipe id: {good: quantity a run}}), from the
    deposits the seat has found and the catalogue's on the partners' tiles among `tile_ids` (the tiles of the
    economy); and for the timber recipes, over `tile_ids`, from each tile's standing wood."""
    limits = list(economy_port_timber.limits(sim, outputs_by_recipe, tile_ids))
    for recipe_id, (resource_id, ore_kg_per_run) in _ore_recipes(sim, outputs_by_recipe).items():
        by_tile = {}
        for row in _worked_by_firms(sim, resource_id, tile_ids):
            ore_kg = row["room_tonnes_per_year"] * ore_tonnes_per_tonne(row) * KILOGRAMS_PER_TONNE
            by_tile[row["tile_id"]] = by_tile.get(row["tile_id"], 0.0) + ore_kg / ore_kg_per_run
        limits.extend(SiteLimit(recipe_id, tile, runs, SITE_YIELD_FACTOR) for tile, runs in sorted(by_tile.items()))
    return limits


def deplete(sim, extraction, outputs_by_recipe):
    """Draw what the firms raised last year ({(recipe id, tile): runs}) from the deposits on those tiles, the
    deposits with most left first."""
    economy_port_timber.fell(sim, extraction, outputs_by_recipe)
    economy_port_timber.regrow(sim)
    recipes = _ore_recipes(sim, outputs_by_recipe)
    worked_tiles = {tile for _recipe_id, tile in extraction}
    for (recipe_id, tile), runs in sorted(extraction.items()):
        if recipe_id not in recipes or runs <= 0.0:
            continue
        resource_id, ore_kg_per_run = recipes[recipe_id]
        ore_tonnes = runs * ore_kg_per_run / KILOGRAMS_PER_TONNE
        for row in sorted((row for row in _worked_by_firms(sim, resource_id, worked_tiles) if row["tile_id"] == tile),
                          key=lambda row: (-row["remaining_tonnes"], row["id"])):
            take = min(ore_tonnes / ore_tonnes_per_tonne(row), row["remaining_tonnes"])
            if take > 0.0:
                sim.draw_deposit(row["id"], take)
                ore_tonnes -= take * ore_tonnes_per_tonne(row)
            if ore_tonnes <= 1e-12:
                break


def crop_yields(economy, weather=1.0):
    """{producer id: yield factor} for the producers whose recipe takes land: the year's weather times the tile's
    soil, climate and water for a recipe that crops (setup.yield_factor_by_recipe_tile), the weather alone for
    pasture and forest."""
    setup = economy.setup
    site_yield = setup.yield_factor_by_recipe_tile
    return {producer_id: weather * site_yield.get(recipe_tile_key(producer.recipe_id, producer.tile), 1.0)
            for producer_id, producer in economy_api.producers_of(economy).items()
            if setup.land_per_run.get(producer.recipe_id, 0.0) > 0.0}


def harmed_yields(yields, harm_by_tile, producers):
    """`yields` with each producer's factor scaled by the harm factor of the tile it stands on (a tile no provider
    names is unharmed); the same mapping when nothing is harmed."""
    if not harm_by_tile:
        return yields
    return {producer_id: factor * harm_by_tile.get(producers[producer_id].tile, 1.0) for producer_id, factor in yields.items()}
