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
        self.wanted: Dict[Tuple[str, str], float] = {}
        for bid in inputs.bids:
            self.wanted[(bid.area, bid.trade)] = self.wanted.get((bid.area, bid.trade), 0.0) + max(bid.hours, 0.0)

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
        """The wage an hour of `trade` in `area` can be had for by fetching hands from elsewhere, as far as
        hands to spare reach. Each reachable area with a wage for the trade offers the hours its workers have
        beyond what its own employers bid for, at its wage (never under what its workers need to live on, so a
        glut does not price below their outside option) plus the way's moving cost over a career's hours. The
        cheapest offers are taken until they fill the hours wanted here beyond the area's own hands; the dearest
        one taken is the cap. None where the spare hands do not fill the shortage: the bids then set the wage."""
        inputs = self.inputs
        here = sum(self.state.workers.get(area, {}).get(trade, ())) * inputs.hours_per_worker_year
        shortage = self.wanted.get((area, trade), 0.0) - here
        if shortage <= 0.0:
            return None
        offers: List[Tuple[float, float]] = []
        for moving_cost, other in self.reach(area):
            wage = self.wages.get(other, {}).get(trade)
            if wage is None:
                continue
            spare = (sum(self.state.workers.get(other, {}).get(trade, ())) * inputs.hours_per_worker_year
                     - self.wanted.get((other, trade), 0.0))
            if spare <= 0.0:
                continue        # that area's own employers want all its hands: none to fetch
            outside = inputs.subsistence_per_worker_year.get(other, 0.0) / max(inputs.hours_per_worker_year, 1e-12)
            offers.append((max(wage, outside) + moving_cost / self.career_hours, spare))
        filled = 0.0
        for cost, spare in sorted(offers):
            filled += spare
            if filled >= shortage:
                return cost
        return None
