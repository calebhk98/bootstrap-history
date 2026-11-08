"""What bondage placement (`bondage_hours.py`) reads and writes besides the offers and the bids: the keep a holder owes as rows, and the
indexes (rows of one market, one worker, one holder in row order) the kernels walk instead of scanning every row."""
from typing import Iterable, Iterator, List, Sequence, Tuple, Union

import numpy

from sim.labour.api import LabourBidTable

from .labour_offer_rows import LabourOfferRows
from .types import LabourBid, LabourOffer


class KeepRows:
    """The keep holders owe for the hours bonded people worked for them: row `i` is `employers[i]` paying `cohorts[i]` `amounts[i]`
    (money). Iterates as `(employer, cohort, money)` tuples."""

    def __init__(self, employers: Sequence[str], cohorts: Sequence[str], amounts):
        self.employers, self.cohorts = list(employers), list(cohorts)
        self.amounts = numpy.asarray(amounts, dtype=numpy.float64)

    @classmethod
    def of_tuples(cls, rows: Iterable[Tuple[str, str, float]]) -> "KeepRows":
        found = list(rows)
        return cls([each[0] for each in found], [each[1] for each in found], [each[2] for each in found])

    def __len__(self) -> int:
        return len(self.employers)

    def __iter__(self) -> Iterator[Tuple[str, str, float]]:
        return iter(zip(self.employers, self.cohorts, self.amounts.tolist()))

    def __eq__(self, other) -> bool:
        return list(self) == list(other)


def as_rows(offers: Union[LabourOfferRows, Sequence[LabourOffer]], bids: Union[LabourBidTable, Sequence[LabourBid]]):
    """(offers, bids) as rows on one numbering of trades and areas, whatever form they were handed over in (records are put into rows)."""
    if not isinstance(bids, LabourBidTable):
        found = LabourBidTable()
        found.add_objects(bids)
        bids = found
    if not isinstance(offers, LabourOfferRows):
        offers = LabourOfferRows.of_objects(offers, bids.trades, bids.areas)
    return offers.on_names(bids.trades, bids.areas), bids


def market_keys(trade: numpy.ndarray, area: numpy.ndarray, area_count: int) -> numpy.ndarray:
    """One number for each (trade, area) of the rows, -1 where either is -1 (a name the rows do not have)."""
    return numpy.where((trade < 0) | (area < 0), -1, trade * max(area_count, 1) + area)


def ranges_of(keys: numpy.ndarray, asked: numpy.ndarray) -> Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]:
    """(order, first, last): `order` lists the rows by key, rows of one key in row order; the rows of key `asked[i]` are
    `order[first[i]:last[i]]` (none for key -1 or a key no row has)."""
    order = numpy.argsort(keys, kind="stable").astype(numpy.int64)
    found = keys[order]
    first = numpy.searchsorted(found, asked, side="left").astype(numpy.int64)
    last = numpy.searchsorted(found, asked, side="right").astype(numpy.int64)
    nothing = asked < 0
    first[nothing] = last[nothing] = 0
    return order, first, last


def numbers_of(names: Sequence[str], row_names) -> List[int]:
    """The number each name has among `row_names` (a `RowNames`), -1 where it has none."""
    found = row_names.number_of
    return [found.get(name, -1) for name in names]
