"""What an hour of a trade costs to bring in from elsewhere: the cap on a market where employers want far
more hours than its own workers offer. Wages pulled up by bids no one in the area can fill stop at what
the trade's workers in the cheapest area to fetch them from earn plus the move spread over a career;
beyond that they come, not stay. Only the hours workers sell at a wage count, here and there."""
import math
from typing import Dict, List, Optional, Sequence, Tuple

from .fetch_wage import fetch_wage
from .premium import annuity_factor
from .records import MarketState, YearInputs
from .reservation import reservation_wage


class ImportCosts:
    """The year's price of fetching hands of a trade into an area. Wages are those at the start of the year (the
    live state is rewritten as the year's markets clear, so reading it would depend on their order)."""

    def __init__(self, state: MarketState, inputs: YearInputs):
        self.state, self.inputs = state, inputs
        self.wages = {area: dict(by_trade) for area, by_trade in state.wages.items()}
        rate, years = inputs.discount_rate, inputs.career_years
        self.career_hours = max(annuity_factor(rate, years) * inputs.hours_per_worker_year, 1e-12)
        self._reach: Dict[str, List[Tuple[float, str]]] = {}
        self._all: Dict[Tuple[str, str], float] = {}
        self._sold: Dict[Tuple[str, str, float], float] = {}      # hours_at answers: the year's workers do not change while markets clear
        self._spare_sources: Dict[Tuple[str, Tuple[str, ...]], Tuple[List[float], float]] = {}
        self._spare: Dict[Tuple[str, str], float] = {}      # _spare_at_most answers: the same inputs for the whole year
        self._bid_totals: Optional[Tuple[Dict[Tuple[str, str], float], Dict[Tuple[str, str], float]]] = None
        self._bids_by_market: Optional[Dict[Tuple[str, str], list]] = None

    @property
    def wanted(self) -> Dict[Tuple[str, str], float]:
        """(area, trade) -> the hours bid for it."""
        return self._totals()[0]

    @property
    def most(self) -> Dict[Tuple[str, str], float]:
        """(area, trade) -> the highest wage any bid for the market would pay."""
        return self._totals()[1]

    def _totals(self):
        if self._bid_totals is None:
            wanted: Dict[Tuple[str, str], float] = {}
            most: Dict[Tuple[str, str], float] = {}
            for bid in self.inputs.bids:
                wanted[(bid.area, bid.trade)] = wanted.get((bid.area, bid.trade), 0.0) + max(bid.hours, 0.0)
                most[(bid.area, bid.trade)] = max(most.get((bid.area, bid.trade), 0.0), bid.maximum_wage)
            self._bid_totals = (wanted, most)
        return self._bid_totals

    def jobs_at(self, area: str, trade: str, wage: float) -> float:
        """The hours employers bid for a trade in an area at `wage` or more."""
        if self._bids_by_market is None:
            self._bids_by_market = {}
            for bid in self.inputs.bids:
                self._bids_by_market.setdefault((bid.area, bid.trade), []).append(bid)
        return math.fsum(max(bid.hours, 0.0) for bid in self._bids_by_market.get((area, trade), ()) if bid.maximum_wage >= wage)

    def reach(self, area: str) -> List[Tuple[float, str]]:
        """(cheapest moving cost over the routes, area) for every other area reachable from `area`, nearest
        first. The route out of an area is taken to cost the same coming back."""
        if area not in self._reach:
            best = self.inputs.carriage_from(area)
            self._reach[area] = sorted((cost, other) for other, cost in best.items() if other != area)
        return self._reach[area]

    def hours_at(self, area: str, trade: str, wage: float) -> float:
        """The hours the trade's workers in an area sell at a wage: the hours they keep for plots and household work are not
        for hire, so where the year gives a schedule (`hours_sold_at`) only what it sells counts."""
        key = (area, trade, wage)
        sold = self._sold.get(key)
        if sold is None:
            sold = self._sold[key] = self.inputs.hours_sold(trade, area, self.everyone(area, trade), wage)
        return sold

    def everyone(self, area: str, trade: str) -> float:
        """All the hours the trade's workers in an area have, whatever they are paid: no wage sells more."""
        key = (area, trade)
        everyone = self._all.get(key)
        if everyone is None:
            everyone = self._all[key] = sum(self.state.workers.get(area, {}).get(trade, ())) * self.inputs.hours_per_worker_year
        return everyone

    def _spare_at_most(self, area: str, trade: str) -> float:
        """The most hours an area can ever spare for another's bids, at any wage."""
        key = (area, trade)
        spare = self._spare.get(key)
        if spare is None:
            spare = self._spare[key] = max(0.0, self.everyone(area, trade) - self.wanted.get(key, 0.0))
        return spare

    def _spare_of(self, trade: str, sources: Sequence[str]) -> Tuple[List[float], float]:
        """(each source's most spare hours, their sum) for a list of sources: the bisection asks the same list at every step."""
        key = (trade, tuple(sources))
        found = self._spare_sources.get(key)
        if found is None:
            remaining = [self._spare_at_most(other, trade) for other in sources]
            found = self._spare_sources[key] = (remaining, sum(remaining))
        return found

    def going(self, area: str, trade: str) -> Optional[float]:
        """The wage the trade paid in the area at the start of the year; before any is paid, what its hands must be paid
        (the reservation wage); None where the area states no outside option either."""
        paid = self.wages.get(area, {}).get(trade)
        if paid is not None:
            return paid
        return reservation_wage(self.inputs, area, self.inputs.trades[trade].fatality_risk_per_year)

    def wage(self, area: str, trade: str) -> Optional[float]:
        """The wage an hour of `trade` in `area` can be had for by fetching hands from elsewhere, as far as
        hands to spare reach. Each reachable area with a wage for the trade offers the hours its workers sell
        beyond what its own employers bid for, from the wage it pays (never under what its workers need to live
        on, so a glut does not price below their outside option) plus the way's moving cost over a career's
        hours; the more the wage, the more hours they sell. The cap is the lowest wage at which the hours the
        area's own workers sell and the hours fetched fill the hours wanted here. None where the workers on the
        spot sell enough at the going wage already, or the spare hands do not fill the shortage: the bids then
        set the wage. The search is the kernel `fetch_wage`, called as the year's inputs carry it."""
        inputs = self.inputs
        going = self.going(area, trade)
        if going is None:
            return None

        def offers() -> List[Tuple[float, str]]:
            return self._offer_costs(area, trade)
        search = inputs.fetch_wage or fetch_wage
        return search(area, self.wanted.get((area, trade), 0.0), going,
                      self.most.get((area, trade), 0.0), offers,
                      lambda other, wage: self.hours_at(other, trade, wage),
                      lambda other: self.wanted.get((other, trade), 0.0),
                      lambda sources: self._spare_of(trade, sources))

    def supply(self, area: str, trade: str) -> Optional[Tuple[float, float]]:
        """(the wage fetched hands bound, the share of the hours wanted here that can be fetched at it), or None where
        none can come. Where the spare hands fill the shortage the bound is `wage` and the share is the shortage over
        the hours wanted; where they do not, the bound is the dearest way in within the highest wage bid, and the
        share is what the sources spare at it, so the bound grows with the hours that can come instead of
        switching on once they cover the whole shortage."""
        wanted = self.wanted.get((area, trade), 0.0)
        going = self.going(area, trade)
        if going is None:
            return None
        shortage = wanted - self.hours_at(area, trade, going)
        if wanted <= 0.0 or shortage <= 0.0:
            return None
        bound = self.wage(area, trade)
        sources = [other for _cost, other in self.reach(area) if self.wages.get(other, {}).get(trade) is not None]
        if bound is None:
            top = self.most.get((area, trade), 0.0)
            costs = [cost for cost, _other in self._offer_costs(area, trade) if cost <= top]
            if not costs:
                return None
            bound = max(costs)
        cost_of: Dict[str, float] = {}
        for cost, other in self._offer_costs(area, trade):
            cost_of.setdefault(other, cost)
        fetched = sum(max(0.0, self.hours_at(other, trade, bound) - self.wanted.get((other, trade), 0.0)) for other in sources
                      if cost_of.get(other, math.inf) <= bound)
        return bound, min(shortage, fetched) / wanted

    def _offer_costs(self, area: str, trade: str) -> List[Tuple[float, str]]:
        """(wage an area's hands come at, area) for every other area with a wage for the trade."""
        found: List[Tuple[float, str]] = []
        for moving_cost, other in self.reach(area):
            wage = self.wages.get(other, {}).get(trade)
            if wage is None:
                continue
            subsistence = self.inputs.subsistence_per_worker_year.get(other)
            floor = wage if subsistence is None else max(wage, subsistence / max(self.inputs.hours_per_worker_year, 1e-12))
            found.append((floor + moving_cost / self.career_hours, other))
        return found
