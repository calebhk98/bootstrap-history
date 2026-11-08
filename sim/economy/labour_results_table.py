"""A year's `LabourResult`s kept as columns, and built as objects only for a reader that asks.

`LabourResults` stands where the ledger's list of results stood (`YearLedger.labour_results`): a sequence in (trade, area) order
whose items are `TableLabourResult`s, `LabourResult`s that read their figures from the year's `LabourFills` and build their `Fill`
tuple on first use. The readers inside the year (the state's wage bill, the hours totals) use the columns directly:
`bought_value`, `hours_totals` and `hours_by_market`.
"""
import bisect
import math
from collections.abc import Sequence as SequenceBase
from typing import Dict, List, Tuple

import numpy

from .labour_fills import LabourFills
from .types import Fill, LabourResult


class TableLabourResult(LabourResult):
    """A `LabourResult` whose `fills` are built from the year's columns when first read."""

    def __init__(self, source: "LabourResults", row: int):     # the dataclass initialiser would need every field
        markets = source.fills.markets
        for name, value in (("trade", markets.trade[row]), ("area", markets.area[row]), ("currency", source.currency),
                            ("wage", source.scalars["wage"][row]), ("hours_hired", source.scalars["hours_hired"][row]),
                            ("vacant_hours", source.scalars["vacant_hours"][row]), ("idle_hours", source.scalars["idle_hours"][row])):
            object.__setattr__(self, name, value)
        object.__setattr__(self, "_source", source)
        object.__setattr__(self, "_row", row)

    @property
    def fills(self) -> Tuple[Fill, ...]:
        return self._source.fills_of(self._row)

    def _values(self):
        return (self.trade, self.area, self.currency, self.wage, self.hours_hired, self.vacant_hours, self.idle_hours, self.fills)

    def __eq__(self, other) -> bool:
        return isinstance(other, LabourResult) and self._values() == (
            other.trade, other.area, other.currency, other.wage, other.hours_hired, other.vacant_hours, other.idle_hours, other.fills)

    def __hash__(self) -> int:
        return hash(self._values())


class LabourResults(SequenceBase):
    """The year's results, one per cleared market; `earlier` are results the ledger already held."""

    def __init__(self, fills: LabourFills, currency: str, earlier=()):
        self.fills, self.currency = fills, currency
        self.before: List[LabourResult] = list(earlier)       # noted before the year's markets
        self.after: List[LabourResult] = []                   # noted after them
        markets = fills.markets
        self.scalars = {"wage": markets.wage.tolist(), "hours_hired": markets.hours_hired.tolist(),
                        "vacant_hours": markets.vacant_hours.tolist(), "idle_hours": markets.idle_hours.tolist()}
        self._objects: List[TableLabourResult] = []

    def __len__(self) -> int:
        return len(self.before) + len(self.after) + len(self.fills.markets.wage)

    def _all(self) -> List[LabourResult]:
        if not self._objects:
            self._objects = [TableLabourResult(self, row) for row in range(len(self.fills.markets.wage))]
        return self.before + self._objects + self.after

    def __getitem__(self, index):
        return self._all()[index]

    def __iter__(self):
        return iter(self._all())

    def append(self, result: LabourResult) -> None:
        """A result noted after the year's markets (the ledger's `note_hours` appends here too)."""
        self.after.append(result)

    def fills_of(self, row: int) -> Tuple[Fill, ...]:
        """The market's `Fill`s as `year_labour._result` built them: the employers' buys, then the workers' sells."""
        fills, markets = self.fills, self.fills.markets
        trade, area, wage, names = markets.trade[row], markets.area[row], self.scalars["wage"][row], fills.names
        buys = [Fill(names[ref], trade, area, "", hours, wage, "buy") for ref, hours in zip(
            fills.buy_ref[fills.buy_start[row]:fills.buy_start[row + 1]].tolist(),
            fills.buy_hours[fills.buy_start[row]:fills.buy_start[row + 1]].tolist())]
        sells = [Fill(names[ref], trade, area, "", hours, wage, "sell") for ref, hours in zip(
            fills.sell_ref[fills.sell_start[row]:fills.sell_start[row + 1]].tolist(),
            fills.sell_hours[fills.sell_start[row]:fills.sell_start[row + 1]].tolist())]
        return tuple(buys + sells)

    def bought_value(self, agent: str) -> float:
        """What `agent` paid for the hours it bought, over every market: the exact sum of hours times wage, as the fsum over
        its buy fills gives it (`state_budget.wages_paid`)."""
        fills = self.fills
        found = bisect.bisect_left(fills.names, agent)
        if found >= len(fills.names) or fills.names[found] != agent:
            return 0.0
        market_of_buy = numpy.repeat(numpy.arange(len(fills.markets.wage)), numpy.diff(fills.buy_start))
        mine = fills.buy_ref == found
        return math.fsum((fills.buy_hours[mine] * fills.markets.wage[market_of_buy[mine]]).tolist())

    def hours_totals(self) -> Tuple[float, float]:
        """(hours hired, idle hours) over every result, each added in order as a loop over the results adds them."""
        hired = idle = 0.0
        for result in self.before:
            hired += result.hours_hired
            idle += result.idle_hours
        for amount in self.scalars["hours_hired"]:
            hired += amount
        for amount in self.scalars["idle_hours"]:
            idle += amount
        for result in self.after:
            hired += result.hours_hired
            idle += result.idle_hours
        return hired, idle

    def hours_by_market(self) -> Dict[Tuple[str, str], float]:
        """(trade, area): hours hired plus idle hours, for every market."""
        markets = self.fills.markets
        found = {(result.trade, result.area): result.hours_hired + result.idle_hours for result in self.before}
        found.update({(trade, area): hired + idle for trade, area, hired, idle in zip(
            markets.trade, markets.area, self.scalars["hours_hired"], self.scalars["idle_hours"])})
        found.update({(result.trade, result.area): result.hours_hired + result.idle_hours for result in self.after})
        return found


def hours_totals(results) -> Tuple[float, float]:
    """`LabourResults.hours_totals` of the year's results, or the same sums over a plain list of `LabourResult`s."""
    if isinstance(results, LabourResults):
        return results.hours_totals()
    hired = idle = 0.0
    for result in results:
        hired += result.hours_hired
        idle += result.idle_hours
    return hired, idle


def bought_value(results, agent: str) -> float:
    """What `agent` paid for the hours it bought (hours times wage over its buy fills, summed exactly)."""
    if isinstance(results, LabourResults):
        return results.bought_value(agent)
    return math.fsum(fill.quantity * fill.price for result in results for fill in result.fills if fill.agent == agent and fill.side == "buy")


def hours_by_market(results) -> Dict[Tuple[str, str], float]:
    """`LabourResults.hours_by_market` of the year's results, or the same figures over a plain list of `LabourResult`s."""
    if isinstance(results, LabourResults):
        return results.hours_by_market()
    return {(result.trade, result.area): result.hours_hired + result.idle_hours for result in results}
