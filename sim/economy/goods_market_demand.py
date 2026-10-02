"""A market's demand as one evaluator: the buyers' schedules summed, with one power call per distinct
(reference price, elasticity) pair instead of one per buyer. Rows keep the order of the bids given."""
import math
from operator import attrgetter
from typing import List, Sequence

from .types import Bid

_SCHEDULE_FIELDS = attrgetter("floor_quantity", "flexible_quantity", "reference_price", "elasticity", "budget",
                              "maximum_price")
_CONSTANT = (1.0, 0.0)    # the schedule of a buyer whose want does not move with price


class DemandSchedule:
    """Demand at a price, and each buyer's own quantity at it, for bids already in their final order."""

    def __init__(self, bids: Sequence[Bid]):
        group_of: dict = {}
        self.group_terms: List[tuple] = []
        self.group_rows: List[list] = []
        self.rows: List[tuple] = []
        self.group_sums: List[tuple] = []
        self.maximums: List[float] = []      # each bid's maximum price, in the order of the bids
        for floor, flexible, reference, elasticity, budget, maximum in map(_SCHEDULE_FIELDS, bids):
            self.maximums.append(maximum)
            if budget <= 0.0:
                floor, flexible, budget, key = 0.0, 0.0, 0.0, _CONSTANT
            elif flexible > 0.0 and reference > 0.0:
                key = (reference, elasticity)
            else:
                flexible, key = 0.0, _CONSTANT
            group = group_of.get(key)
            if group is None:
                group = group_of[key] = len(self.group_terms)
                self.group_terms.append(key)
                self.group_rows.append([])
            row = (floor, flexible, budget, group)
            self.rows.append(row)
            if budget > 0.0:
                self.group_rows[group].append(row)

        self.price_capped = any(maximum < math.inf for maximum in self.maximums)

    def distinct_schedules(self) -> int:
        return len(self.group_terms)

    def uncapped_at(self, price: float) -> float:
        """Demand ignoring budgets: never below `total_at`, and one step per distinct schedule."""
        if not self.group_sums:
            self.group_sums = [(math.fsum(row[0] for row in rows), math.fsum(row[1] for row in rows))
                               for rows in self.group_rows]
        return sum([floors + flexibles * factor for factor, (floors, flexibles)
                    in zip(self._flexible_factors(price), self.group_sums)])

    def _flexible_factors(self, price: float) -> List[float]:
        factors = []
        for reference, elasticity in self.group_terms:
            try:
                factors.append((price / reference) ** -elasticity)
            except OverflowError:
                factors.append(math.inf)
        return factors

    def total_at(self, price: float) -> float:
        """Total quantity wanted at a positive price."""
        if self.price_capped:
            return math.fsum(self.each_at(price))
        total = 0.0
        for factor, rows in zip(self._flexible_factors(price), self.group_rows):
            total += sum([min(floor + flexible * factor, budget / price) for floor, flexible, budget, _group in rows])
        return total

    def each_at(self, price: float) -> List[float]:
        """Each bid's quantity at a positive price, in the order of the bids."""
        factors = self._flexible_factors(price)
        quantities = [min(floor + flexible * factors[group], budget / price) for floor, flexible, budget, group in self.rows]
        if self.price_capped:
            quantities = [0.0 if price > maximum else quantity for quantity, maximum in zip(quantities, self.maximums)]
        return quantities
