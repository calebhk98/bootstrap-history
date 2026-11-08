"""The labour core's state read and written as nested dicts, for callers not yet on the tables.

`state.workers[area][trade]` is a list of people per ability band, `state.trainees[area][trade]` a list of
[years_left, people per band, bonus], `state.wages[area][trade]` and `state.asks[area][trade]` floats and
`state.hired_hours[area][trade]` a dict employer -> hours. `AreaMap` is the view of one field over all its areas and `TradeMap` of one
area's trades; a `Field` says what a pair holds in each (which table, how it is read, written and removed). Areas and trades are
listed in the order they were given their entries. A view is for callers outside the compiled year; code inside it reads the tables.
"""
from collections.abc import Mapping, MutableMapping
from typing import Iterator, List

import numpy

from .state_views import Bands, Cohort, CohortList, EmployerHours, Where


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
    def read(state, where: Where):
        return Bands(where)

    @staticmethod
    def write(state, row: int, value) -> None:
        values = [float(each) for each in value]
        state.fit_width(len(values))
        table = state.workers_table
        if not table.present[row]:
            table.present[row], table.order[row] = True, state.next_order()
        table.people[row] = 0.0
        table.people[row, :len(values)] = values
        table.length[row] = len(values)

    @staticmethod
    def erase(state, row: int) -> None:
        state.workers_table.present[row] = False
        state.workers_table.people[row] = 0.0
        state.workers_table.length[row] = 0


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
    def read(cls, state, where: Where) -> float:
        return float(getattr(state.market_table, cls.column)[where.row()])

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
    def read(state, where: Where):
        return EmployerHours(where)

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
    def read(state, where: Where):
        return CohortList(where)

    @staticmethod
    def write(state, row: int, value) -> None:
        state.set_cohorts(row, [(each[0], each[1], each[2] if len(each) > 2 else 0.0) for each in value])

    @staticmethod
    def erase(state, row: int) -> None:
        state.set_cohorts(row, [])


class TradeMap(MutableMapping):
    """`view[area]`: trade -> the field's value for one area (named, so the view survives the state being laid out again)."""

    def __init__(self, state, field, area: str):
        self._state, self._field, self._area = state, field, area

    def _area_number(self) -> int:
        return self._state.ids.areas.number(self._area)

    def _present_trades(self) -> List[int]:
        trades = len(self._state.ids.trades)
        number = self._state.ids.areas.find(self._area)
        if not trades or number is None:
            return []
        rows = slice(number * trades, (number + 1) * trades)
        present = numpy.flatnonzero(self._field.present(self._state, rows))
        return present[numpy.argsort(self._field.order(self._state, rows)[present], kind="stable")].tolist()

    def __len__(self) -> int:
        return len(self._present_trades())

    def __iter__(self) -> Iterator[str]:
        names = self._state.ids.trades.names
        return iter([names[trade] for trade in self._present_trades()])

    def _row(self, trade: str, create: bool):
        """The grid row of the pair; None where the trade is unknown and `create` is off (a new trade is numbered when it is on)."""
        if self._state.ids.trades.find(trade) is None:
            if not create:
                return None
            self._state.admit((), (trade,))
        return self._state.grid_row(self._area, trade)

    def __contains__(self, trade) -> bool:
        row = self._row(trade, False) if isinstance(trade, str) else None
        return row is not None and bool(self._field.present(self._state, row))

    def __getitem__(self, trade: str):
        row = self._row(trade, False)
        if row is None or not self._field.present(self._state, row):
            raise KeyError(trade)
        return self._field.read(self._state, Where(self._state, self._area, trade))

    def __setitem__(self, trade: str, value) -> None:
        self._row(trade, True)
        self._field.write(self._state, self._state.grid_row(self._area, trade), value)
        self._state.name_area(self._field.name, self._area_number())

    def __delitem__(self, trade: str) -> None:
        if trade not in self:
            raise KeyError(trade)
        self._field.erase(self._state, self._row(trade, False))

    def setdefault(self, trade, default=None):
        if trade not in self:
            self[trade] = default if default is not None else {} if self._field.name == "hired" else []
        return self._field.read(self._state, Where(self._state, self._area, trade))

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
        return TradeMap(self._state, self._field, area)

    def __setitem__(self, area: str, by_trade) -> None:
        by_trade = dict(by_trade.items()) if isinstance(by_trade, Mapping) else dict(by_trade)
        self._state.admit((area,), by_trade)
        trades = TradeMap(self._state, self._field, area)
        for trade in list(trades):
            if trade not in by_trade:
                del trades[trade]
        self._state.name_area(self._field.name, self._state.ids.areas.number(area))
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
        return TradeMap(self._state, self._field, area)

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
