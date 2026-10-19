"""Who a route's dues are owed to: each due is levied at the tile where the haul changes to a mode, and belongs to
whoever holds that tile now. The route search prices the dues per tonne in each mode's handling; this reads the
found route's legs against the owner map, so a change of holder moves the revenue with no new search.
"""
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional


def route_dues_levied(legs: Iterable[Mapping[str, Any]], dues_per_tonne: Mapping[str, float],
                      owner_of: Callable[[str], Optional[str]]) -> List[Dict[str, Any]]:
    """[{tile, holder, mode, per_tonne}] for each leg whose mode carries dues and whose starting tile is held;
    `legs` carry `from` (tile) and `mode`, `dues_per_tonne` is money per tonne by mode."""
    levied = []
    for leg in legs:
        per_tonne = float(dues_per_tonne.get(leg["mode"], 0.0))
        holder = owner_of(leg["from"]) if per_tonne > 0.0 else None
        if holder is not None:
            levied.append({"tile": leg["from"], "holder": holder, "mode": leg["mode"], "per_tonne": per_tonne})
    return levied


def route_dues_by_holder(legs: Iterable[Mapping[str, Any]], dues_per_tonne: Mapping[str, float],
                         owner_of: Callable[[str], Optional[str]], tonnes: float = 1.0) -> Dict[str, float]:
    """{holder: money owed} for `tonnes` carried over the legs."""
    owed: Dict[str, float] = {}
    for due in route_dues_levied(legs, dues_per_tonne, owner_of):
        owed[due["holder"]] = owed.get(due["holder"], 0.0) + due["per_tonne"] * tonnes
    return owed
