"""The stretch of country a merchant knows (Complaints/517).

A merchant knows the prices of the areas a year's haul reaches from its home tile and from each tile it has traded at,
and acts on no others. Trading at a tile keeps it in the stretch; a tile unvisited for `memory_years()`
drops out, so a stretch grows by trading outward and shrinks when left alone. A good that crosses more than a year's
haul passes through the stretches of several merchants, each buying at the end of its own and selling to the next.
"""
from typing import Dict, FrozenSet, Iterable, List, Mapping

from sim.world import belief

from . import merchants_search

def memory_years() -> int:
    """Years a merchant keeps a tile it has stopped trading at: the years a firsthand belief about the tile stays reliable
    (`sim.world.belief`)."""
    return belief.years_until_unreliable(belief.TRADE_OBSERVATION_VARIANCE, belief.VARIANCE_GROWTH_PER_YEAR, belief.UNRELIABLE_VARIANCE)


def stretch_of(home_tile: str, traded_tiles: Iterable[str]) -> FrozenSet[str]:
    """The tiles a merchant's knowledge is centred on: its home and every tile it still remembers trading at."""
    return frozenset(traded_tiles) | {home_tile}


def after_year(traded_tiles: Mapping[str, int], traded_now: Iterable[str], memory_years: int) -> Dict[str, int]:
    """The tiles remembered after a year, each with the years since it was traded at: those traded at now are 0, the
    others a year older, and a tile older than `memory_years` is dropped."""
    now = set(traded_now)
    kept = {tile: years + 1 for tile, years in traded_tiles.items() if tile not in now and years + 1 <= memory_years}
    kept.update({tile: 0 for tile in now})
    return kept


def routes_tiles(routes: Mapping) -> List[str]:
    """The tiles a merchant's routes of the year start at or end at: `routes` maps (good, source tile) to legs of
    (destination tile, area, weight)."""
    tiles = set()
    for (_good, source), legs in routes.items():
        tiles.add(source)
        tiles.update(destination for destination, _area, _weight in legs)
    return sorted(tiles)


def known_flags(good, areas, carriage, stretch: Iterable[str]) -> List[bool]:
    """For each area of the good, whether a merchant with this stretch knows its price: a year's haul from some tile of the
    stretch reaches the area's anchor."""
    flags = [False] * len(areas)
    for tile in stretch:
        reached = merchants_search.news_current_flags(good, areas, carriage, tile)
        flags = [known or near for known, near in zip(flags, reached)]
    return flags
