"""What an hour of a trade costs to bring in from elsewhere: the cap on a market where employers want far
more hours than its own workers offer. Wages pulled up by bids no one in the area can fill stop at what
the trade's workers in the cheapest area to fetch them from earn plus the move spread over a career;
beyond that they come, not stay. Only the hours workers sell at a wage count, here and there."""
import heapq
import math
from typing import Dict, List, Optional, Sequence, Tuple

from .records import MarketState, YearInputs


BISECTION_STEPS = 40      # a numerical bound: the search for the wage at which fetched hands fill a shortage


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
        self.most: Dict[Tuple[str, str], float] = {}      # the highest wage any bid for the market would pay
        for bid in inputs.bids:
            self.wanted[(bid.area, bid.trade)] = self.wanted.get((bid.area, bid.trade), 0.0) + max(bid.hours, 0.0)
            self.most[(bid.area, bid.trade)] = max(self.most.get((bid.area, bid.trade), 0.0), bid.maximum_wage)

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

    def hours_at(self, area: str, trade: str, wage: float) -> float:
        """The hours the trade's workers in an area sell at a wage: the hours they keep for plots and leisure are not
        for hire, so where the area has a schedule (`hours_share_at`) only its share of their hours counts."""
        everyone = sum(self.state.workers.get(area, {}).get(trade, ())) * self.inputs.hours_per_worker_year
        share = self.inputs.hours_share_at.get((trade, area))
        return everyone if share is None else everyone * share(wage)

    def _fetched(self, area: str, trade: str, sources: Sequence[str], wage: float) -> float:
        """The hours the trade's workers in the `sources` areas can spare for `area` at a wage: those they sell
        at it beyond what their own employers bid for."""
        return sum(max(0.0, self.hours_at(other, trade, wage) - self.wanted.get((other, trade), 0.0)) for other in sources)

    def wage(self, area: str, trade: str) -> Optional[float]:
        """The wage an hour of `trade` in `area` can be had for by fetching hands from elsewhere, as far as
        hands to spare reach. Each reachable area with a wage for the trade offers the hours its workers sell
        beyond what its own employers bid for, from the wage it pays (never under what its workers need to live
        on, so a glut does not price below their outside option) plus the way's moving cost over a career's
        hours; the more the wage, the more hours they sell. The cap is the lowest wage at which the hours the
        area's own workers sell and the hours fetched fill the hours wanted here. None where the workers on the
        spot sell enough at the going wage already, or the spare hands do not fill the shortage: the bids then
        set the wage."""
        inputs = self.inputs
        wanted = self.wanted.get((area, trade), 0.0)
        going = self.wages.get(area, {}).get(trade, 0.0)
        if self.hours_at(area, trade, going) >= wanted:
            return None
        offers: List[Tuple[float, str]] = []
        for moving_cost, other in self.reach(area):
            wage = self.wages.get(other, {}).get(trade)
            if wage is None:
                continue
            outside = inputs.subsistence_per_worker_year.get(other, 0.0) / max(inputs.hours_per_worker_year, 1e-12)
            offers.append((max(wage, outside) + moving_cost / self.career_hours, other))
        sources: List[str] = []
        lowest = going
        for cost, other in sorted(offers):
            if self.hours_at(area, trade, cost) + self._fetched(area, trade, sources, cost) >= wanted:
                return self._lowest_filling(area, trade, sources, wanted, lowest, cost)
            sources.append(other)
            if self.hours_at(area, trade, cost) + self._fetched(area, trade, sources, cost) >= wanted:
                return cost
            lowest = cost
        # past the dearest way in, a higher wage still draws more of the hours the workers keep back
        top = self.most.get((area, trade), 0.0)
        if top > lowest and self.hours_at(area, trade, top) + self._fetched(area, trade, sources, top) >= wanted:
            return self._lowest_filling(area, trade, sources, wanted, lowest, top)
        return None

    def _lowest_filling(self, area: str, trade: str, sources: Sequence[str], wanted: float, low: float,
                        high: float) -> float:
        """The lowest wage in (low, high] at which the hours sold here and fetched from `sources` fill `wanted`,
        found by bisection on a total that rises with the wage; `high` fills it."""
        for _step in range(BISECTION_STEPS):
            middle = (low + high) / 2.0
            if self.hours_at(area, trade, middle) + self._fetched(area, trade, sources, middle) >= wanted:
                high = middle
            else:
                low = middle
        return high
