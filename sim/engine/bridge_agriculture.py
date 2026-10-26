"""Bridge entries the agriculture module uses until the modules that own these facts move.

Each view answers through `Sim` as the old mixin methods did; when its owner moves it publishes the same name and the entry
is deleted. The geography ones hand the module the per-tile sums over the held land. `legacy_dice` is the game's random
source, used in place."""
from sim.assembly.api import QUOTE

from . import externalities
from .bridge import bridge_view
from .data import load_geography
from sim.geography.api import tiles_held


# ---- land ----

@bridge_view("held_tile_geometry")
def held_tile_geometry(sim):
    """[(tile id, lat, lon, land area km2, arable fraction)] for each held tile the land map describes, in held order."""
    tiles_by_id = (load_geography(sim.world_map).get("land_tiles") or {}).get("tiles") or {}
    rows = []
    for tile_id in tiles_held(sim.civ, sim.world_map):
        tile = tiles_by_id.get(tile_id)
        if not tile:
            continue
        rows.append((tile_id, tile["lat"], tile["lon"], tile.get("land_area_km2", 0.0), tile.get("arable_fraction", 0.0)))
    return rows


@bridge_view("crop_sites", kind=QUOTE)
def crop_sites(sim, cropped_share, nutrient_factors, tillage_capacity):
    """{tile: crop site} over the held tiles under a rotation that crops `cropped_share`."""
    return sim.geography.crop_sites(cropped_share, nutrient_factors, tillage_capacity)


@bridge_view("food_kcal_by_source", kind=QUOTE)
def food_kcal_by_source(sim, wild_stock, crop_technique, nutrient_factors):
    return sim.geography.food_kcal_by_source(wild_stock, crop_technique, nutrient_factors)


@bridge_view("game_food_sources")
def game_food_sources(sim):
    return sim.geography.game_food_sources()


@bridge_view("huntable_kcal", kind=QUOTE)
def huntable_kcal(sim, wild_stock):
    return sim.geography.huntable_kcal(wild_stock)


@bridge_view("take_hunt", kind=QUOTE)
def take_hunt(sim, wild_stock, available, share):
    return sim.geography.take_hunt(wild_stock, available, share)


@bridge_view("regrow_wild_stock", kind=QUOTE)
def regrow_wild_stock(sim, wild_stock):
    return sim.geography.regrow_wild_stock(wild_stock)


@bridge_view("tile_soil_nitrogen_factors", kind=QUOTE)
def tile_soil_nitrogen_factors(sim, stock, cropped_share, reference_cropped_share, manure_kg):
    return sim.geography.soil_nitrogen_factors(stock, cropped_share, reference_cropped_share, manure_kg)


@bridge_view("soil_nitrogen_after_year", kind=QUOTE)
def soil_nitrogen_after_year(sim, stock, cropped_share, reference_cropped_share, kg_per_cropped_hectare, legume_share, manure_kg):
    """The soil nitrogen stock a year of cropping, legumes and manure on the held tiles leaves; `stock` is not changed."""
    after = dict(stock)
    sim.geography.step_soil_nitrogen(after, cropped_share, reference_cropped_share, kg_per_cropped_hectare, legume_share,
                                     manure_kg)
    return after


# ---- labour, prices, hazards and the game's own state ----

@bridge_view("externality_yield_factors", kind=QUOTE)
def externality_yield_factors(sim, year):
    """{tile: factor} the mods' externalities agree on for the year's harvest, each clamped to 0..1."""
    return externalities.yield_factors(sim, year)


@bridge_view("legacy_dice")
def legacy_dice(sim):
    """The game's random source; the weather salt is drawn from it once."""
    return sim.rng
