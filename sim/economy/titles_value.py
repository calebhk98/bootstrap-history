"""What a title is worth.

A title's value is the capitalised rent of the land it covers: the tile's rent per hectare (the one the
land market cleared) times the hectares the share holds, over the interest rate. `title_wealth` is the one
read of a holder's land wealth.
"""
from typing import Mapping

from . import titles
from .types import AgentId, TileId


def capitalising_rate(live_rate: float, opening_rate: float) -> float:
    """The rate rent is capitalised at: the live rate, never under the opening's."""
    return max(live_rate, opening_rate)


def share_value(tile, rent_per_hectare: float, share: float, rate: float) -> float:
    return share * tile.cropland_hectares * rent_per_hectare / rate if rate > 0.0 else 0.0


def title_wealth(tiles: Mapping[TileId, object], record, holder: AgentId, rate: float) -> float:
    """The capitalised rent of every title the holder has."""
    return sum(share_value(tile, record.land_rent.get(tile_id, 0.0), titles.holding(record, tile_id, holder), rate)
               for tile_id, tile in sorted(tiles.items()))
