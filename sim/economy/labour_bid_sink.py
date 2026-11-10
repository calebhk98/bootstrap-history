"""Where a writer of labour bids puts them: rows of the year's `LabourBidTable`, or (a test, a caller not yet on rows) a plain list of
`LabourBid`s.

A writer works out its bids as figures, one tuple `(employer, trade, area, hours, maximum_wage)` each, and hands them to `put_bids`:
the table takes them as rows with no object made, a list gets the objects."""
from typing import Iterable, List, Tuple

from sim.labour.api import LabourBidTable

from .types import LabourBid

BidFigures = Tuple[str, str, str, float, float]


def put_bids(sink, figures: Iterable[BidFigures]) -> None:
    """Add the bids to `sink`, in order."""
    if isinstance(sink, LabourBidTable):
        found = list(figures)
        if found:
            employers, trades, areas, hours, wages = zip(*found)
            sink.add_named(employers, trades, areas, hours, wages)
    else:
        sink.extend(LabourBid(*each) for each in figures)


def bid_objects(figures: Iterable[BidFigures]) -> List[LabourBid]:
    """The figures as `LabourBid` records (an edge: a caller that reads bids as objects)."""
    return [LabourBid(*each) for each in figures]
