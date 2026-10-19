"""Remembers one good's candidate routes so merchants that see the same prices share the search.

A good's routes depend on the carriage table, the good's areas and spec, the price in each area and the
interest rate, and on nothing else. Merchants holding the same expectations, and the lending and ordering
passes at an unchanged rate, therefore ask the same question. The memo lives beside the carriage table
(dropped with it) and never reaches a saved record. A hit needs every input equal, so it returns exactly
what the search would.
"""
import weakref
from typing import Callable, Dict, List

SLOTS_PER_GOOD = 4        # a few recent questions per good; older ones are forgotten

_memos: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def routes_for_good(carriage, good, areas, spec, prices: tuple, interest_rate: float,
                    search: Callable[[], List]) -> List:
    """The rows `search()` returns, reused when the same question was asked of this carriage table before.
    The rows are shared between callers, who must not change them."""
    try:
        memo: Dict[str, list] = _memos.setdefault(carriage, {})
    except TypeError:                                  # a carriage that cannot be weakly held is not memoised
        return search()
    slots = memo.setdefault(good, [])
    for slot_areas, slot_spec, slot_prices, slot_rate, slot_scale, rows in slots:
        if slot_areas is areas and slot_spec == spec and slot_rate == interest_rate and slot_prices == prices \
                and slot_scale == getattr(carriage, "scale", 1.0):
            return rows
    rows = search()
    slots.append((areas, spec, prices, interest_rate, getattr(carriage, "scale", 1.0), rows))
    del slots[:-SLOTS_PER_GOOD]
    return rows


_sorted_memos: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def sorted_rows(carriage, parts: List[List], order: Callable[[List], List]) -> List:
    """`order(all the rows of parts)`, reused when the last question for this carriage table was made of the very
    same per-good row lists (as merchants with the same expectations ask). The result is shared between callers,
    who must not change it."""
    try:
        last = _sorted_memos.get(carriage)
    except TypeError:
        last = None
    if last is not None and len(last[0]) == len(parts) and all(old is new for old, new in zip(last[0], parts)):
        return last[1]
    rows = order([row for part in parts for row in part])
    try:
        _sorted_memos[carriage] = (parts, rows)
    except TypeError:
        pass
    return rows
