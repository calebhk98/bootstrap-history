"""A market's demand as one evaluator: the buyers' schedules summed, with one power call per distinct
(reference price, elasticity) pair instead of one per buyer. Rows keep the order of the bids given."""
import math
from bisect import bisect_right
from operator import attrgetter, itemgetter
from typing import List, Optional, Sequence

import numpy

from .types import Bid

_SCHEDULE_FIELDS = attrgetter("floor_quantity", "flexible_quantity", "reference_price", "elasticity", "budget",
                              "maximum_price", "priority")
_MAXIMUM = itemgetter(3)
_CONSTANT = (1.0, 0.0)    # the schedule of a buyer whose want does not move with price


class DemandSchedule:
    """Demand at a price, and each buyer's own quantity at it, for bids already in their final order."""

    def __init__(self, bids: Sequence[Bid]):
        group_of: dict = {}
        self.group_terms: List[tuple] = []
        self.group_rows: List[list] = []
        self.rows: List[tuple] = []
        self.maximums: List[float] = []      # each bid's maximum price, in the order of the bids
        self.priorities: List[float] = []    # each bid's priority tier, in the order of the bids
        for floor, flexible, reference, elasticity, budget, maximum, priority in map(_SCHEDULE_FIELDS, bids):
            self.maximums.append(maximum)
            self.priorities.append(priority)
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
        self._negated_terms = [(reference, -elasticity) for reference, elasticity in self.group_terms]
        self._packed: Optional[List[tuple]] = None
        self._totals: dict = {}              # total_at by price: a market is cleared at the same prices many times
        self._uncapped_terms: Optional[List[tuple]] = None
        self._ceilings: Optional[List[float]] = None
        self.solutions: dict = {}            # solve_price's memo: books against this demand share it
        self._arrays: Optional[tuple] = None

    def distinct_schedules(self) -> int:
        return len(self.group_terms)

    def uncapped_at(self, price: float) -> float:
        """Demand ignoring budgets: never below `total_at`, and one step per distinct schedule."""
        terms = self._uncapped_terms
        if terms is None:
            terms = self._uncapped_terms = [
                (reference, negated, math.fsum(row[0] for row in rows), math.fsum(row[1] for row in rows))
                for (reference, negated), rows in zip(self._negated_terms, self.group_rows)]
        try:
            return sum([floors + flexibles * ((price / reference) ** negated)
                        for reference, negated, floors, flexibles in terms])
        except OverflowError:
            return sum([floors + flexibles * factor for factor, (_reference, _negated, floors, flexibles)
                        in zip(self._flexible_factors(price), terms)])

    def _flexible_factors(self, price: float) -> List[float]:
        try:
            return [(price / reference) ** negated for reference, negated in self._negated_terms]
        except OverflowError:
            pass
        factors = []
        for reference, negated in self._negated_terms:
            try:
                factors.append((price / reference) ** negated)
            except OverflowError:
                factors.append(math.inf)
        return factors

    def ceilings_descending(self) -> List[float]:
        """The buyers' finite maximum prices, distinct, dearest first."""
        if self._ceilings is None:
            self._ceilings = sorted({maximum for maximum in self.maximums if maximum < math.inf}, reverse=True)
        return self._ceilings

    def total_at(self, price: float) -> float:
        """Total quantity wanted at a price; at zero or below, every buyer with a budget takes its floor plus its
        flexible part, the same limit `quantity_at` returns, since a budget cap cannot bind on a free good."""
        if price <= 0.0:
            return math.fsum(self._free_each())
        total = self._totals.get(price)
        if total is None:
            total = self._totals[price] = self._capped_total_at(price) if self.price_capped else self._total_at(price)
        return total

    def _total_at(self, price: float) -> float:
        total = 0.0
        for factor, rows in zip(self._flexible_factors(price), self.group_rows):
            total += sum([min(floor + flexible * factor, budget / price) for floor, flexible, budget, _group in rows])
        return total

    def _capped_total_at(self, price: float) -> float:
        """`fsum(each_at(price))` without the buyers priced out (they add exactly zero); fsum is exact, so row order is free."""
        packed = self._packed
        if packed is None:
            packed = self._packed = self._pack()
        wanted: List[float] = []
        try:
            for reference, negated, rows, keys in packed:
                factor = (price / reference) ** negated
                count = bisect_right(keys, -price)
                if count:
                    wanted += [(cap if (cap := budget / price) < (want := floor + flexible * factor) else want)
                               for floor, flexible, budget in (rows if count == len(rows) else rows[:count])]
        except OverflowError:
            return self._capped_total_overflowing(price)
        return math.fsum(wanted)

    def _pack(self) -> List[tuple]:
        """Per group: its terms, its (floor, flexible, budget) rows with the dearest ceiling first, and the
        negated ceilings in the same order (ascending, for bisection)."""
        by_group: List[list] = [[] for _ in self.group_terms]
        for (floor, flexible, budget, group), maximum in zip(self.rows, self.maximums):
            if budget > 0.0:
                by_group[group].append((floor, flexible, budget, maximum))
        packed = []
        for (reference, negated), rows in zip(self._negated_terms, by_group):
            rows.sort(key=_MAXIMUM, reverse=True)
            packed.append((reference, negated, [row[:3] for row in rows], [-row[3] for row in rows]))
        return packed

    def _capped_total_overflowing(self, price: float) -> float:
        wanted: List[float] = []
        for factor, (_reference, _negated, rows, keys) in zip(self._flexible_factors(price), self._pack()):
            count = bisect_right(keys, -price)
            wanted += [min(floor + flexible * factor, budget / price) for floor, flexible, budget in rows[:count]]
        return math.fsum(wanted)

    def each_at(self, price: float) -> List[float]:
        """Each bid's quantity at a price, in the order of the bids; at zero or below see `total_at`."""
        if price <= 0.0:
            return self._free_each()
        factors = self._flexible_factors(price)
        if self.price_capped:
            return [0.0 if price > maximum else min(floor + flexible * factors[group], budget / price)
                    for (floor, flexible, budget, group), maximum in zip(self.rows, self.maximums)]
        return [min(floor + flexible * factors[group], budget / price) for floor, flexible, budget, group in self.rows]

    def _free_each(self) -> List[float]:
        return [floor + flexible for floor, flexible, _budget, _group in self.rows]    # a bid without a budget has none

    def maximum_array(self) -> "numpy.ndarray":
        """Each bid's maximum price, in the order of the bids."""
        return self._columns()[5]

    def _columns(self) -> tuple:
        arrays = self._arrays
        if arrays is None:
            table = numpy.array(self.rows, dtype=float).reshape(-1, 4)
            floors, flexibles, budgets = table[:, 0].copy(), table[:, 1].copy(), table[:, 2].copy()
            groups = table[:, 3].astype(numpy.intp)
            maximums = numpy.array(self.maximums, dtype=float)
            arrays = self._arrays = (floors, flexibles, budgets, groups, numpy.array(self._negated_terms, dtype=float).reshape(-1, 2),
                                     maximums)
        return arrays

    def kernel_arrays(self) -> tuple:
        """(floors, flexibles, budgets, references, exponents, maximums, capped) per bid in the order of the bids, for
        goods_market_kernels."""
        floors, flexibles, budgets, groups, terms, maximums = self._columns()
        return (floors, flexibles, budgets, terms[groups, 0].copy(), terms[groups, 1].copy(), maximums, self.price_capped)

    def tier_bounds(self) -> "numpy.ndarray":
        """Where each priority tier of the bids (contiguous, in tier order) starts, and the count of bids at the end."""
        priorities = numpy.array(self.priorities, dtype=float)
        starts = numpy.flatnonzero(priorities[1:] != priorities[:-1]) + 1
        return numpy.concatenate(([0], starts, [len(priorities)])).astype(numpy.int64) if len(priorities) else numpy.zeros(1, dtype=numpy.int64)

    def matrix_at(self, prices: "numpy.ndarray") -> "numpy.ndarray":
        """`each_at` for many prices at once: row per price, column per bid, the same values to rounding."""
        floors, flexibles, budgets, groups, terms, maximums = self._columns()
        column = prices[:, None]
        with numpy.errstate(all="ignore"):
            factors = (column / terms[:, 0][None, :]) ** terms[:, 1][None, :]
            wanted = floors[None, :] + numpy.where(flexibles > 0.0, flexibles[None, :] * factors[:, groups], 0.0)
            wanted = numpy.minimum(wanted, budgets[None, :] / column)
            wanted = numpy.where(column <= 0.0, (floors + flexibles)[None, :], wanted)    # a free good: see `total_at`
        if self.price_capped:
            wanted[column > maximums[None, :]] = 0.0
        return wanted
