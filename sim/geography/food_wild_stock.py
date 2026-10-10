"""The game's standing stock of each hunted species on each tile, as a share of its carrying capacity.

The stock is plain data the game keeps and saves: {tile id: {species id: share left}}. A missing entry is a
full stock, so an untouched map needs none. Pure helpers only; hunting draws it down (food_wild_harvest.py)
and food potential reads it (food_wild.py).
"""
from typing import Mapping, Optional


def stock_fraction(wild_stock: Optional[Mapping], tile_id: str, species_id: str) -> float:
    """Share of the carrying capacity left, 1 when nothing has been taken."""
    if not wild_stock:
        return 1.0
    return float(wild_stock.get(tile_id, {}).get(species_id, 1.0))


def regrown_fraction(fraction: float, growth_rate: float, recolonisation_floor: float) -> float:
    """One year of logistic regrowth at the species' maximum rate. A stock below the floor is topped up to it
    first, from game wandering in from neighbouring land, so a hunted-out stock can recover."""
    start = min(1.0, max(fraction, recolonisation_floor))
    return min(1.0, start + growth_rate * start * (1.0 - start))
