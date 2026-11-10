"""`country_figures._traded_volumes` as it was before the area test used `isdisjoint`: a set intersection per market."""
from sim.economy.country_figures import _area_tiles, country_tiles

KEY_SEPARATOR = "|"


def traded_volumes_by_intersection(economy, country):
    tiles = country_tiles(economy, country)
    totals = {}
    areas_of = {}
    for key, volume in sorted(economy.record.goods.volumes.items()):
        good, area = key.split(KEY_SEPARATOR, 1)
        if country is not None:
            by_area = areas_of.get(good)
            if by_area is None:
                by_area = areas_of[good] = _area_tiles(economy, good)
            if area in by_area and not (by_area[area] & tiles):
                continue
        totals[good] = totals.get(good, 0.0) + volume
    return totals
