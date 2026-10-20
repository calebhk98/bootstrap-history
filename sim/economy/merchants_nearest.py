"""The cheapest carriage from a source area to any other area of a good, kept per carriage table.

`merchants._good_routes` uses it as a lower bound on the carriage of every destination, to stop scanning
destinations that cannot beat the best found. An entry is kept only while the good's area tuple and the source
tile's cost table are the very objects it was computed from, so a changed table or scale is never read stale.
"""
import itertools
import math
import weakref

_entries: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def nearest_carriage(carriage, good, areas, source, costs) -> float:
    """The least cost per tonne from `source` (whose cost table is `costs`) to the anchor of any other area in `areas`."""
    try:
        by_good = _entries.setdefault(carriage, {})
    except TypeError:                                  # a carriage that cannot be weakly held keeps nothing
        by_good = {}
    entry = by_good.get(good)
    if entry is None or entry[0] is not areas:
        entry = by_good[good] = (areas, {}, [area.anchor_tile for area in areas], {area.area_id: i for i, area in enumerate(areas)})
    kept = entry[1].get(source.area_id)
    if kept is not None and kept[0] is costs:
        return kept[1]
    costs_to = list(map(costs.get, entry[2], itertools.repeat(math.inf)))
    costs_to[entry[3][source.area_id]] = math.inf          # the source's own area is not another area
    nearest = min(costs_to, default=math.inf)
    entry[1][source.area_id] = (costs, nearest)
    return nearest
