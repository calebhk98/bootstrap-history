"""The year's labour bids as one table of rows (docs/architecture/COMPILED_YEAR.md, stage 4): every writer of bids (the plans, the
carriers, the state, the mint, a seat's staff) appends rows here, and the labour core reads the columns, so no bid object is made
per bid inside the year.

Columns of `LabourBids` (one row per bid, in the order the bids arrived; that order is the bid's sequence and it breaks ties in the
core, which ranks bids by maximum wage, then hours, then employer):
    employer       who bids: a place in `names.employers`                                   employer number
    trade          the trade the hours are for: a place in `names.trades`                    trade number
    area           the labour area the hours are in: a place in `names.areas`                area number
    hours          hours wanted                                                              hours per year
    maximum_wage   the most an hour is worth to the employer                                 money per hour

The numbers are this table's own, given in the order a name first arrives (`RowNames`). The core numbers employers again in name
order, so nothing downstream depends on the arrival order. Objects exist only at the edge: `objects()` (tests, the plain path of
the core) and `add_objects` (a protocol edge that still hands over bid records)."""
from typing import Dict, Iterable, List, Sequence

import numpy

from sim.compiled_tables.spec import Column, TableSpec

from .records import EmployerHoursBid

LABOUR_BIDS = TableSpec("LabourBids", (
    Column("employer", numpy.int64, "who bids: a place in the table's employer names", "employer number", ids="employers"),
    Column("trade", numpy.int64, "the trade the hours are for: a place in the table's trade names", "trade number", ids="trades"),
    Column("area", numpy.int64, "the labour area the hours are in: a place in the table's area names", "area number", ids="areas"),
    Column("hours", numpy.float64, "hours wanted (a bid of no hours makes no tranche)", "hours per year"),
    Column("maximum_wage", numpy.float64, "the most an hour is worth to the employer", "money per hour"),
))
LabourBids = LABOUR_BIDS.make_type(__name__)


class RowNames:
    """Names numbered in the order they first arrive; a name keeps its number."""

    def __init__(self) -> None:
        self.names: List[str] = []
        self.number_of: Dict[str, int] = {}

    def __len__(self) -> int:
        return len(self.names)

    def number(self, name: str) -> int:
        """The name's number, given the next one when the name is new."""
        found = self.number_of.get(name)
        if found is None:
            found = self.number_of[name] = len(self.names)
            self.names.append(name)
        return found

    def numbers(self, names: Iterable[str]) -> numpy.ndarray:
        """The numbers of the names, in the order given (new names numbered as they come)."""
        names = list(names)
        found = self.number_of
        for name in dict.fromkeys(names):
            if name not in found:
                found[name] = len(self.names)
                self.names.append(name)
        return numpy.fromiter(map(found.__getitem__, names), dtype=numpy.int64, count=len(names))


class RowBlocks:
    """Rows of several columns, appended one at a time or as arrays and read back as whole columns in arrival order.

    `dtypes` gives the numpy type of each column. The columns `columns()` returns are the collection's own: a kernel that changes
    one in place changes what every later read sees, and rows appended afterwards follow them."""

    def __init__(self, dtypes: Sequence) -> None:
        self._dtypes = tuple(dtypes)
        self._blocks: List[tuple] = []
        self._pending: tuple = tuple([] for _each in self._dtypes)      # rows added one at a time, not yet in a block
        self._count = 0
        self._columns = None

    def __len__(self) -> int:
        return self._count

    def append_row(self, *values) -> None:
        """One row; a value per column."""
        for column, value in zip(self._pending, values):
            column.append(value)
        self._count += 1
        self._columns = None

    def append_block(self, *columns) -> None:
        """Many rows at once; an array per column, all of one length."""
        if not len(columns[0]):
            return
        self._flush()
        self._blocks.append(tuple(numpy.asarray(column, dtype=dtype) for column, dtype in zip(columns, self._dtypes)))
        self._count += len(columns[0])
        self._columns = None

    def _flush(self) -> None:
        if self._pending[0]:
            self._blocks.append(tuple(numpy.array(column, dtype=dtype) for column, dtype in zip(self._pending, self._dtypes)))
            self._pending = tuple([] for _each in self._dtypes)

    def columns(self) -> tuple:
        """One array per column, exactly as long as the rows."""
        if self._columns is None:
            self._flush()
            if len(self._blocks) == 1:
                self._columns = self._blocks[0]
            elif self._blocks:
                self._columns = tuple(numpy.concatenate(each) for each in zip(*self._blocks))
            else:
                self._columns = tuple(numpy.zeros(0, dtype) for dtype in self._dtypes)
            self._blocks = [self._columns] if self._count else []
        return self._columns


class LabourBidTable(RowBlocks):
    """The year's labour bids: rows are appended in arrival order, then read as the `LabourBids` table (`table()`)."""

    def __init__(self) -> None:
        super().__init__((numpy.int64, numpy.int64, numpy.int64, numpy.float64, numpy.float64))
        self.employers, self.trades, self.areas = RowNames(), RowNames(), RowNames()
        self._table = None

    def add(self, employer: str, trade: str, area: str, hours: float, maximum_wage: float) -> None:
        """One bid as a row."""
        self.append_row(self.employers.number(employer), self.trades.number(trade), self.areas.number(area), hours, maximum_wage)
        self._table = None

    def add_rows(self, employer: numpy.ndarray, trade: numpy.ndarray, area: numpy.ndarray, hours: numpy.ndarray,
                 maximum_wage: numpy.ndarray) -> None:
        """Many bids at once, their employers, trades and areas already numbered by this table's names."""
        self.append_block(employer, trade, area, hours, maximum_wage)
        self._table = None

    def add_named(self, employers: Sequence[str], trades: Sequence[str], areas: Sequence[str], hours, maximum_wage) -> None:
        """Many bids given by name (the employer, trade and area of each), numbered here."""
        self.add_rows(self.employers.numbers(employers), self.trades.numbers(trades), self.areas.numbers(areas), hours, maximum_wage)

    def add_objects(self, bids: Iterable) -> None:
        """Bids handed over as records with `employer`, `trade`, `area`, `hours` and `maximum_wage` (a protocol edge, a test)."""
        for bid in bids:
            self.add(bid.employer, bid.trade, bid.area, bid.hours, bid.maximum_wage)

    extend = add_objects

    def table(self):
        """The rows as a `LabourBids` table, exactly as long as the bids. Its columns are the table's own: a kernel that cuts the
        hours of a bid (bondage placement) changes what the next read of the table sees."""
        if self._table is None:
            columns = self.columns()
            rows = len(columns[0])
            self._table = LabourBids(numpy.array([rows], dtype=numpy.int64), numpy.array([rows], dtype=numpy.int64), *columns)
        return self._table

    def objects(self) -> List[EmployerHoursBid]:
        """The bids as records, in order (an edge: tests, the core's plain path)."""
        table = self.table()
        employers, trades, areas = self.employers.names, self.trades.names, self.areas.names
        return [EmployerHoursBid(employers[employer], trades[trade], areas[area], hours, wage) for employer, trade, area, hours, wage
                in zip(table.employer.tolist(), table.trade.tolist(), table.area.tolist(), table.hours.tolist(), table.maximum_wage.tolist())]

    def __iter__(self):
        return iter(self.objects())

    def __getitem__(self, index):
        return self.objects()[index]

    def copy(self) -> "LabourBidTable":
        """The same bids in columns of their own (hours cut on the copy leave these alone); the names are shared."""
        found = LabourBidTable()
        found.employers, found.trades, found.areas = self.employers, self.trades, self.areas
        found.add_rows(*(column.copy() for column in self.columns()))
        return found
