"""The sites a wood-felling firm works: the standing timber of each tile.

Part of the port. A production entry that names `extracted_from: "standing timber"` is limited, tile by tile,
to the runs the tile's standing wood allows; a tile with no forest has no limit, so the recipe does not run
there. As the felled area spreads out from the settlement the haul to the nearest standing wood lengthens,
which lowers the wood a run delivers (the yield factor) and so raises its cost. What the firms fell is read
back each year and drawn from the tile's stock (the resources module's `timber_felled`); the stock then regrows.
"""
from sim.economy.api import SiteLimit
from sim.geography.api import modes_carrying, carriage_rates, standing_timber_tonnes, timber_haul_km
from sim.resources.api import FellTimber, RegrowTimber
from sim.unit_conversions import KILOGRAMS_PER_TONNE
from sim.world import demand

TIMBER_SOURCE = "standing timber"


def timber_recipes(outputs_by_recipe):
    """{recipe id: (kg felled a run, labour hours a run)} for the recipes that fell standing timber."""
    production = demand.production_data()
    found = {}
    for recipe_id, outputs in sorted(outputs_by_recipe.items()):
        entry = production.get(recipe_id) or {}
        if entry.get("extracted_from") == TIMBER_SOURCE and outputs.get(recipe_id, 0.0) > 0.0:
            found[recipe_id] = (outputs[recipe_id], sum((entry.get("labour_hours") or {}).values()))
    return found


def haul_hours_per_tonne_km(world_map):
    """Crew hours to carry a tonne a kilometre over level ground, by the cheapest land mode that carries goods."""
    rates = carriage_rates(sorted(modes_carrying("goods", world_map)), world_map)
    land = [rate["crew_hours_per_tonne_km"] for rate in rates.values()
            if "land" in rate["edge_classes"] and not rate.get("needs_improvement")]
    return min(land) if land else 0.0


def limits(sim, outputs_by_recipe, tile_ids):
    """[SiteLimit] for the timber recipes over `tile_ids`: runs the standing wood allows, yield cut by the haul."""
    recipes = timber_recipes(outputs_by_recipe)
    if not recipes:
        return []
    world_map = sim.world_map
    felled = sim.view("timber_felled")()
    hours_per_tonne_km = haul_hours_per_tonne_km(world_map)
    found = []
    for tile in sorted(tile_ids):
        standing_kg = standing_timber_tonnes(felled, tile, world_map) * KILOGRAMS_PER_TONNE
        if standing_kg <= 0.0:
            continue
        haul_km = timber_haul_km(felled, tile, world_map)
        for recipe_id, (kg_per_run, hours_per_run) in recipes.items():
            extra_hours = haul_km * hours_per_tonne_km * kg_per_run / KILOGRAMS_PER_TONNE
            factor = hours_per_run / (hours_per_run + extra_hours) if hours_per_run > 0.0 else 1.0
            found.append(SiteLimit(recipe_id, tile, standing_kg / kg_per_run, factor))
    return found


def fell(sim, extraction, outputs_by_recipe):
    """Take what the firms felled last year ({(recipe id, tile): runs}) from the tiles' stock."""
    recipes = timber_recipes(outputs_by_recipe)
    if not recipes:
        return
    cuts = tuple((tile, runs * recipes[recipe_id][0] / KILOGRAMS_PER_TONNE)
                 for (recipe_id, tile), runs in sorted(extraction.items()) if recipe_id in recipes and runs > 0.0)
    sim.send(FellTimber(cuts))


def regrow(sim):
    """The stock a year on."""
    sim.send(RegrowTimber())
