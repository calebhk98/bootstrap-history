"""Cleared ground (Complaint 538): hectares a clearer made are new arable land on the tile, not a transfer.

A tile's arable land is its cropland plus what has been cleared and taken up (`record.cleared_hectares`). Ground
in a clearer's stock is not arable until an actor takes it up as its own title: `add_ground` grows the tile's
arable land by those hectares and gives them to that actor. Titles are shares of the arable land, so every other
holder's share, every tenancy's share and every pledge on the tile shrinks by the same factor and keeps its
hectares.
"""
from . import titles
from .types import AgentId, TileId


def arable_hectares(record, tile_id: TileId, tile) -> float:
    """The tile's cropland and the ground cleared on it. 0 for a tile the economy does not know."""
    if tile is None:
        return 0.0
    return tile.cropland_hectares + getattr(record, "cleared_hectares", {}).get(tile_id, 0.0)


def add_ground(record, tile_id: TileId, receiver: AgentId, hectares: float, arable_before: float) -> float:
    """`hectares` of newly cleared ground join the tile's arable land and become the receiver's title. Returns the
    hectares added (none for no hectares or a tile with no arable land)."""
    if hectares <= 0.0 or arable_before <= 0.0:
        return 0.0
    keep = arable_before / (arable_before + hectares)
    held = titles._held(record, tile_id)
    for holder in list(held):
        held[holder] *= keep
    held[receiver] = held.get(receiver, 0.0) + hectares / (arable_before + hectares)
    for row in getattr(record, "tenancies", {}).get(tile_id, ()):
        row["share"] *= keep
    for loan in record.loans:
        if loan.collateral_tile == tile_id:
            loan.collateral_share *= keep
    record.cleared_hectares[tile_id] = record.cleared_hectares.get(tile_id, 0.0) + hectares
    return hectares
