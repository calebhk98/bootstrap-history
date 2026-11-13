"""Order-book helpers the credit market shares: where a queue of sellers meets a queue of buyers, how a total is shared among
them, and the move of a remembered price toward its target. Plain functions over the figures handed in."""
from typing import Dict, List, Optional, Sequence, Tuple

Entry = Tuple[float, str, float]     # (limit price, agent id, quantity)


def cumulative_curve(entries: Sequence[Tuple[float, float]], reverse: bool) -> Tuple[List[float], List[float]]:
    """Distinct limit prices, ascending, and at each the quantity of entries whose limit is at most that price (or, when
    `reverse`, at least that price)."""
    live = sorted(((price, quantity) for price, quantity in entries if quantity > 0), reverse=reverse)
    prices: List[float] = []
    totals: List[float] = []
    running = 0.0
    for price, quantity in live:
        running += quantity
        if prices and prices[-1] == price:
            totals[-1] = running
        else:
            prices.append(price)
            totals.append(running)
    if reverse:
        prices.reverse()
        totals.reverse()
    return prices, totals


def interpolated(prices: Sequence[float], totals: Sequence[float], price: float) -> float:
    """The curve through (price, total) points at `price`: straight between points, flat beyond the ends."""
    if price <= prices[0]:
        return totals[0]
    for index in range(len(prices) - 1):
        if price < prices[index + 1]:
            return totals[index] + (totals[index + 1] - totals[index]) * (price - prices[index]) / (prices[index + 1] - prices[index])
    return totals[-1]


def supply_demand_crossing(floors: Sequence[Tuple[float, float]], caps: Sequence[Tuple[float, float]]) -> Optional[float]:
    """The price where the quantity offered meets the quantity requested, each a curve through its cumulative points.

    `floors` are (lowest acceptable price, quantity) of the sellers, `caps` (highest acceptable price, quantity) of the
    buyers. The supply curve is the quantity of sellers whose floor is at most the price, the demand curve the quantity of
    buyers whose cap is at least it, each drawn straight between its points, so the crossing moves smoothly as an entry
    changes. Where supply already meets demand at the lowest floor, that floor is the price. With no buyers it is the lowest
    floor, with no sellers the highest cap; None if both are absent. Sellers set the price: it never passes the dearest floor,
    so buyers still unserved there are rationed by quantity, not by a bid that a few units of supply would move.
    """
    supply_prices, supply_totals = cumulative_curve(floors, False)
    demand_prices, demand_totals = cumulative_curve(caps, True)
    if not supply_prices and not demand_prices:
        return None
    if not supply_prices:
        return demand_prices[-1]
    if not demand_prices:
        return supply_prices[0]
    points = sorted({price for price in supply_prices + demand_prices if supply_prices[0] <= price <= supply_prices[-1]})
    previous_price, previous_gap = points[0], 0.0
    for index, price in enumerate(points):
        gap = interpolated(supply_prices, supply_totals, price) - interpolated(demand_prices, demand_totals, price)
        if gap >= 0.0:
            if index == 0:
                return price
            return previous_price + (price - previous_price) * (0.0 - previous_gap) / (gap - previous_gap)
        previous_price, previous_gap = price, gap
    return points[-1]


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
