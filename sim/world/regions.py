"""Regions as named groups of tiles: a derived view, never a second source.

`data/world/geography.json` keeps for each region only what a tile cannot
say: its name, a label anchor point, route difficulty, the reach figure for
trade, and the shares of metal not yet tied to a deposit. Area, arable land
and fertility are sums over the region's tiles (`land.load_region_lands`);
a region's metal shares add the deposits on its tiles
(`mineral_shares.regional_mineral_shares`). Standalone: data files only.
"""
from typing import Any, Dict

from sim.world import mineral_shares, tile_lookup


region_of_tile = tile_lookup.region_of_tile


def region_records(geography: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """{region_id: label record with `minerals` completed from deposits}."""
    shares = mineral_shares.regional_mineral_shares(geography)
    return {region_id: dict(record, minerals=shares[region_id])
            for region_id, record in geography.get("regions", {}).items()
            if not region_id.startswith("_")}
