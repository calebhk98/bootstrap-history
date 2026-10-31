"""Land each cohort may work for itself in a year, from the titles and tenancies on its tile."""
from typing import Dict

from . import titles_ground, titles_worked


def hectares_held(setup, record) -> Dict[str, float]:
    """Hectares each cohort may work for itself: the land it holds or leases (titles, tenancies), cut to
    the tile's arable land if the claims exceed it. Decided before any growing."""
    held: Dict[str, float] = {}
    for tile_id in sorted({cohort.tile for cohort in record.cohorts.values()}):
        tile = setup.tiles.get(tile_id)
        arable = titles_ground.arable_hectares(record, tile_id, tile)
        asked = {cohort.agent_id: titles_worked.worked_share(record, tile_id, cohort.agent_id) * arable
                 for cohort in record.cohorts.values() if cohort.tile == tile_id}
        held.update(titles_worked.allocate_hectares(asked, arable))
    return held
