"""The land held livestock and nursery stock stand on, as functions of the holding they are given.

A held lot stands on one tile, the holder's: the held tile nearest the middle of what the holder holds. Pasture
room is that holding's grass beyond the live weight already grazing; nursery room is the place's arable land at
a production entry's output per hectare. The stock's own ledger, its production entry and its labour stay with
the caller (sim/engine/living_stock_growth.py).
"""
import functools

from sim.geography.queries import arable_hectares, endemic_animal_loss, pasture_capacity_kg, tile_facts
from sim.geography.tile_holdings import tiles_held


@functools.lru_cache(maxsize=None)
def _centre_of(tile_ids, world_map):
    """The tile of `tile_ids` nearest their mean position, or None for none."""
    if not tile_ids:
        return None
    facts = [tile_facts(tile_id, world_map) for tile_id in tile_ids]
    mean_lat = sum(fact["lat"] for fact in facts) / len(facts)
    mean_lon = sum(fact["lon"] for fact in facts) / len(facts)
    return min(facts, key=lambda fact: ((fact["lat"] - mean_lat) ** 2 + (fact["lon"] - mean_lon) ** 2,
                                        fact["id"]))["id"]


def stock_place(civ, world_map):
    """The held tile nearest the middle of the holding (the ledger has one holder, so one place); None for a
    holder with no tiles."""
    return _centre_of(tuple(sorted(tiles_held(civ, world_map))), world_map)


def pasture_room_kg(place, grazing_kg, wild_stock, civ, world_map):
    """Live weight more that the held tiles' grass keeps beside the `grazing_kg` already on it; None where the
    stock has no place."""
    if place is None:
        return None
    carried = sum(pasture_capacity_kg(tile, wild_stock, world_map) for tile in tiles_held(civ, world_map))
    return max(0.0, carried - grazing_kg)


def endemic_stock_loss(place, species, world_map):
    """Share of a held lot lost in a year to the endemic disease of its place, 0 for stock with no species or
    no place."""
    if place is None or not species:
        return 0.0
    return endemic_animal_loss(place, species, world_map)


def nursery_room_units(place, output_per_batch, hectare_years_per_batch, world_map):
    """Units the place's arable land can raise in a year at a production entry's output and land use per batch;
    None where nothing limits it (no place, or an entry that works no land)."""
    if place is None or hectare_years_per_batch <= 0.0:
        return None
    return arable_hectares(place, world_map) * output_per_batch / hectare_years_per_batch
