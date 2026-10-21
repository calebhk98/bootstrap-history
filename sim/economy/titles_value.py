"""What a title is worth.

A title's value is the capitalised rent of the land it covers: the tile's rent per hectare (the one the
land market cleared) times the hectares the share holds, over the interest rate. `title_wealth` is the one
read of a holder's land wealth.
"""
from typing import Mapping

from . import titles, titles_ground
from .types import AgentId, TileId


def capitalising_rate(live_rate: float, opening_rate: float) -> float:
    """The rate rent is capitalised at: the live rate, never under the opening's."""
    return max(live_rate, opening_rate)


def hectare_value(rent_per_hectare: float, rate: float) -> float:
    """What one hectare is worth to its holder: its rent capitalised at the rate."""
    return rent_per_hectare / rate if rate > 0.0 else 0.0


def share_value(arable_hectares: float, rent_per_hectare: float, share: float, rate: float) -> float:
    return share * arable_hectares * rent_per_hectare / rate if rate > 0.0 else 0.0


def title_wealth(tiles: Mapping[TileId, object], record, holder: AgentId, rate: float) -> float:
    """The capitalised rent of every title the holder has."""
    return sum(share_value(titles_ground.arable_hectares(record, tile_id, tile), record.land_rent.get(tile_id, 0.0), titles.holding(record, tile_id, holder), rate)
               for tile_id, tile in sorted(tiles.items()))
