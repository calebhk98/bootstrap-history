"""An urban marker (Complaint 645): a tile is urban when most of its people are on no plot of their own. Urban households have
no hearth or plot, so they buy cooked food and service. Plain functions of the tile's (people, share of land worked) rows."""
from typing import Dict, List, Sequence, Tuple

from sim.constants import declare

from . import titles_worked
from .types import TileId

URBAN_LANDLESS_SHARE = declare(
    "URBAN_LANDLESS_SHARE", 0.5, kind="temporary_heuristic",
    unit="share of a tile's people on no plot of their own at which the tile is urban",
    source=None, confidence="D", retire="Complaints/645-household-work-is-not-a-need-so-there-are-no-servants-cooks-or-taverns.md",
    why="Sources define a town by size (Roman towns of roughly 5,000 or more, data/world/urban_share_bands.json) or by the "
        "share out of agriculture, not by plots; a majority off the land stands in until settlement density is a tile figure.")

PLOT_EPSILON = 1e-9


def is_urban(people_and_worked: Sequence[Tuple[float, float]], landless_share: float = URBAN_LANDLESS_SHARE) -> bool:
    """Whether a tile is urban: the people in (people, share of the tile's land worked) rows who work none are at least
    `landless_share` of all its people. A tile with no people is not urban."""
    total = sum(max(0.0, people) for people, _worked in people_and_worked)
    if total <= 0.0:
        return False
    landless = sum(max(0.0, people) for people, worked in people_and_worked if worked <= PLOT_EPSILON)
    return landless >= landless_share * total


def tile_rows(record, tile: TileId) -> List[Tuple[float, float]]:
    """(people, share of the tile's land worked) of each cohort on `tile`."""
    cohorts = [cohort for _agent_id, cohort in sorted(record.cohorts.items()) if cohort.tile == tile]
    worked = titles_worked.worked_shares(record, [tile] * len(cohorts), [cohort.agent_id for cohort in cohorts])
    return [(cohort.people, share) for cohort, share in zip(cohorts, worked)]


def urban_tiles(record, tiles: Sequence[TileId]) -> Dict[TileId, bool]:
    """`is_urban` of each distinct tile of `tiles`."""
    return {tile: is_urban(tile_rows(record, tile)) for tile in dict.fromkeys(tiles)}
