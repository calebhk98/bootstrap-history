"""What a worker asks, and the order-book helpers other markets share.

The labour market itself is the labour core's (`sim.labour.api`; sim/economy/year_labour.py hands it the
year). `clearing_point` and `allocate_in_order` clear the credit market; `sticky_move` is the move of a
remembered price toward its target.
"""
import math
from typing import Dict, List, Optional, Sequence, Tuple

Entry = Tuple[float, str, float]     # (limit price, agent id, quantity)


def clearing_point(floors: Sequence[Tuple[float, float]], caps: Sequence[Tuple[float, float]]) -> Optional[float]:
    """The price where quantity asked at or above a floor meets quantity bid at or below a cap.

    `floors` are (lowest acceptable price, quantity) of the sellers, `caps` (highest acceptable price,
    quantity) of the buyers. With trade, the price is midway across the range no one left out would
    break: at or above the last seller matched and any buyer left out, at or below the last buyer matched
    and any seller left out. So a glut of sellers holds the price at their floor, a queue of buyers at
    their cap. With none, it is midway between the cheapest seller and the keenest buyer, or the one side's
    best limit if the other is absent; None if both are absent.
    """
    live_floors = sorted((price, quantity) for price, quantity in floors if quantity > 0)
    live_caps = sorted(((price, quantity) for price, quantity in caps if quantity > 0), reverse=True)
    if not live_floors and not live_caps:
        return None
    if not live_floors:
        return live_caps[0][0]
    if not live_caps:
        return live_floors[0][0]
    seller, buyer = 0, 0
    seller_left, buyer_left = live_floors[0][1], live_caps[0][1]
    last_floor = last_cap = None
    while seller < len(live_floors) and buyer < len(live_caps):
        if live_floors[seller][0] > live_caps[buyer][0]:
            break
        last_floor, last_cap = live_floors[seller][0], live_caps[buyer][0]
        matched = min(seller_left, buyer_left)
        seller_left -= matched
        buyer_left -= matched
        if seller_left <= 0:
            seller += 1
            seller_left = live_floors[seller][1] if seller < len(live_floors) else 0.0
        if buyer_left <= 0:
            buyer += 1
            buyer_left = live_caps[buyer][1] if buyer < len(live_caps) else 0.0
    if last_floor is None:
        return (live_floors[0][0] + live_caps[0][0]) / 2.0
    # competition among those left out bounds the price: an unmatched seller would undercut above its
    # floor, an unmatched buyer would outbid below its cap
    next_floor = live_floors[seller][0] if seller < len(live_floors) else math.inf
    next_cap = live_caps[buyer][0] if buyer < len(live_caps) else -math.inf
    low, high = max(last_floor, next_cap), min(last_cap, next_floor)
    if low > high:
        return (last_floor + last_cap) / 2.0
    return (low + high) / 2.0


def allocate_in_order(entries: Sequence[Entry], total: float, descending: bool) -> List[float]:
    """Share `total` among entries best limit first, pro rata among equal limits at the margin.

    Returns quantities aligned with `entries`. The shares sum to `total` (or to all the entries' quantity if
    that is less); the answer does not depend on the order entries are given in.
    """
    shares = [0.0] * len(entries)
    groups: Dict[float, List[int]] = {}
    for index, (limit, _agent, _quantity) in enumerate(entries):
        groups.setdefault(limit, []).append(index)
    remaining = total
    for limit in sorted(groups, reverse=descending):
        if remaining <= 0:
            break
        members = sorted(groups[limit], key=lambda index: (entries[index][1], entries[index][2]))
        group_total = sum(entries[index][2] for index in members)
        if group_total <= remaining:
            for index in members:
                shares[index] = entries[index][2]
            remaining -= group_total
            continue
        given = 0.0
        for index in members[:-1]:
            shares[index] = entries[index][2] * remaining / group_total
            given += shares[index]
        shares[members[-1]] = remaining - given
        remaining = 0.0
    return shares


def sticky_move(last_value: Optional[float], target: float, share: float) -> float:
    """Move from the last value toward the target by a share of the gap, never past it."""
    if last_value is None:
        return target
    return last_value + max(0.0, min(1.0, share)) * (target - last_value)
