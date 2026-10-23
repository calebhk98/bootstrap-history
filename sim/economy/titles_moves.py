"""Land titles moved by a state's decree (confiscation, land reform): the economy applies the moves the state planned.

A move is (tile, giver, receiver, share of the tile). `titles.pass_title` is the one rule that moves a title, so a giver
parts with no more than he holds and a tenant who receives his lessor's land holds it outright.
"""
from typing import Dict, Iterable, Tuple

from . import titles
from .types import AgentId, TileId

Move = Tuple[TileId, AgentId, AgentId, float]


def holdings(record, tiles: Iterable[TileId]) -> Tuple[Dict[TileId, Dict[AgentId, float]], Dict[TileId, list]]:
    """(holder -> share, tenancy rows) of each of the tiles, for the state to plan its moves from."""
    held = {tile: titles.shares(record, tile) for tile in sorted(set(tiles))}
    tenancies = {tile: [dict(row) for row in getattr(record, "tenancies", {}).get(tile, ())] for tile in held}
    return held, tenancies


def apply(record, moves: Iterable[Move]) -> Dict[TileId, float]:
    """Pass each title; the share of each tile actually moved."""
    moved: Dict[TileId, float] = {}
    for tile, giver, receiver, share in moves:
        done = titles.pass_title(record, tile, giver, receiver, share)
        if done > 0.0:
            moved[tile] = moved.get(tile, 0.0) + done
    return moved
