"""Each region's share of a metal's output, from the tiles its deposits sit on.

A named deposit carries its own share and a position, which resolves to the
land tile that holds it (the geography deposit catalogue). the geography data's region records keep only the
shares not tied to a deposit. A region's total is its own table plus the
deposits whose tile belongs to it, so a share is stored once, at one place.
What a holder can draw on (`held_share`) counts the deposits on its tiles exactly and the table
remainder by the fraction of each region's tiles held.
Standalone: reads data files only, never the engine.
"""
from typing import Any, Dict, Iterable, Optional

from sim.world import deposits
from sim.geography.api import tile_lookup


def _tables(geography: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """{region_id: the region record's own table of shares not tied to a deposit}."""
    return {region_id: dict(record.get("minerals") or {})
            for region_id, record in geography["regions"].items() if not region_id.startswith("_")}


def deposit_shares_by_tile(
        geography: Dict[str, Any],
        deposits_data: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, float]]:
    """{metal: {tile_id: share of output}} for the deposits, each on the tile that holds it."""
    deposits_data = (deposits_data if deposits_data is not None
                     else deposits.load_deposit_data())
    tiles = geography.get("land_tiles", {}).get("tiles", {})
    by_metal: Dict[str, Dict[str, float]] = {}
    for metal, entries in deposits_data["deposits"].items():
        if metal.startswith("_"):
            continue
        for entry in entries:
            tile_id = tile_lookup.nearest_tile_id(tiles, entry["lat"], entry["lon"])
            on_tile = by_metal.setdefault(metal, {})
            on_tile[tile_id] = on_tile.get(tile_id, 0.0) + entry["share_of_empire_output"]
    return by_metal


def regional_mineral_shares(
        geography: Dict[str, Any],
        deposits_data: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, float]]:
    """{region_id: {metal: share}} for every region record. Only metals the
    region table itself lists (iron, coal, copper, ...) are completed from
    deposits; a metal the table never lists (gold, mercury) stays out of the
    regional view, as before."""
    shares = _tables(geography)
    listed_metals = {metal for table in shares.values() for metal in table}
    region_of_tile = tile_lookup.region_of_tile(geography)
    for metal, on_tile in deposit_shares_by_tile(geography, deposits_data).items():
        if metal not in listed_metals:
            continue
        for tile_id, share in on_tile.items():
            region_id = region_of_tile.get(tile_id)
            if region_id in shares:
                shares[region_id][metal] = shares[region_id].get(metal, 0.0) + share
    return shares


def held_share(
        held_tiles: Iterable[str], metal: str, geography: Dict[str, Any],
        deposits_data: Optional[Dict[str, Any]] = None) -> float:
    """Share of a metal's output on the tiles held: the deposits sitting on them, plus each region's
    table remainder (shares with no deposit behind them) by the fraction of that region's tiles held.
    A metal no region table lists is untracked and gives zero."""
    tables = _tables(geography)
    if not any(metal in table for table in tables.values()):
        return 0.0
    held = set(held_tiles)
    on_tile = deposit_shares_by_tile(geography, deposits_data).get(metal, {})
    total = sum(share for tile_id, share in on_tile.items() if tile_id in held)
    for region_id, region_tiles in geography.get("land_tiles", {}).get("region_to_tiles", {}).items():
        remainder = tables.get(region_id, {}).get(metal, 0.0)
        if remainder and region_tiles:
            total += remainder * len(held.intersection(region_tiles)) / len(region_tiles)
    return total
