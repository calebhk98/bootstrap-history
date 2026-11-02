"""Land each cohort may work for itself in a year, from the titles and tenancies on its tile."""
from typing import Dict, Mapping

from . import titles_ground, titles_worked
from .types import AgentId


def allocate_on_tile(asked_by_holder: Mapping[AgentId, float], arable_hectares: float, ceded_hectares: float) -> Dict[AgentId, float]:
    """Hectares each holder may work on one tile: its claim, all cut by one factor if together they exceed the arable land
    less the hectares let to producers that outbid the plots (land_priority.py)."""
    return titles_worked.allocate_hectares(asked_by_holder, arable_hectares - max(0.0, ceded_hectares))


def hectares_held(setup, record) -> Dict[str, float]:
    """Hectares each cohort may work for itself: the land it holds or leases (titles, tenancies), cut to
    the tile's arable land if the claims exceed it, less what producers that outbid the plots were let. Decided before
    any growing."""
    held: Dict[str, float] = {}
    for tile_id in sorted({cohort.tile for cohort in record.cohorts.values()}):
        tile = setup.tiles.get(tile_id)
        arable = titles_ground.arable_hectares(record, tile_id, tile)
        asked = {cohort.agent_id: titles_worked.worked_share(record, tile_id, cohort.agent_id) * arable
                 for cohort in record.cohorts.values() if cohort.tile == tile_id}
        held.update(allocate_on_tile(asked, arable, record.land.land_ceded.get(tile_id, 0.0)))
    return held
