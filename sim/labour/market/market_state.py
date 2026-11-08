"""`MarketState`: what the labour core carries from one year to the next, held as tables (state_tables.py).

Callers outside the compiled year still see nested dicts: `state.workers`, `.trainees`, `.wages`, `.asks` and `.hired_hours`
are live views (state_fields.py) that read and write the tables, and the constructor, `to_plain` and `from_plain` take and
give nested dicts, so a save, a test and the economy's mirrors work unchanged. Code inside the year reads `state.workers_table`
and the other tables directly.

Rows: areas and trades are numbered in sorted name order (state_ids.py), a grid row is `area * trade_count + trade`. Admitting a
new area or trade renumbers (`admit`; the dict views name their pair, so they survive it). The tables hold one band count
(`bands`: the ability band count; a longer list widens the tables, and each list keeps the length it was stored with).
"""
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy

from sim.rekey import rename_text

from . import aptitude
from .state_ids import LabourIds
from .state_tables import AREAS, Areas, HIRED, Hired, MARKETS, Markets, TRAINEES, Trainees, WORKERS, Workers
from .state_fields import AreaMap, AsksField, HiredField, TradeMap, TraineesField, WagesField, WorkersField

_FIELDS = (("workers", WorkersField), ("trainees", TraineesField), ("wages", WagesField), ("hired_hours", HiredField), ("asks", AsksField))


def _spliced(table, spec, start: int, stop: int, replacement: Dict[str, numpy.ndarray], widths: Dict[str, int]):
    """The table with rows `start .. stop - 1` replaced by the given columns (any length), packed to its rows."""
    rows = int(table.row_count[0])
    new_length = None
    columns: List[numpy.ndarray] = []
    for column in spec.columns:
        old = getattr(table, column.name)
        new = numpy.asarray(replacement[column.name], dtype=column.dtype)
        if column.width is not None and new.ndim < 2:
            new = new.reshape(len(new), widths[column.name])
        new_length = len(new)
        columns.append(numpy.concatenate((old[:start], new, old[stop:rows])))
    total = rows - (stop - start) + new_length
    return type(table)(numpy.array([total], dtype=numpy.int64), numpy.array([total], dtype=numpy.int64), *columns)


def _plain_value(value):
    if isinstance(value, float):
        return value
    if hasattr(value, "items"):
        return dict(value.items())
    return [each.plain() if hasattr(each, "plain") else each for each in value]


class MarketState:
    """The core's state: people per area, trade and band; trainee cohorts; wages, asks and hired hours per labour market."""

    def __init__(self, workers=None, trainees=None, wages=None, hired_hours=None, asks=None, ids: Optional[LabourIds] = None):
        self.ids = ids if ids is not None else LabourIds()
        self._order = 0
        self.bands = self._first_width(workers, trainees)
        self._allocate()
        given = {"workers": workers, "trainees": trainees, "wages": wages, "hired_hours": hired_hours, "asks": asks}
        names = [(area, trade) for nested in given.values() if nested for area, by_trade in nested.items() for trade in by_trade]
        self.admit([area for nested in given.values() if nested for area in nested], [trade for _area, trade in names])
        for name, nested in given.items():
            if nested:
                setattr(self, name, nested)

    # -- the dict views ----------------------------------------------------------------------------------------------

    @property
    def workers(self) -> AreaMap:
        return AreaMap(self, WorkersField)

    @workers.setter
    def workers(self, nested) -> None:
        self._replace(WorkersField, nested)

    @property
    def trainees(self) -> AreaMap:
        return AreaMap(self, TraineesField)

    @trainees.setter
    def trainees(self, nested) -> None:
        self._replace(TraineesField, nested)

    @property
    def wages(self) -> AreaMap:
        return AreaMap(self, WagesField)

    @wages.setter
    def wages(self, nested) -> None:
        self._replace(WagesField, nested)

    @property
    def hired_hours(self) -> AreaMap:
        return AreaMap(self, HiredField)

    @hired_hours.setter
    def hired_hours(self, nested) -> None:
        self._replace(HiredField, nested)

    @property
    def asks(self) -> AreaMap:
        return AreaMap(self, AsksField)

    @asks.setter
    def asks(self, nested) -> None:
        self._replace(AsksField, nested)

    def _replace(self, field, nested) -> None:
        view = AreaMap(self, field)
        view.clear()
        nested = dict(nested.items()) if hasattr(nested, "items") else dict(nested)
        self.admit(nested, [trade for by_trade in nested.values() for trade in by_trade])
        for area, by_trade in nested.items():
            view[area] = by_trade

    # -- tables ------------------------------------------------------------------------------------------------------

    @staticmethod
    def _first_width(workers, trainees) -> int:
        for by_area in (workers or {}).values():
            for bands in by_area.values():
                return len(bands)
        for by_area in (trainees or {}).values():
            for cohorts in by_area.values():
                for cohort in cohorts:
                    return len(cohort[1])
        return aptitude.band_count()

    def _allocate(self) -> None:
        """Empty tables for the current areas, trades and band count."""
        rows = len(self.ids.areas) * len(self.ids.trades)
        widths = {"people": self.bands}
        self.workers_table = WORKERS.new_table(Workers, rows, rows, widths)
        self.market_table = MARKETS.new_table(Markets, rows, rows)
        self.market_table.wage[:] = numpy.nan
        self.market_table.ask[:] = numpy.nan
        self.areas_table = AREAS.new_table(Areas, len(self.ids.areas), len(self.ids.areas))
        self.hired_table = HIRED.new_table(Hired, 0)
        self.trainee_table = TRAINEES.new_table(Trainees, 0, widths=widths)

    def fit_width(self, bands: int) -> None:
        """Room for lists of `bands` bands: the tables' people columns widen (zero beyond a shorter list's length) if a longer
        list than any so far is stored. A state of one band count, as the game keeps, never widens."""
        if bands <= self.bands:
            return
        for name in ("workers_table", "trainee_table"):
            table = getattr(self, name)
            people = numpy.zeros((len(table.people), bands))
            people[:, :self.bands] = table.people
            setattr(self, name, type(table)(*[people if field == "people" else column for field, column in zip(table._fields, table)]))
        self.bands = bands

    def admit(self, areas: Iterable[str], trades: Iterable[str]) -> None:
        """Number the areas and trades not known yet; the tables are laid out again once if any were new."""
        old_areas, old_trades = len(self.ids.areas), len(self.ids.trades)
        area_map = self.ids.areas.admit(areas)
        trade_map = self.ids.trades.admit(trades)
        if area_map is None and trade_map is None:
            return
        area_map = area_map if area_map is not None else numpy.arange(old_areas, dtype=numpy.int64)
        trade_map = trade_map if trade_map is not None else numpy.arange(old_trades, dtype=numpy.int64)
        old_rows = old_areas * old_trades
        new_row = (area_map[numpy.arange(old_rows) // max(old_trades, 1)] * len(self.ids.trades)
                   + trade_map[numpy.arange(old_rows) % max(old_trades, 1)]) if old_rows else numpy.zeros(0, dtype=numpy.int64)
        old = (self.workers_table, self.market_table, self.areas_table, self.trainee_table)
        self._allocate_keeping(old, area_map, new_row)

    def _allocate_keeping(self, old, area_map: numpy.ndarray, new_row: numpy.ndarray) -> None:
        workers, markets, areas, trainees = old
        hired, bands = self.hired_table, self.bands
        self._allocate()
        for column in WORKERS.columns:
            getattr(self.workers_table, column.name)[new_row] = getattr(workers, column.name)[:len(new_row)]
        for column in MARKETS.columns:
            getattr(self.market_table, column.name)[new_row] = getattr(markets, column.name)[:len(new_row)]
        for column in AREAS.columns:
            getattr(self.areas_table, column.name)[area_map] = getattr(areas, column.name)[:len(area_map)]
        self.hired_table = hired
        count = int(trainees.row_count[0])
        self.trainee_table = _spliced(trainees, TRAINEES, 0, count, {"market": new_row[trainees.market[:count]], "years_left": trainees.years_left[:count],
                                      "bonus": trainees.bonus[:count], "length": trainees.length[:count], "people": trainees.people[:count]}, {"people": bands}) if count else self.trainee_table
        self._reindex()

    def _reindex(self) -> None:
        """First rows of the hired and trainee groups, from their counts (groups lie in grid order)."""
        markets = self.market_table
        markets.hired_first[:] = numpy.cumsum(markets.hired_count) - markets.hired_count
        markets.cohort_first[:] = numpy.cumsum(markets.cohort_count) - markets.cohort_count

    def next_order(self) -> int:
        """The next sequence number: dict views list areas and pairs in the order they got their entries."""
        self._order += 1
        return self._order

    def named_areas(self, field: str) -> List[int]:
        """The areas the field's view names, in the order they were named."""
        named = numpy.flatnonzero(getattr(self.areas_table, field + "_named"))
        return named[numpy.argsort(getattr(self.areas_table, field + "_order")[named], kind="stable")].tolist()

    def area_is_named(self, field: str, area: int) -> bool:
        return bool(getattr(self.areas_table, field + "_named")[area])

    def name_area(self, field: str, area: int, named: bool = True) -> None:
        """Give the field's view an entry for the area (empty if nothing is in it), or take it away."""
        flags = getattr(self.areas_table, field + "_named")
        if named and not flags[area]:
            getattr(self.areas_table, field + "_order")[area] = self.next_order()
        flags[area] = named

    def stamp_pairs(self, order_column: numpy.ndarray, rows: numpy.ndarray) -> None:
        """Give the grid rows, in the order given, the next sequence numbers in the order column (they become present now)."""
        order_column[rows] = self._order + 1 + numpy.arange(len(rows))
        self._order += len(rows)

    def stamp_areas(self, field: str, areas: numpy.ndarray) -> None:
        """Name the areas (given by grid row // trade count, in the order the pairs were written) in the field's view, new ones only."""
        areas = areas[~getattr(self.areas_table, field + "_named")[areas]]
        if len(areas):
            _unique, first = numpy.unique(areas, return_index=True)
            for area in areas[numpy.sort(first)].tolist():
                self.name_area(field, area)

    def replace_hired(self, counts: numpy.ndarray, employers: numpy.ndarray, hours: numpy.ndarray) -> None:
        """Set every market's hired rows at once: `counts` per grid row, the rows end to end in grid order."""
        self.hired_table = type(self.hired_table)(numpy.array([len(employers)], dtype=numpy.int64), numpy.array([len(employers)], dtype=numpy.int64),
                                                  employers, hours)
        self.market_table.hired_count[:] = counts
        self._reindex()

    # -- hired hours and cohorts: the groups of rows that grow ----------------------------------------------------

    def cohort_range(self, market: int) -> Tuple[int, int]:
        return int(self.market_table.cohort_first[market]), int(self.market_table.cohort_count[market])

    def _splice_cohorts(self, market: int, start: int, stop: int, cohorts: Sequence[tuple]) -> None:
        table = self.trainee_table
        if cohorts:
            self.fit_width(max(len(each[1]) for each in cohorts))
            table = self.trainee_table
        replacement = {"market": numpy.full(len(cohorts), market, dtype=numpy.int64), "years_left": [each[0] for each in cohorts],
                       "bonus": [each[2] for each in cohorts], "length": [len(each[1]) for each in cohorts],
                       "people": [list(each[1]) + [0.0] * (self.bands - len(each[1])) for each in cohorts]}
        self.trainee_table = _spliced(table, TRAINEES, start, stop, replacement, {"people": self.bands})
        counts = self.market_table.cohort_count
        if cohorts and not counts[market]:
            self.market_table.cohort_order[market] = self.next_order()
        counts[market] += len(cohorts) - (stop - start)
        self._reindex()

    def insert_cohort(self, market: int, index: int, years_left: float, bands: Sequence[float], bonus: float) -> None:
        first, _count = self.cohort_range(market)
        self._splice_cohorts(market, first + index, first + index, [(years_left, bands, bonus)])

    def remove_cohort(self, row: int) -> None:
        self._splice_cohorts(int(self.trainee_table.market[row]), row, row + 1, [])

    def set_cohorts(self, market: int, cohorts: Sequence[tuple]) -> None:
        first, count = self.cohort_range(market)
        self._splice_cohorts(market, first, first + count, [(each[0], list(each[1]), each[2]) for each in cohorts])

    def _splice_hired(self, market: int, start: int, stop: int, employers: Sequence[str], hours: Sequence[float]) -> None:
        numbers = self.ids.employers.admit(employers)
        self.hired_table = _spliced(self.hired_table, HIRED, start, stop, {"employer": numbers, "hours": hours}, {})
        self.market_table.hired_count[market] += len(numbers) - (stop - start)
        self._reindex()

    def keep_cohorts(self, keep: numpy.ndarray) -> None:
        """Keep the cohort rows marked in `keep` (one flag per row in use). An area left with no cohort loses its trainees entry."""
        rows = int(self.trainee_table.row_count[0])
        kept = numpy.flatnonzero(keep[:rows])
        table = self.trainee_table
        new = [numpy.array([len(kept)], dtype=numpy.int64), numpy.array([len(kept)], dtype=numpy.int64)] + [column[kept] for column in table[2:]]
        self.trainee_table = type(table)(*new)
        counts = numpy.bincount(table.market[kept], minlength=len(self.market_table.cohort_count))
        self.market_table.cohort_count[:] = counts
        trades = len(self.ids.trades)
        if trades:
            self.areas_table.trainees_named[:] = self.areas_table.trainees_named & counts.reshape(-1, trades).any(axis=1)
        self._reindex()

    def merge_cohorts(self, pending) -> None:
        """Put the pending table's cohorts into the state's table, after the cohorts their market already had."""
        added = int(pending.row_count[0])
        table = self.trainee_table
        rows = int(table.row_count[0])
        market = numpy.concatenate((table.market[:rows], pending.market[:added]))
        order = numpy.argsort(market, kind="stable")
        lengths = numpy.concatenate((table.length[:rows], numpy.full(added, self.bands, dtype=numpy.int64)))
        columns = [numpy.concatenate((getattr(table, name)[:rows], getattr(pending, name)[:added]))[order]
                   for name in ("market", "years_left", "bonus")] + [lengths[order], numpy.concatenate((table.people[:rows], pending.people[:added]))[order]]
        total = rows + added
        self.trainee_table = type(table)(numpy.array([total], dtype=numpy.int64), numpy.array([total], dtype=numpy.int64), *columns)
        self.market_table.cohort_count[:] = numpy.bincount(market, minlength=len(self.market_table.cohort_count))
        self._reindex()

    def set_hired(self, market: int, hired: Dict[str, float]) -> None:
        first, count = int(self.market_table.hired_first[market]), int(self.market_table.hired_count[market])
        self._splice_hired(market, first, first + count, list(hired), list(hired.values()))
        if not self.market_table.hired_present[market]:
            self.market_table.hired_present[market], self.market_table.hired_order[market] = True, self.next_order()
        self.name_area("hired", market // len(self.ids.trades))

    def append_hired(self, market: int, employer: str, hours: float) -> None:
        end = int(self.market_table.hired_first[market] + self.market_table.hired_count[market])
        self._splice_hired(market, end, end, [employer], [hours])

    def remove_hired(self, market: int, row: int) -> None:
        self._splice_hired(market, row, row + 1, [], [])

    # -- people ------------------------------------------------------------------------------------------------------

    def grid_row(self, area: str, trade: str) -> Optional[int]:
        """The grid row of the pair, or None where the state numbers no such area or trade."""
        area_number, trade_number = self.ids.areas.find(area), self.ids.trades.find(trade)
        if area_number is None or trade_number is None:
            return None
        return area_number * len(self.ids.trades) + trade_number

    def area_people(self, area: str, include_trainees: bool = True) -> float:
        """Everyone counted in one area, working or learning: the trades in the order the workers view lists them, each band
        list summed by `sum` (the order of a float sum is part of the answer)."""
        number = self.ids.areas.find(area)
        if number is None:
            return 0.0
        trades = len(self.ids.trades)
        total = 0.0
        if self.area_is_named("workers", number):
            for trade in TradeMap(self, WorkersField, area)._present_trades():
                total += sum(self.workers_table.people[number * trades + trade].tolist())
        if include_trainees and self.area_is_named("trainees", number):
            for trade in TradeMap(self, TraineesField, area)._present_trades():
                first, count = self.cohort_range(number * trades + trade)
                for row in range(first, first + count):
                    total += sum(self.trainee_table.people[row].tolist())
        return total

    def rename_employer(self, old: str, new: str) -> None:
        """An employer becomes another id (`sim.rekey`): in the hired hours, `old` as a whole name or a part of a composite id is `new`;
        two employers that become one in a market add their hours."""
        for area, trades in list(self.hired_hours.items()):
            for trade, hired in list(trades.items()):
                renamed = {}
                for employer, hours in hired.items():
                    name = rename_text(employer, old, new)
                    renamed[name] = renamed[name] + hours if name in renamed else hours
                if list(renamed) != list(hired):
                    trades[trade] = renamed

    # -- plain data, copies, equality ----------------------------------------------------------------------------------

    def to_plain(self) -> dict:
        """Nested dicts and lists of numbers and strings: what a save holds."""
        return {name: {area: {trade: _plain_value(value) for trade, value in by_trade.items()}
                       for area, by_trade in AreaMap(self, field).items()} for name, field in _FIELDS}

    def copy(self) -> "MarketState":
        """An independent copy (tables and numbering)."""
        other = MarketState.__new__(MarketState)
        other.ids = self.ids.copy()
        other.bands, other._order = self.bands, self._order
        for name in ("workers_table", "market_table", "areas_table", "hired_table", "trainee_table"):
            table = getattr(self, name)
            setattr(other, name, type(table)(*[column.copy() for column in table]))
        return other

    __deepcopy__ = lambda self, memo: self.copy()

    def __eq__(self, other) -> bool:
        return isinstance(other, MarketState) and self.to_plain() == other.to_plain()

    __hash__ = None

    def __repr__(self) -> str:
        return "MarketState(%r)" % (self.to_plain(),)
