"""The year's labour offers as rows, written by the code that makes them (docs/architecture/COMPILED_YEAR.md, stage 4): one row per
cohort x trade offer, in the order the offers were made (cohorts by id, trades by name, then a seat's own offers). The labour offers
table (`labour_offers_table.py`), the supply, bondage placement and the settlement read these columns, so no `LabourOffer` is made per
offer inside the year; `objects()` builds them at an edge (a household reader not yet on columns, a test).

Columns (`columns()`, one array each, all as long as the rows):
    worker             the household cohort that offers the hours: a place in `workers`           cohort number
    trade              the trade: a place in `trades`                                           trade number
    area               the labour area: a place in `areas`                                       area number
    hours              hours offered before the cohort keeps any at home                         hours per year
    reservation_wage   the wage per hour below which the offer is not made                      money per hour

`trades` and `areas` may be the names of the year's bid table (`LabourBidTable.trades`), so a trade or an area has one number for the
bids and the offers; `workers` is the offers' own."""
from typing import Dict, Iterable, List, Optional, Tuple

import numpy

from sim.labour.api import RowBlocks, RowNames

from .types import LabourOffer


class LabourOfferRows(RowBlocks):
    """Offers appended in arrival order, read as columns."""

    def __init__(self, trades: Optional[RowNames] = None, areas: Optional[RowNames] = None) -> None:
        super().__init__((numpy.int64, numpy.int64, numpy.int64, numpy.float64, numpy.float64))
        self.workers = RowNames()
        self.trades = trades if trades is not None else RowNames()
        self.areas = areas if areas is not None else RowNames()
        self._objects: Optional[List[LabourOffer]] = None

    @classmethod
    def of_objects(cls, offers: Iterable[LabourOffer], trades: Optional[RowNames] = None, areas: Optional[RowNames] = None):
        """The rows of a sequence of `LabourOffer`s (an edge: a test, a seat's orders)."""
        rows = cls(trades, areas)
        rows.add_objects(offers)
        return rows

    def add(self, worker: str, trade: str, area: str, hours: float, reservation_wage: float) -> None:
        """One offer as a row."""
        self.append_row(self.workers.number(worker), self.trades.number(trade), self.areas.number(area), hours, reservation_wage)
        self._objects = None

    def add_rows(self, worker: numpy.ndarray, trade: numpy.ndarray, area: numpy.ndarray, hours: numpy.ndarray,
                 reservation_wage: numpy.ndarray) -> None:
        """Many offers at once, their cohorts, trades and areas already numbered by this collection's names."""
        self.append_block(worker, trade, area, hours, reservation_wage)
        self._objects = None

    def add_objects(self, offers: Iterable[LabourOffer]) -> None:
        for offer in offers:
            self.add(offer.worker, offer.trade, offer.area, offer.hours, offer.reservation_wage)

    extend = add_objects

    def hours_changed(self) -> None:
        """A kernel cut hours in place: records made from the old hours are dropped."""
        self._objects = None

    def objects(self) -> List[LabourOffer]:
        """The offers as records, in order, made on first use and kept while the rows are not appended to. Hours cut in place by
        a kernel (bondage placement) are cut before a reader asks."""
        if self._objects is None:
            worker, trade, area, hours, wage = self.columns()
            workers, trades, areas = self.workers.names, self.trades.names, self.areas.names
            self._objects = [LabourOffer(workers[each], trades[kind], areas[place], amount, reservation) for each, kind, place, amount, reservation
                             in zip(worker.tolist(), trade.tolist(), area.tolist(), hours.tolist(), wage.tolist())]
        return self._objects

    def __iter__(self):
        return iter(self.objects())

    def __getitem__(self, index):
        return self.objects()[index]

    def on_names(self, trades: RowNames, areas: RowNames) -> "LabourOfferRows":
        """These offers numbered by the given trade and area names (self when they already are): the offers and the bids of a year
        share one numbering of trades and areas, and a set of offers made on names of its own is renumbered to it."""
        if trades is self.trades and areas is self.areas:
            return self
        worker, trade, area, hours, wage = self.columns()
        found = LabourOfferRows(trades, areas)
        found.workers = self.workers
        found.append_block(worker.copy(), trades.numbers(self.trades.names)[trade] if len(trade) else trade.copy(),
                           areas.numbers(self.areas.names)[area] if len(area) else area.copy(), hours.copy(), wage.copy())
        return found

    def faced_wages(self, recorded_wage, faced_wage) -> Dict[Tuple[str, str], float]:
        """For each (trade, area) market with an offer, the wage its sellers face: `faced_wage(recorded_wage(trade, area), reservation
        wage of the market's last offer)`. `recorded_wage` is last year's clearing wage or None."""
        _worker, trade, area, _hours, wage = self.columns()
        if not len(trade):
            return {}
        width = max(len(self.areas), 1)
        key = trade * width + area
        distinct, from_end = numpy.unique(key[::-1], return_index=True)
        reservation = wage[len(key) - 1 - from_end].tolist()
        trades, areas = self.trades.names, self.areas.names
        return {(trades[each // width], areas[each % width]): faced_wage(recorded_wage(trades[each // width], areas[each % width]), found)
                for each, found in zip(distinct.tolist(), reservation)}

    def copy(self) -> "LabourOfferRows":
        """The same offers in columns of their own (hours cut on the copy leave these alone)."""
        found = LabourOfferRows(self.trades, self.areas)
        found.workers = self.workers
        found.append_block(*(column.copy() for column in self.columns()))
        return found
