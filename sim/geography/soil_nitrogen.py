"""The held cropland's soil nitrogen between years (Complaint 543), as functions of the stock they are given.

The stock is {tile: share of the native pool left}; a tile with no entry is native. The society's rotation, its crop
and its draught herd come in as arguments, so this module reads nothing from the simulation. The pool arithmetic is
sim/world/soil_nutrients.py.
"""
from typing import Dict, Iterable, Optional

from sim.geography.queries import crop_site
from sim.geography.tile_holdings import tiles_held
from sim.world import soil_nutrients


def unworn_sites(civ, world_map, cropped_share: float):
    """{tile: crop site} over the held tiles, with no soil nitrogen penalty, under a rotation that crops `cropped_share`."""
    return {tile_id: crop_site(tile_id, cropped_share, world_map) for tile_id in tiles_held(civ, world_map)}


def manure_nitrogen_per_hectare(herd_kg: float, sites) -> float:
    """Transitional: nitrogen of the draught herd's collected dung over the cropped hectares of `sites`, kg per hectare of holding."""
    hectares = sum(site.cropped_hectares for site in sites.values())
    return 0.0 if hectares <= 0.0 else soil_nutrients.herd_manure_nitrogen_kg(herd_kg) / hectares


def yield_factors(stock: Dict[str, float], held_tiles: Iterable[str], cropped_share: float,
                  reference_cropped_share: float, manure_per_hectare: float) -> Dict[str, float]:
    """{tile: yield factor of its soil nitrogen stock} for the held tiles that have a stock entry."""
    return {tile_id: soil_nutrients.yield_response(stock[tile_id], cropped_share, reference_cropped_share, manure_per_hectare)
            for tile_id in held_tiles if tile_id in stock}


def step_year(stock: Dict[str, float], sites, kg_per_cropped_hectare: float, legume_share: float,
              reference_cropped_share: float, manure_per_hectare: float) -> None:
    """One year of cropping, legumes and manure on every site with cropland; writes the new shares into `stock`."""
    for tile_id, site in sites.items():
        if site.arable_hectares <= 0.0 or site.cropped_hectares <= 0.0:
            continue
        cropped_share = min(1.0, site.cropped_hectares / site.arable_hectares)
        stock[tile_id] = soil_nutrients.next_share(
            stock.get(tile_id, 1.0), cropped_share, kg_per_cropped_hectare * site.yield_factor,
            legume_share, manure_per_hectare, reference_cropped_share)
