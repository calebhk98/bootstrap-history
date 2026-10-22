"""What a bonded person is worth, and where a bonded people are bought (Complaints 644 and 648). Plain functions.

An owner will not sell a person for less than the present value of the person's hours over a working life, at the
wage those hours fetch where the owner is; a buyer will not pay more than the same value at the wage where the buyer
is. A trained person's hours fetch the trade's wage; an untrained person's the area's wage floor, so a trained person
is dearer by the trade's training premium. Merchants carry people from where the owners' ask is low to where the buyers'
bid is high and the carriage is paid by the price: a person is bought wherever ask plus carriage stays under the bid,
cheapest first. Nothing here names a trade, an area or an owner.
"""
import dataclasses
import heapq
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from .expectations import annuity_factor
from .premium import training_premium


@dataclasses.dataclass(frozen=True)
class BondedLot:
    """People of a trade bought in `origin` for `destination`: the owners' ask and the carriage, per person."""
    destination: str
    trade: str
    origin: str
    people: float
    ask: float
    carriage: float
    payers: Tuple[Tuple[str, float], ...] = ()   # (employer, share of the price) of those who pay and hold the people

    @property
    def price(self) -> float:
        return self.ask + self.carriage


def worth_of_hours(wage_per_hour: float, hours_per_year: float, career_years: float, discount_rate: float) -> float:
    """Present value of a person's hours over a working life at `wage_per_hour`, discounted at the rate lenders ask."""
    return max(0.0, wage_per_hour) * max(0.0, hours_per_year) * annuity_factor(discount_rate, career_years)


def trained_wage_per_hour(trade_wage: Optional[float], floor_per_hour: float, training_years: float,
                          discount_rate: float, career_years: float) -> float:
    """The wage an hour of a trained person fetches: the trade's wage where it is practised, never less than the
    floor wage plus what its training years add (training_premium); with no practice, that premium wage."""
    premium_wage = max(0.0, floor_per_hour) * training_premium(training_years, discount_rate, career_years)
    return max(premium_wage, trade_wage) if trade_wage is not None and trade_wage > 0.0 else premium_wage


def cheapest_carriage(routes: Mapping[str, Sequence], origin: str, destination: str) -> Optional[float]:
    """The least that moving a person costs along the routes (`Route`-like rows with `destination` and
    `moving_cost`); 0 for no move; None when no way leads there."""
    if origin == destination:
        return 0.0
    best: Dict[str, float] = {origin: 0.0}
    queue: List[Tuple[float, str]] = [(0.0, origin)]
    while queue:
        cost, area = heapq.heappop(queue)
        if area == destination:
            return cost
        if cost > best.get(area, float("inf")):
            continue
        for route in routes.get(area, ()):
            step = cost + max(0.0, route.moving_cost)
            if step < best.get(route.destination, float("inf")):
                best[route.destination] = step
                heapq.heappush(queue, (step, route.destination))
    return None


def carriage_from(routes: Mapping[str, Sequence], origin: str) -> Dict[str, float]:
    """`cheapest_carriage` from one origin to every area a way leads to, in one search."""
    best: Dict[str, float] = {origin: 0.0}
    queue: List[Tuple[float, str]] = [(0.0, origin)]
    while queue:
        cost, area = heapq.heappop(queue)
        if cost > best.get(area, float("inf")):
            continue
        for route in routes.get(area, ()):
            step = cost + max(0.0, route.moving_cost)
            if step < best.get(route.destination, float("inf")):
                best[route.destination] = step
                heapq.heappush(queue, (step, route.destination))
    return best


def buy_lots(destination: str, trade: str, wanted: float, bid_worth: float,
             for_sale: Dict[str, float], ask_by_origin: Mapping[str, float],
             carriage_by_origin: Mapping[str, Optional[float]]) -> List[BondedLot]:
    """Lots bought for `wanted` people, cheapest landed price first, none dearer than `bid_worth`. `for_sale` (origin ->
    people left of the trade) is drawn down by what is bought."""
    options = []
    for origin in sorted(for_sale):
        carriage = carriage_by_origin.get(origin)
        if carriage is None or for_sale[origin] <= 0.0 or origin not in ask_by_origin:
            continue
        landed = ask_by_origin[origin] + carriage
        if landed <= bid_worth:
            options.append((landed, origin, carriage))
    lots: List[BondedLot] = []
    remaining = wanted
    for landed, origin, carriage in sorted(options):
        if remaining <= 1e-12:
            break
        take = min(remaining, for_sale[origin])
        lots.append(BondedLot(destination, trade, origin, take, landed - carriage, carriage))
        for_sale[origin] -= take
        remaining -= take
    return lots
