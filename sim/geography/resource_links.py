"""What the resource catalogue says about mining a resource: the ore goods it yields and whether its
workings are priced from the deposits' own physical works. Content lives in data/world/geography/resources/,
so a mod adds a mineral by adding a row there.
"""
from typing import Dict, Tuple

from sim.geography.map_source import WorldMap


def ore_goods(world_map: WorldMap) -> Dict[str, Dict[str, Tuple[str, ...]]]:
    """{resource id: {ore good: smelting recipe ids in order of preference}} for resources that yield ore goods,
    in the catalogue's order."""
    return {resource_id: {good: tuple(recipes) for good, recipes in row["ore_goods"].items()}
            for resource_id, row in world_map.catalogue("resources").items() if row.get("ore_goods")}


def works_priced_from_deposits(world_map: WorldMap) -> Tuple[str, ...]:
    """Resource ids whose mine running cost comes from the deposits' physical works, with no book price needed."""
    return tuple(resource_id for resource_id, row in world_map.catalogue("resources").items()
                 if row.get("works_priced_from_deposits"))
