"""Posted land rent: what a tile's tenants are charged, which follows what its land clears at only slowly.

Land clears at a step function of demand (the rent jumps when use first spills into a worse band), and
producers plan with last year's rent, so a rent that followed the clearing exactly would make demand
and rent chase each other from year to year.
"""
from typing import Dict, Mapping

from sim.constants import declare
from .types import TileId

LAND_RENT_ADJUSTMENT_SHARE = declare(
    "LAND_RENT_ADJUSTMENT_SHARE", 0.3, kind="temporary_heuristic",
    unit="share of the gap between posted rent and what the land clears at closed each year",
    source=None, confidence="D",
    why="Tenancies run several years and are renegotiated a part at a time, so posted rent follows the "
        "market's clearing rent with a lag. The length of leases and how rent is renegotiated are not "
        "modelled; a lease book (term and renewal per tenancy) would replace the share.")


def posted_rents(previous: Mapping[TileId, float], cleared: Mapping[TileId, float],
                 share: float = LAND_RENT_ADJUSTMENT_SHARE) -> Dict[TileId, float]:
    """Next posted rent per hectare by tile: a tile with no rent posted yet takes what it clears at;
    otherwise the posted rent closes `share` of the gap to the clearing rent (a tile nobody asked for
    land on clears at zero)."""
    posted: Dict[TileId, float] = {}
    for tile in set(previous) | set(cleared):
        target = max(0.0, cleared.get(tile, 0.0))
        posted[tile] = target if tile not in previous else previous[tile] + share * (target - previous[tile])
    return posted
