"""The order a save writes market names in: by (good, area id), which is the name with its separator sorted before every character."""
import numpy

from .market_table_specs import KEY_SEPARATOR

_RANKS = {}       # id of a name list -> (copy of the names, rank of each); a stale entry fails the equality check and is rebuilt
_KEPT = 8


def saved_rank(names) -> numpy.ndarray:
    """rank[row] is the place of the market named `names[row]` in saved order (names are all different)."""
    held = _RANKS.get(id(names))
    if held is not None and held[0] == names:
        return held[1]
    keys = [name.replace(KEY_SEPARATOR, "\x00") for name in names]
    order = sorted(range(len(names)), key=keys.__getitem__)
    rank = numpy.empty(len(names), dtype=numpy.int64)
    rank[order] = numpy.arange(len(names), dtype=numpy.int64)
    if len(_RANKS) >= _KEPT:
        _RANKS.clear()
    _RANKS[id(names)] = (list(names), rank)
    return rank


def in_saved_order(rows: numpy.ndarray, names) -> numpy.ndarray:
    """The rows (of the numbering `names`) sorted by saved order."""
    return rows[numpy.argsort(saved_rank(names)[rows], kind="stable")]
