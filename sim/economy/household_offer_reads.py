"""The year's labour offers read as columns by the household decisions (household_work_year, household_hours_year): what the
plain loops over `LabourOffer` records computed per cohort and per market, from the columns of `LabourOfferRows`.

`OfferReads(rows)` sorts the rows by worker once (stable, so a worker's rows keep the order the offers were made) and finds each
distinct (trade, area) market once. Every figure equals the record loop's to the last digit (`household_offer_kernels` adds the way
CPython's `sum` does); `exact` is False when an hour or a wage is NaN or infinite, which the kernels do not reproduce: the caller
then runs the plain loop on records."""
from typing import Callable, Dict, Optional, Tuple

import numpy

from . import household_offer_kernels as kernels
from .labour_offer_rows import LabourOfferRows


class OfferReads:
    """Columns of one set of offers, grouped by worker and by market."""

    def __init__(self, rows: LabourOfferRows):
        worker, trade, area, hours, reservation = rows.columns()
        self.rows = rows
        self.worker_count = len(rows.workers)
        self.order = numpy.argsort(worker, kind="stable")
        sorted_worker = worker[self.order]
        numbers = numpy.arange(self.worker_count, dtype=numpy.int64)
        self.start = numpy.searchsorted(sorted_worker, numbers, side="left").astype(numpy.int64)
        self.end = numpy.searchsorted(sorted_worker, numbers, side="right").astype(numpy.int64)
        self.hours = hours
        self.sorted_hours = hours[self.order]
        self.reservation = reservation
        width = max(len(rows.areas), 1)
        distinct, inverse = numpy.unique(trade * width + area, return_inverse=True)
        self.market_of_offer = inverse.reshape(-1)
        trade_names, area_names = rows.trades.names, rows.areas.names
        self.markets = [(trade_names[each // width], area_names[each % width]) for each in distinct.tolist()]
        self.exact = bool(numpy.isfinite(hours).all() and numpy.isfinite(reservation).all())

    def worker_number(self, name: str) -> Optional[int]:
        """The place of a worker's name among the rows' workers, None for a name with no offer."""
        return self.rows.workers.number_of.get(name)

    def hours_of_workers(self) -> numpy.ndarray:
        """Each worker's hours over all its offers (hours per year), indexed by worker number."""
        return kernels.hours_by_worker(self.start, self.end, self.sorted_hours)

    def market_values(self, value_of: Callable[[str, str], float]) -> numpy.ndarray:
        """`value_of(trade, area)` for each distinct market, in the order of `markets`."""
        return numpy.array([value_of(trade, area) for trade, area in self.markets], dtype=numpy.float64)

    def faced_wage(self, recorded_wage: Callable[[str, str], Optional[float]]) -> numpy.ndarray:
        """Per offer, the wage its seller faces: the market's recorded wage, else the offer's reservation wage
        (`trade_wages.faced_wage`)."""
        recorded = [recorded_wage(trade, area) for trade, area in self.markets]
        known = numpy.array([each is not None for each in recorded], dtype=numpy.bool_)
        found = numpy.array([0.0 if each is None else each for each in recorded], dtype=numpy.float64)
        return numpy.where(known[self.market_of_offer], found[self.market_of_offer], self.reservation)

    def hour_value_of_workers(self, faced_wage: numpy.ndarray, share_of_market: Optional[numpy.ndarray] = None) -> numpy.ndarray:
        """Each worker's wage per hour averaged over its hours (`households_work.hour_value`), indexed by worker number: the
        faced wage per offer, times the share expected to sell in the offer's market (`share_of_market`, per distinct market;
        omitted: every share is one, `household_hours_year.wage_faced_per_hour`)."""
        wage = faced_wage if share_of_market is None else faced_wage * share_of_market[self.market_of_offer]
        scratch = numpy.zeros(len(self.hours))
        return kernels.hour_value_by_worker(self.start, self.end, self.sorted_hours, wage[self.order], scratch, scratch.copy())

    def hours_by_market(self) -> Dict[Tuple[str, str], float]:
        """{(trade, area): hours offered}, hours added in row order, markets in the order the first offer of each came."""
        totals = kernels.sum_in_order_by_group(self.market_of_offer, len(self.markets), self.hours).tolist()
        first = numpy.unique(self.market_of_offer, return_index=True)[1]
        return {self.markets[market]: totals[market] for market in numpy.argsort(first).tolist()}
