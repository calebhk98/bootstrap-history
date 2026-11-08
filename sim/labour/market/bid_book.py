"""The year's bids as columns: employers' demands for hours of a trade in an area, cut into tranches inside a kernel.

A caller may hand the core `EmployerHoursBid` objects (a plain sequence: tests, a mod, anything not yet on the tables) or
`TrancheBids`: the employers' own bids, each cut into a number of equal-hours tranches whose maximum wages average the bid's own
(the economy's `labour_bids.sloped_bids`, which makes the objects the plain path reads). The core reads either as the same
columns (`columns_of`), so the tranches never exist as Python objects on the table path. `TrancheBids` still iterates as the
tranche `EmployerHoursBid`s, built on first use, for the readers that want objects.
"""
from collections.abc import Sequence as SequenceBase
from operator import attrgetter
from typing import List, NamedTuple, Sequence

import numpy

from sim.jit import njit

from .records import EmployerHoursBid


class TrancheBids(SequenceBase):
    """Bids (objects with employer, trade, area, hours and maximum_wage) cut into `tranches` tranches each. A bid of no hours
    gives none. Tranche k of a bid holds `hours / tranches` hours at `maximum_wage * (1 + spread * (0.5 - (k + 0.5) / tranches))`."""

    def __init__(self, bids: Sequence, tranches, spread: float):
        self.bids = [bid for bid in bids if bid.hours > 0.0]
        self.tranches = tranches
        self.count = int(tranches)
        self.factors = [1.0 + spread * (0.5 - (index + 0.5) / tranches) for index in range(self.count)]
        self._objects: List[EmployerHoursBid] = []
        self._columns = None
        self._numbered = None

    def __len__(self) -> int:
        return len(self.bids) * self.count

    def objects(self) -> List[EmployerHoursBid]:
        if not self._objects and self.bids:
            hours = [bid.hours / self.tranches for bid in self.bids]
            self._objects = [EmployerHoursBid(bid.employer, bid.trade, bid.area, share, bid.maximum_wage * factor)
                             for bid, share in zip(self.bids, hours) for factor in self.factors]
        return self._objects

    def __getitem__(self, index):
        return self.objects()[index]

    def __iter__(self):
        return iter(self.objects())


class BidColumns(NamedTuple):
    """The bids as columns. `employers`, `trades` and `areas` hold one name per bid as handed over; each of the `repeat`
    tranches of a bid follows it in `hours` and `maximum_wage` (so those are `repeat` times as long)."""
    employers: List[str]
    trades: List[str]
    areas: List[str]
    hours: numpy.ndarray         # hours wanted in each tranche (hours)
    maximum_wage: numpy.ndarray  # most an hour is worth to the employer in each tranche (currency per hour)
    repeat: int


@njit
def cut_into_tranches(hours, maximum_wage, divisor, factors, tranche_hours, tranche_wage):
    """Bid `bid` becomes tranches `bid * count .. bid * count + count - 1`: its hours over `divisor` and its maximum wage times
    each of `factors`."""
    count = factors.shape[0]
    for bid in range(hours.shape[0]):
        for tranche in range(count):
            tranche_hours[bid * count + tranche] = hours[bid] / divisor
            tranche_wage[bid * count + tranche] = maximum_wage[bid] * factors[tranche]


def columns_of(bids: Sequence) -> BidColumns:
    """The columns of a year's bids, whichever form they came in (made once for `TrancheBids`)."""
    if isinstance(bids, TrancheBids):
        if bids._columns is None:
            bids._columns = _tranche_columns(bids)
        return bids._columns
    return BidColumns(list(map(attrgetter("employer"), bids)), list(map(attrgetter("trade"), bids)),
                      list(map(attrgetter("area"), bids)), numpy.fromiter(map(attrgetter("hours"), bids), numpy.float64, len(bids)),
                      numpy.fromiter(map(attrgetter("maximum_wage"), bids), numpy.float64, len(bids)), 1)


def _tranche_columns(bids: TrancheBids) -> BidColumns:
    raw = bids.bids
    hours = numpy.fromiter(map(attrgetter("hours"), raw), numpy.float64, len(raw))
    wage = numpy.fromiter(map(attrgetter("maximum_wage"), raw), numpy.float64, len(raw))
    tranche_hours = numpy.empty(len(raw) * bids.count)
    tranche_wage = numpy.empty(len(raw) * bids.count)
    cut_into_tranches(hours, wage, float(bids.tranches), numpy.array(bids.factors), tranche_hours, tranche_wage)
    return BidColumns(list(map(attrgetter("employer"), raw)), list(map(attrgetter("trade"), raw)), list(map(attrgetter("area"), raw)),
                      tranche_hours, tranche_wage, bids.count)


class NumberedBids(NamedTuple):
    """The bids' columns with their names turned into the state's numbers (-1 where the state numbers no such area or trade)."""
    employer: numpy.ndarray
    area: numpy.ndarray
    trade: numpy.ndarray
    hours: numpy.ndarray           # hours wanted in each tranche
    maximum_wage: numpy.ndarray    # most an hour is worth to the employer in each tranche


def numbered(state, bids: Sequence) -> NumberedBids:
    """The bids as numbers on the state's numbering, employers numbered as they are met. Worked out once while the numbering is the
    same, for `TrancheBids`."""
    ids = state.ids
    key = (len(ids.areas), len(ids.trades), len(ids.employers))
    cached = getattr(bids, "_numbered", None)
    if cached is not None and cached[0] == key:
        return cached[1]
    columns = columns_of(bids)
    employer = ids.employers.admit(columns.employers)
    area = numpy.array([-1 if ids.areas.find(name) is None else ids.areas.find(name) for name in columns.areas], numpy.int64)
    trade = numpy.array([-1 if ids.trades.find(name) is None else ids.trades.find(name) for name in columns.trades], numpy.int64)
    result = NumberedBids(*(numpy.repeat(each, columns.repeat) for each in (employer, area, trade)), columns.hours, columns.maximum_wage)
    if isinstance(bids, TrancheBids):
        bids._numbered = ((len(ids.areas), len(ids.trades), len(ids.employers)), result)
    return result
