"""The mechanisms a content row of the `resources` catalogue may name, and which model reads each.

Mechanisms are code, so their names live here; content (gold, goats, unobtainium) is data that
picks one. A row naming a mechanism not listed is an error, whichever model meets it first.
"""
from typing import Any, Dict, List

from sim.geography.map_source import MapDataError, WorldMap

OWNER_OF_MECHANISM = {
    "mineral_deposit": "resources", "point_occurrence": "resources", "surface_stock": "resources",
    "biotic_stand": "resources",
    "wild_population": "food", "herd_animal": "food", "forage_plant": "food", "fishery": "food",
}


def owner(mechanism: str, row_id: str = "?") -> str:
    """The model that reads this mechanism; an unknown one is an error naming the row."""
    if mechanism not in OWNER_OF_MECHANISM:
        raise MapDataError("resource %r (data/world/geography/resources/): unknown mechanism %r; known: %s"
                           % (row_id, mechanism, ", ".join(sorted(OWNER_OF_MECHANISM))))
    return OWNER_OF_MECHANISM[mechanism]


def unknown_rows(world_map: WorldMap) -> List[str]:
    """Ids of resource rows whose mechanism no model reads."""
    return [row_id for row_id, row in sorted(world_map.catalogue("resources").items())
            if row.get("mechanism") not in OWNER_OF_MECHANISM]


def rows_owned_by(world_map: WorldMap, model: str) -> Dict[str, Dict[str, Any]]:
    """{row_id: row} of the resource rows a model reads, checking every row's mechanism."""
    return {row_id: row for row_id, row in sorted(world_map.catalogue("resources").items())
            if owner(row.get("mechanism"), row_id) == model}
