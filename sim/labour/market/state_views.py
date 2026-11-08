"""The labour core's state read and written as nested dicts, for callers not yet on the tables.

`state.workers[area][trade]` is a list of people per ability band, `state.trainees[area][trade]` a list of
[years_left, people per band, bonus], `state.wages[area][trade]` and `state.asks[area][trade]` floats and
`state.hired_hours[area][trade]` a dict employer -> hours. Each is a live view over the state's tables: reading builds nothing
that is kept, and writing (`bands[:] = ...`, `view[area][trade] = ...`, `setdefault`) writes the table. Names iterate in sorted
order. A view is for callers outside the compiled year; code inside it reads the tables (`MarketState.tables`).
"""
from collections.abc import Mapping, MutableMapping, MutableSequence
from typing import Iterator, List

import numpy


class Bands(MutableSequence):
    """People per ability band of one row of a table column (`column[row]`), read and written in place."""

    def __init__(self, column, row: int):
        self._column, self._row = column, row

    def __len__(self) -> int:
        return self._column.shape[1]

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self._column[self._row, index].tolist()
        return float(self._column[self._row, index])

    def __setitem__(self, index, value) -> None:
        if isinstance(index, slice):
            values = list(value)
            if len(self._column[self._row, index]) != len(values):
                raise ValueError("a band list keeps its %d bands" % len(self))
            self._column[self._row, index] = values
        else:
            self._column[self._row, index] = value

    def __delitem__(self, index) -> None:
        raise TypeError("bands cannot lose a band")

    def insert(self, index, value) -> None:
        raise TypeError("bands cannot gain a band")

    def __iter__(self):
        return iter(self._column[self._row].tolist())

    def __eq__(self, other) -> bool:
        return list(self) == list(other) if isinstance(other, (list, tuple, Bands)) else NotImplemented

    __hash__ = None

    def __repr__(self) -> str:
        return repr(list(self))


class Cohort(MutableSequence):
    """One row of the trainees table as the list [years_left, people per band, bonus]."""

    def __init__(self, state, row: int):
        self._state, self._row = state, row

    def __len__(self) -> int:
        return 3

    def __getitem__(self, index):
        table = self._state.trainee_table
        if isinstance(index, slice):
            return [self[position] for position in range(*index.indices(3))]
        if index in (0, -3):
            return float(table.years_left[self._row])
        if index in (1, -2):
            return Bands(table.people, self._row)
        if index in (2, -1):
            return float(table.bonus[self._row])
        raise IndexError(index)

    def __setitem__(self, index, value) -> None:
        table = self._state.trainee_table
        if index in (0, -3):
            table.years_left[self._row] = value
        elif index in (1, -2):
            Bands(table.people, self._row)[:] = value
        elif index in (2, -1):
            table.bonus[self._row] = value
        else:
            raise IndexError(index)

    def __delitem__(self, index) -> None:
        raise TypeError("a cohort keeps its three entries")

    def insert(self, index, value) -> None:
        raise TypeError("a cohort keeps its three entries")

    def plain(self) -> list:
        return [self[0], list(self[1]), self[2]]

    def __eq__(self, other) -> bool:
        return self.plain() == (other.plain() if isinstance(other, Cohort) else list(other)) if isinstance(other, (list, tuple, Cohort)) else NotImplemented

    __hash__ = None

    def __repr__(self) -> str:
        return repr(self.plain())


class CohortList(MutableSequence):
    """The cohorts of one (area, trade) market, in the order they enrolled."""

    def __init__(self, state, market: int):
        self._state, self._market = state, market

    def _rows(self) -> range:
        first, count = self._state.cohort_range(self._market)
        return range(first, first + count)

    def __len__(self) -> int:
        return len(self._rows())

    def __getitem__(self, index):
        rows = self._rows()
        if isinstance(index, slice):
            return [Cohort(self._state, row) for row in rows[index]]
        return Cohort(self._state, rows[index])

    def __setitem__(self, index, value) -> None:
        if isinstance(index, slice):
            raise TypeError("replace cohorts one at a time")
        cohort = Cohort(self._state, self._rows()[index])
        for position in range(3):
            cohort[position] = value[position]

    def __delitem__(self, index) -> None:
        if isinstance(index, slice):
            raise TypeError("delete cohorts one at a time")
        self._state.remove_cohort(self._rows()[index])

    def insert(self, index, value) -> None:
        count = len(self)
        index = min(max(index + count if index < 0 else index, 0), count)
        self._state.insert_cohort(self._market, index, value[0], value[1], value[2])

    def __eq__(self, other) -> bool:
        return [each.plain() for each in self] == [list(each) if not isinstance(each, Cohort) else each.plain() for each in other] if isinstance(other, (list, tuple, CohortList)) else NotImplemented

    __hash__ = None

    def __repr__(self) -> str:
        return repr([each.plain() for each in self])


class EmployerHours(MutableMapping):
    """The employers' hours in one (area, trade) market: HIRED rows, in the order they were written."""

    def __init__(self, state, market: int):
        self._state, self._market = state, market

    def _rows(self) -> range:
        markets = self._state.market_table
        first = int(markets.hired_first[self._market])
        return range(first, first + int(markets.hired_count[self._market]))

    def _names(self) -> List[str]:
        employers = self._state.ids.employers
        return [employers.name(number) for number in self._state.hired_table.employer[self._rows().start:self._rows().stop].tolist()]

    def _row_of(self, name: str):
        number = self._state.ids.employers.table.find(name)
        if number is not None:
            found = numpy.flatnonzero(self._state.hired_table.employer[self._rows().start:self._rows().stop] == number)
            if len(found):
                return self._rows().start + int(found[0])
        return None

    def __len__(self) -> int:
        return len(self._rows())

    def __iter__(self) -> Iterator[str]:
        return iter(self._names())

    def __getitem__(self, name: str) -> float:
        row = self._row_of(name)
        if row is None:
            raise KeyError(name)
        return float(self._state.hired_table.hours[row])

    def __setitem__(self, name: str, hours: float) -> None:
        row = self._row_of(name)
        if row is not None:
            self._state.hired_table.hours[row] = hours
        else:
            self._state.append_hired(self._market, name, hours)

    def __delitem__(self, name: str) -> None:
        row = self._row_of(name)
        if row is None:
            raise KeyError(name)
        self._state.remove_hired(self._market, row)

    def pop(self, name, *default):
        found = self.get(name, None) if default else self[name]
        if name in self:
            del self[name]
            return found
        return default[0]

    def setdefault(self, name, default=None):
        if name not in self:
            self[name] = default
        return self[name]

    def __repr__(self) -> str:
        return repr(dict(self))


class WorkersField:
    """Strategy for the `workers` view: what a pair holds and how it is read, written and removed."""
    name = "workers"

    @staticmethod
    def present(state, rows):
        return state.workers_table.present[rows]

    @staticmethod
    def order(state, rows):
        return state.workers_table.order[rows]

    @staticmethod
    def read(state, row: int):
        return Bands(state.workers_table.people, row)

    @staticmethod
    def write(state, row: int, value) -> None:
        values = [float(each) for each in value]
        state.fit_width(len(values))
        table = state.workers_table
        if not table.present[row]:
            table.present[row], table.order[row] = True, state.next_order()
        table.people[row] = values

    @staticmethod
    def erase(state, row: int) -> None:
        state.workers_table.present[row] = False
        state.workers_table.people[row] = 0.0


class _ScalarField:
    """A float per pair that is absent while NaN (wages and asks)."""
    column = ""

    @classmethod
    def present(cls, state, rows):
        return ~numpy.isnan(getattr(state.market_table, cls.column)[rows])

    @classmethod
    def order(cls, state, rows):
        return getattr(state.market_table, cls.name_of_order)[rows]

    @classmethod
    def read(cls, state, row: int) -> float:
        return float(getattr(state.market_table, cls.column)[row])

    @classmethod
    def write(cls, state, row: int, value) -> None:
        values = getattr(state.market_table, cls.column)
        if numpy.isnan(values[row]):
            getattr(state.market_table, cls.name_of_order)[row] = state.next_order()
        values[row] = value

    @classmethod
    def erase(cls, state, row: int) -> None:
        getattr(state.market_table, cls.column)[row] = numpy.nan


class WagesField(_ScalarField):
    name, column, name_of_order = "wages", "wage", "wage_order"


class AsksField(_ScalarField):
    name, column, name_of_order = "asks", "ask", "ask_order"


class HiredField:
    name = "hired"

    @staticmethod
    def present(state, rows):
        return state.market_table.hired_present[rows]

    @staticmethod
    def order(state, rows):
        return state.market_table.hired_order[rows]

    @staticmethod
    def read(state, row: int):
        return EmployerHours(state, row)

    @staticmethod
    def write(state, row: int, value) -> None:
        state.set_hired(row, dict(value))

    @staticmethod
    def erase(state, row: int) -> None:
        state.set_hired(row, {})
        state.market_table.hired_present[row] = False


class TraineesField:
    name = "trainees"
    derived_presence = True       # a pair is named by holding a cohort, so it cannot be named empty

    @staticmethod
    def present(state, rows):
        return state.market_table.cohort_count[rows] > 0

    @staticmethod
    def order(state, rows):
        return state.market_table.cohort_order[rows]

    @staticmethod
    def read(state, row: int):
        return CohortList(state, row)

    @staticmethod
    def write(state, row: int, value) -> None:
        state.set_cohorts(row, [(each[0], each[1], each[2]) for each in value])

    @staticmethod
    def erase(state, row: int) -> None:
        state.set_cohorts(row, [])


class TradeMap(MutableMapping):
    """`view[area]`: trade -> the field's value for one area."""

    def __init__(self, state, field, area: int):
        self._state, self._field, self._area = state, field, area

    def _present_trades(self) -> List[int]:
        trades = len(self._state.ids.trades)
        if not trades:
            return []
        rows = slice(self._area * trades, (self._area + 1) * trades)
        present = numpy.flatnonzero(self._field.present(self._state, rows))
        return present[numpy.argsort(self._field.order(self._state, rows)[present], kind="stable")].tolist()

    def __len__(self) -> int:
        return len(self._present_trades())

    def __iter__(self) -> Iterator[str]:
        names = self._state.ids.trades.names
        return iter([names[trade] for trade in self._present_trades()])

    def _row(self, trade: str, create: bool):
        number = self._state.ids.trades.find(trade)
        if number is None:
            if not create:
                return None
            self._state.admit((), (trade,))
            number = self._state.ids.trades.number(trade)
        return self._area * len(self._state.ids.trades) + number

    def __contains__(self, trade) -> bool:
        row = self._row(trade, False) if isinstance(trade, str) else None
        return row is not None and bool(self._field.present(self._state, row))

    def __getitem__(self, trade: str):
        row = self._row(trade, False)
        if row is None or not self._field.present(self._state, row):
            raise KeyError(trade)
        return self._field.read(self._state, row)

    def __setitem__(self, trade: str, value) -> None:
        row = self._row(trade, True)
        self._field.write(self._state, row, value)
        self._state.name_area(self._field.name, self._area)

    def __delitem__(self, trade: str) -> None:
        if trade not in self:
            raise KeyError(trade)
        self._field.erase(self._state, self._row(trade, False))

    def setdefault(self, trade, default=None):
        if trade not in self:
            self[trade] = default if default is not None else {} if self._field.name == "hired" else []
        return self._field.read(self._state, self._row(trade, False))

    def pop(self, trade, *default):
        if trade in self:
            plain = _plain_of(self[trade])
            del self[trade]
            return plain
        if default:
            return default[0]
        raise KeyError(trade)

    def __repr__(self) -> str:
        return repr(dict(self))


def _plain_of(value):
    if isinstance(value, float):
        return value
    if isinstance(value, EmployerHours):
        return dict(value)
    return [each.plain() if isinstance(each, Cohort) else each for each in value]


class AreaMap(MutableMapping):
    """`state.workers` and its kin: area -> `TradeMap`."""

    def __init__(self, state, field):
        self._state, self._field = state, field

    def _named_areas(self) -> List[int]:
        return self._state.named_areas(self._field.name)

    def __len__(self) -> int:
        return len(self._named_areas())

    def __iter__(self) -> Iterator[str]:
        names = self._state.ids.areas.names
        return iter([names[area] for area in self._named_areas()])

    def __contains__(self, area) -> bool:
        number = self._state.ids.areas.find(area) if isinstance(area, str) else None
        return number is not None and self._state.area_is_named(self._field.name, number)

    def __getitem__(self, area: str) -> TradeMap:
        if area not in self:
            raise KeyError(area)
        return TradeMap(self._state, self._field, self._state.ids.areas.number(area))

    def __setitem__(self, area: str, by_trade) -> None:
        by_trade = dict(by_trade.items()) if isinstance(by_trade, Mapping) else dict(by_trade)
        self._state.admit((area,), by_trade)
        number = self._state.ids.areas.number(area)
        trades = TradeMap(self._state, self._field, number)
        for trade in list(trades):
            if trade not in by_trade:
                del trades[trade]
        self._state.name_area(self._field.name, number)
        for trade, value in by_trade.items():
            trades[trade] = value

    def __delitem__(self, area: str) -> None:
        if area not in self:
            raise KeyError(area)
        trades = self[area]
        for trade in list(trades):
            del trades[trade]
        self._state.name_area(self._field.name, self._state.ids.areas.number(area), False)

    def setdefault(self, area, default=None):
        if area not in self:
            self[area] = default if default is not None else {}
        return TradeMap(self._state, self._field, self._state.ids.areas.number(area))

    def pop(self, area, *default):
        if area in self:
            plain = {trade: _plain_of(value) for trade, value in self[area].items()}
            del self[area]
            return plain
        if default:
            return default[0]
        raise KeyError(area)

    def clear(self) -> None:
        for area in list(self):
            del self[area]

    def __repr__(self) -> str:
        return repr(dict(self))
