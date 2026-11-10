"""The values inside the labour core's nested-dict views: a pair's band list, a cohort, a market's cohorts and its employers' hours
(state_fields.py has the views of areas and trades that hand them out).

Each is a live view over the state's tables that names its pair (`Where`), so it stays right if the state is laid out again for a new
area or trade. Reading builds nothing that is kept, and writing (`bands[:] = ...`, `hours[employer] = ...`) writes the table."""
from collections.abc import MutableMapping, MutableSequence
from typing import Iterator, List

import numpy


class Where:
    """A pair named by its area and trade, looked up in the state at every use, so a view stays right when the state is laid out
    again for a new area or trade."""
    __slots__ = ("state", "area", "trade")

    def __init__(self, state, area: str, trade: str):
        self.state, self.area, self.trade = state, area, trade

    def row(self) -> int:
        return self.state.grid_row(self.area, self.trade)


class Bands(MutableSequence):
    """People per ability band of a pair's workers, or of one of its cohorts (`cohort` is its place among them), read and written
    in place. The list is as long as the one stored (`length`); the table's columns may be wider."""

    def __init__(self, where: Where, cohort=None):
        self._where, self._cohort = where, cohort

    def _target(self):
        state = self._where.state
        row = self._where.row()
        if self._cohort is None:
            return state.workers_table.people, state.workers_table.length, row
        cohort_row = state.cohort_range(row)[0] + self._cohort
        return state.trainee_table.people, state.trainee_table.length, cohort_row

    def __len__(self) -> int:
        _column, lengths, row = self._target()
        return int(lengths[row])

    def _values(self):
        column, lengths, row = self._target()
        return column[row, :lengths[row]]

    def __getitem__(self, index):
        values = self._values()
        if isinstance(index, slice):
            return values[index].tolist()
        return float(values[index])

    def __setitem__(self, index, value) -> None:
        values = self._values()
        if isinstance(index, slice):
            replacement = list(value)
            if len(values[index]) != len(replacement):
                raise ValueError("a band list keeps its %d bands" % len(self))
            values[index] = replacement
        else:
            values[index] = value

    def __delitem__(self, index) -> None:
        raise TypeError("bands cannot lose a band")

    def insert(self, index, value) -> None:
        raise TypeError("bands cannot gain a band")

    def __iter__(self):
        return iter(self._values().tolist())

    def __eq__(self, other) -> bool:
        return list(self) == list(other) if isinstance(other, (list, tuple, Bands)) else NotImplemented

    __hash__ = None

    def __repr__(self) -> str:
        return repr(list(self))


class Cohort(MutableSequence):
    """One cohort of a pair as the list [years_left, people per band, bonus]."""

    def __init__(self, where: Where, index: int):
        self._where, self._index = where, index

    def _row(self) -> int:
        return self._where.state.cohort_range(self._where.row())[0] + self._index

    def __len__(self) -> int:
        return 3

    def __getitem__(self, index):
        table = self._where.state.trainee_table
        if isinstance(index, slice):
            return [self[position] for position in range(*index.indices(3))]
        if index in (0, -3):
            return float(table.years_left[self._row()])
        if index in (1, -2):
            return Bands(self._where, self._index)
        if index in (2, -1):
            return float(table.bonus[self._row()])
        raise IndexError(index)

    def __setitem__(self, index, value) -> None:
        table = self._where.state.trainee_table
        if index in (0, -3):
            table.years_left[self._row()] = value
        elif index in (1, -2):
            Bands(self._where, self._index)[:] = value
        elif index in (2, -1):
            table.bonus[self._row()] = value
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

    def __init__(self, where: Where):
        self._where = where

    def __len__(self) -> int:
        return self._where.state.cohort_range(self._where.row())[1]

    def __getitem__(self, index):
        positions = range(len(self))
        if isinstance(index, slice):
            return [Cohort(self._where, position) for position in positions[index]]
        return Cohort(self._where, positions[index])

    def __setitem__(self, index, value) -> None:
        if isinstance(index, slice):
            raise TypeError("replace cohorts one at a time")
        cohort = Cohort(self._where, range(len(self))[index])
        for position in range(3):
            cohort[position] = value[position]

    def __delitem__(self, index) -> None:
        if isinstance(index, slice):
            raise TypeError("delete cohorts one at a time")
        state = self._where.state
        state.remove_cohort(state.cohort_range(self._where.row())[0] + range(len(self))[index])

    def insert(self, index, value) -> None:
        count = len(self)
        index = min(max(index + count if index < 0 else index, 0), count)
        self._where.state.insert_cohort(self._where.row(), index, value[0], value[1], value[2] if len(value) > 2 else 0.0)

    def __eq__(self, other) -> bool:
        return [each.plain() for each in self] == [list(each) if not isinstance(each, Cohort) else each.plain() for each in other] if isinstance(other, (list, tuple, CohortList)) else NotImplemented

    __hash__ = None

    def __repr__(self) -> str:
        return repr([each.plain() for each in self])


class EmployerHours(MutableMapping):
    """The employers' hours in one (area, trade) market: HIRED rows, in the order they were written."""

    def __init__(self, where: Where):
        self._where = where

    def _rows(self) -> range:
        markets = self._where.state.market_table
        row = self._where.row()
        first = int(markets.hired_first[row])
        return range(first, first + int(markets.hired_count[row]))

    def _names(self) -> List[str]:
        state = self._where.state
        rows = self._rows()
        return [state.ids.employers.name(number) for number in state.hired_table.employer[rows.start:rows.stop].tolist()]

    def _row_of(self, name: str):
        state = self._where.state
        number = state.ids.employers.table.find(name)
        if number is not None:
            rows = self._rows()
            found = numpy.flatnonzero(state.hired_table.employer[rows.start:rows.stop] == number)
            if len(found):
                return rows.start + int(found[0])
        return None

    def __len__(self) -> int:
        return len(self._rows())

    def __iter__(self) -> Iterator[str]:
        return iter(self._names())

    def __getitem__(self, name: str) -> float:
        row = self._row_of(name)
        if row is None:
            raise KeyError(name)
        return float(self._where.state.hired_table.hours[row])

    def __setitem__(self, name: str, hours: float) -> None:
        row = self._row_of(name)
        if row is not None:
            self._where.state.hired_table.hours[row] = hours
        else:
            self._where.state.append_hired(self._where.row(), name, hours)

    def __delitem__(self, name: str) -> None:
        row = self._row_of(name)
        if row is None:
            raise KeyError(name)
        self._where.state.remove_hired(self._where.row(), row)

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
