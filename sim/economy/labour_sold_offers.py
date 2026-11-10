"""The offers of a year as they sold, read from the `LabourOffers` table the supply settled (`labour_supply.HourSupply.settle`).

`SoldOffers` stands where the list of `LabourOffer`s with the hours sold stood: the settlement reads its columns (`labour_fills.sell_rows`:
the hours sold of each offer and the labour market of each), and a reader that wants the records gets them (`objects()`, made on
first use, one per offer, with the hours sold in place of the hours offered)."""
from collections.abc import Sequence as SequenceBase
from typing import Dict, List, Sequence, Tuple

import numpy

from sim.jit import njit

from .types import LabourOffer


@njit
def sum_in_order(values, group, group_count):
    """Per group number, the values of its rows added in row order (the order a Python loop over the offers adds them)."""
    totals = numpy.zeros(group_count)
    for row in range(values.shape[0]):
        totals[group[row]] += values[row]
    return totals


class SoldOffers(SequenceBase):
    """The settled offers: `table` is the `LabourOffers` table (its `sold_hours` filled), `ids` its numberings, `rows` the offers as made."""

    def __init__(self, table, ids, rows, market_names: Sequence[Tuple[str, str]]):
        self.table, self.ids, self.rows = table, ids, rows
        self.market_names = list(market_names)       # (trade, area) of each market number of the table
        self._objects = None

    def __len__(self) -> int:
        return int(self.table.row_count[0])

    def sold_columns(self) -> numpy.ndarray:
        """The hours each offer sold, in the order of the offers."""
        return self.table.sold_hours[:len(self)]

    def market_rows(self, trades: Sequence[str], areas: Sequence[str]) -> numpy.ndarray:
        """For each offer, the row of its (trade, area) among these markets, -1 where the clearing did not cover it."""
        row_of = {(trade, area): row for row, (trade, area) in enumerate(zip(trades, areas))}
        by_market = numpy.array([row_of.get(market, -1) for market in self.market_names], dtype=numpy.int64)
        return by_market[self.table.market[:len(self)]] if len(self) else numpy.zeros(0, dtype=numpy.int64)

    def workers_of(self, offer_rows: numpy.ndarray) -> Tuple[List[str], numpy.ndarray]:
        """(the distinct workers of these offers, for each offer the place of its worker among them)."""
        used, inverse = numpy.unique(self.table.cohort[offer_rows], return_inverse=True)
        return [self.ids.cohorts.name(each) for each in used.tolist()], inverse.reshape(-1).astype(numpy.int64)

    def hours_by_worker(self) -> Dict[str, float]:
        """Each worker's hours sold over its offers, added in the offers' order."""
        cohorts = self.table.cohort[:len(self)]
        totals = sum_in_order(self.sold_columns(), cohorts, len(self.ids.cohorts)).tolist()
        present, first = numpy.unique(cohorts, return_index=True)       # the workers with an offer, in the order their first offer came
        return {self.ids.cohorts.name(number): totals[number] for number in present[numpy.argsort(first)].tolist()}

    def objects(self) -> List[LabourOffer]:
        """The offers as records with the hours they sold."""
        if self._objects is None:
            self._objects = [LabourOffer(offer.worker, offer.trade, offer.area, sold, offer.reservation_wage)
                             for offer, sold in zip(self.rows.objects(), self.sold_columns().tolist())]
        return self._objects

    def __getitem__(self, index):
        return self.objects()[index]

    def __iter__(self):
        return iter(self.objects())


def sold_hours_by_worker(offers: Sequence[LabourOffer]) -> Dict[str, float]:
    """Each worker's hours over its offers, added in the offers' order: from the columns of settled offers, else offer by offer."""
    if hasattr(offers, "hours_by_worker"):
        return offers.hours_by_worker()
    found: Dict[str, float] = {}
    for offer in offers:
        found[offer.worker] = found.get(offer.worker, 0.0) + offer.hours
    return found
