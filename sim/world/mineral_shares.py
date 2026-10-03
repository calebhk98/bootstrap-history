"""Each region's share of a metal's output, from the tiles its deposits sit on.

A named deposit carries its own share and a position, which resolves to the
land tile that holds it (data/world/deposits.json). geography.json's region records keep only the
shares not tied to a deposit. A region's total is its own table plus the
deposits whose tile belongs to it, so a share is stored once, at one place.
Standalone: reads data files only, never the engine.
"""
from typing import Any, Dict, Optional

from sim.world import deposits
from sim.geography.api import tile_lookup


def regional_mineral_shares(
        geography: Dict[str, Any],
        deposits_data: Optional[Dict[str, Any]] = None) -> Dict[str, Dict[str, float]]:
    """{region_id: {metal: share}} for every region record. Only metals the
    region table itself lists (iron, coal, copper, ...) are completed from
    deposits; a metal the table never lists (gold, mercury) stays out of the
    regional view, as before."""
    deposits_data = (deposits_data if deposits_data is not None
                     else deposits._load_json(deposits.DEPOSITS_FILE))
    regions = {region_id: record for region_id, record in geography["regions"].items()
               if not region_id.startswith("_")}
    shares = {region_id: dict(record.get("minerals") or {})
              for region_id, record in regions.items()}
    listed_metals = {metal for table in shares.values() for metal in table}
    region_of_tile = tile_lookup.region_of_tile(geography)
    tiles = geography.get("land_tiles", {}).get("tiles", {})
    for metal, entries in deposits_data["deposits"].items():
        if metal.startswith("_") or metal not in listed_metals:
            continue
        for entry in entries:
            region_id = region_of_tile.get(tile_lookup.nearest_tile_id(tiles, entry["lat"], entry["lon"]))
            if region_id in shares:
                shares[region_id][metal] = (
                    shares[region_id].get(metal, 0.0) + entry["share_of_empire_output"])
    return shares
