"""Everything the endowment model says a tile holds, resource by resource."""
from typing import Any, Dict

from sim.geography.map_source import WorldMap
from sim.geography.resources_catalogue import resource_definitions
from sim.geography.resources_endowment import endowment


def resources_at(world_map: WorldMap, tile_id: str) -> Dict[str, Dict[str, Any]]:
    """{resource_id: endowment or stand dict} for each resource the tile has any of."""
    summary = {}
    for resource_id in resource_definitions(world_map):
        found = endowment(world_map, tile_id, resource_id)
        if found.get("total", found.get("standing_stock", 0.0)) > 0.0:
            summary[resource_id] = found
    return summary
