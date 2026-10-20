"""What an hour of a trade costs to bring in from elsewhere: the cap on a market where employers want far
more hours than its own workers offer. Wages pulled up by bids no one in the area can fill stop at what
the trade's workers in the cheapest area to fetch them from earn plus the move spread over a career;
beyond that they come, not stay."""
import heapq
import math
from typing import Dict, List, Optional, Tuple

from .records import MarketState, YearInputs


class ImportCosts:
    """The year's price of fetching hands of a trade into an area. Wages are those at the start of the year (the
    live state is rewritten as the year's markets clear, so reading it would depend on their order)."""

    def __init__(self, state: MarketState, inputs: YearInputs):
        self.state, self.inputs = state, inputs
        self.wages = {area: dict(by_trade) for area, by_trade in state.wages.items()}
        rate, years = inputs.discount_rate, inputs.career_years
        discounted_years = years if rate <= 0.0 else (1.0 - math.exp(-rate * years)) / rate
        self.career_hours = max(discounted_years * inputs.hours_per_worker_year, 1e-12)
        self._reach: Dict[str, List[Tuple[float, str]]] = {}

    def reach(self, area: str) -> List[Tuple[float, str]]:
        """(cheapest moving cost over the routes, area) for every other area reachable from `area`, nearest
        first. The route out of an area is taken to cost the same coming back."""
        if area not in self._reach:
            best = {area: 0.0}
            queue = [(0.0, area)]
            while queue:
                cost, here = heapq.heappop(queue)
                if cost > best.get(here, math.inf):
                    continue
                for route in self.inputs.routes.get(here, ()):
                    step = route.moving_cost
                    if not step >= 0.0:
                        step = 0.0      # a route never pays you to move; a negative or unknown cost would loop the search
                    total = cost + step
                    if total < best.get(route.destination, math.inf):
                        best[route.destination] = total
                        heapq.heappush(queue, (total, route.destination))
            self._reach[area] = sorted((cost, other) for other, cost in best.items() if other != area)
        return self._reach[area]

    def wage(self, area: str, trade: str) -> Optional[float]:
        """The cheapest wage an hour of `trade` in `area` can be had for from an area that has hands of the
        trade and a wage for it: that wage (never under what its workers need to live on, so a glut does not
        price below their outside option) plus the way's moving cost over a career's hours. None where no
        reachable area has the trade."""
        inputs = self.inputs
        cheapest: Optional[float] = None
        for moving_cost, other in self.reach(area):
            fare = moving_cost / self.career_hours
            if cheapest is not None and fare >= cheapest:
                break       # farther areas cost more to fetch from, whatever they pay
            wage = self.wages.get(other, {}).get(trade)
            if wage is None or sum(self.state.workers.get(other, {}).get(trade, ())) <= 0.0:
                continue
            outside = inputs.subsistence_per_worker_year.get(other, 0.0) / max(inputs.hours_per_worker_year, 1e-12)
            cost = max(wage, outside) + fare
            if cheapest is None or cost < cheapest:
                cheapest = cost
        return cheapest
