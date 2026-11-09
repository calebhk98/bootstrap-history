"""The cohort table: every household cohort as a row of columns (`cohort_rows.py`), and the mapping view over it.

`CohortStore` is what `record.cohorts` is. The year loop reads and writes its columns (`table`, `ids`, `order`, the block writes
below); a `Cohort` is built only when something asks for one through the mapping (`store[cohort_id]`, `.values()`, `.items()`),
which is how the rules written over a cohort object, the screens, the protocol and the tests read it. A `Cohort` handed out is a
snapshot: changing the table changes the next one built, never one already held, and `put` (or `store[id] = cohort`) writes a whole
record into its row.

Rows are in the order the cohorts entered (a mapping's insertion order); `seat_sorted` puts them in id order, which is the order a
load reads them in. `version` rises on every write, so a reader that keeps a derived copy knows when to read again. A float field
written as a numpy float is read back as one (`numpy_typed`): CPython's `sum()` adds exact Python floats with compensation and numpy
floats without, so a changed scalar type moves a total by a last digit."""
import math
from collections.abc import MutableMapping
from typing import Dict, Iterable, Iterator, List, Mapping, NamedTuple, Optional

import numpy as np

from sim.compiled_tables.growth import reserve_rows
from sim.compiled_tables.ids import IdTable

from .cohort_rows import (COHORT_ROWS_SPEC, FLOAT_BIT, OPTIONAL_FLOATS, SCALAR_FLOATS, WIDE_COLUMNS, WIDE_GROUPS, CohortRows)
from .households_cohort import Cohort

_FIRST_CAPACITY = 64
_FIELDS = ("agent_id", "tile", "income_class", "people", "working_people", "ownership_share", "expected_inflation", "cash_target",
           "last_basket_price_level", "last_year_income", "share_wealth", "planned_spending", "expected_spending",
           "expected_floor_cost", "unmet_floor_by_need", "own_plan_by_need", "hired_work_per_person", "milled_grains")
_DICTS = {"unmet": "unmet_floor_by_need", "plan": "own_plan_by_need"}


class CohortFigures(NamedTuple):
    """The few figures most rules read of a cohort, read from the columns in a block (`CohortStore.figures`): `own_plan_by_need` is None
    unless it was asked for."""
    agent_id: str
    tile: str
    people: float
    working_people: float
    last_year_income: float
    hired_work_per_person: float
    milled_grains: tuple
    own_plan_by_need: Optional[Dict[str, float]]


def typed_flags(values) -> np.ndarray:
    """One flag per value: True where it is a numpy float (a list of Python floats, the usual case, is checked in one pass)."""
    if set(map(type, values)) <= {float, type(None)}:
        return np.zeros(len(values), dtype=np.bool_)
    return np.array([isinstance(value, np.floating) for value in values], dtype=np.bool_)


def table_of(cohorts) -> "CohortStore":
    """`cohorts` as the cohort table: the table itself, or a plain mapping of cohorts (a test's) made into one."""
    return cohorts if isinstance(cohorts, CohortStore) else CohortStore(cohorts)


class CohortStore(MutableMapping):
    """The cohorts by id, as columns; a mapping from agent id to `Cohort`."""

    def __init__(self, cohorts: Optional[Mapping[str, Cohort]] = None):
        self.table: CohortRows = COHORT_ROWS_SPEC.new_table(CohortRows, _FIRST_CAPACITY, widths={name: 1 for name in WIDE_COLUMNS})
        self.names: Dict[str, IdTable] = {kind: IdTable(kind) for kind in ("tiles", "needs", "goods")}
        self.ids: List[str] = []                    # by row
        self.row_of: Dict[str, int] = {}
        self.version = 0                            # rises on every write
        self._objects: List[Optional[Cohort]] = []
        self._milled: List[Optional[tuple]] = []    # by row: the grains bought milled as names, until the row's grains are written
        self._order: Optional[np.ndarray] = None
        self._order_members = -1
        self._members = 0                           # rises when a cohort enters or its tile or class is written
        self._tile_rows: Dict[str, np.ndarray] = {}
        self._tile_rows_members = -1
        if cohorts:
            for cohort in cohorts.values():
                self.put(cohort)

    @property
    def count(self) -> int:
        return int(self.table.row_count[0])

    # ---- the mapping -----------------------------------------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.row_of)

    def __contains__(self, cohort_id) -> bool:
        return cohort_id in self.row_of

    def __iter__(self) -> Iterator[str]:
        return iter(self.row_of)

    def __getitem__(self, cohort_id: str) -> Cohort:
        return self.at(self.row_of[cohort_id])

    def __setitem__(self, cohort_id: str, cohort: Cohort) -> None:
        if cohort.agent_id != cohort_id:
            raise ValueError("cohort %r stored under %r" % (cohort.agent_id, cohort_id))
        self.put(cohort)

    def __delitem__(self, cohort_id: str) -> None:
        kept = [self.at(row) for row in range(self.count) if self.ids[row] != cohort_id]
        if len(kept) == self.count:
            raise KeyError(cohort_id)
        self.clear()
        for cohort in kept:
            self.put(cohort)

    def __eq__(self, other) -> bool:
        return isinstance(other, Mapping) and dict(self.items()) == dict(other.items())

    __hash__ = None

    def get(self, cohort_id, default=None):
        row = self.row_of.get(cohort_id)
        return default if row is None else self.at(row)

    def keys(self):
        return self.row_of.keys()

    def values(self):
        objects = self._objects
        for row, kept in enumerate(objects):          # rows are in table order, every one alive
            if kept is None:
                self.at(row)
        return list(objects)

    def items(self):
        self.values()
        return list(zip(self.ids, self._objects))

    def clear(self) -> None:
        version, names = self.version + 1, self.names
        self.__init__()
        self.version, self.names = version, names     # counters and numbers never go back

    def at(self, row: int) -> Cohort:
        """The cohort in `row`, built from the columns and kept until the row is written."""
        kept = self._objects[row]
        if kept is None:
            kept = self._objects[row] = self._build(row)
        return kept

    # ---- writing a record ------------------------------------------------------------------------------------------------

    def put(self, cohort: Cohort) -> int:
        """`cohort` is the table's row for its id, new (a row at the end) or replacing; the row's number."""
        row = self.row_of.get(cohort.agent_id)
        if row is None:
            row = self._claim(cohort.agent_id)
        self._write(row, cohort)
        self._objects[row] = None
        self._members += 1
        self.version += 1
        return row

    def _claim(self, cohort_id: str) -> int:
        self.table = reserve_rows(self.table, 1)
        row = self.count
        self.table.row_count[0] = row + 1
        self.ids.append(cohort_id)
        self._objects.append(None)
        self._milled.append(None)
        self.row_of[cohort_id] = row
        self._members += 1
        return row

    def _name(self, kind: str, name: str) -> int:
        table = self.names[kind]
        found = table.numbers.get(name)
        return table.admit([name])[0] if found is None else found

    def _widen(self, group: str, width: int) -> None:
        """Room for `width` places a row in the wide columns of `group` (they grow together)."""
        wanted = max(width, 1)
        fields = {name: getattr(self.table, name) for name in self.table._fields}
        for name in WIDE_GROUPS[group]:
            old = fields[name]
            if old.shape[1] < wanted:
                grown = np.zeros((old.shape[0], max(wanted, 2 * old.shape[1])), dtype=old.dtype)
                grown[:, :old.shape[1]] = old
                fields[name] = grown
        self.table = CohortRows(**fields)

    def _write(self, row: int, cohort: Cohort) -> None:
        table = self.table
        table.tile[row] = self._name("tiles", cohort.tile)
        table.income_class[row] = cohort.income_class
        for name in SCALAR_FLOATS:
            getattr(table, name)[row] = getattr(cohort, name)
        table.share_wealth[row] = np.nan if cohort.share_wealth is None else cohort.share_wealth
        table.numpy_typed[row] = sum(bit for name, bit in FLOAT_BIT.items() if isinstance(getattr(cohort, name), np.floating))
        self._write_pairs(row, "unmet", cohort.unmet_floor_by_need)
        self._write_pairs(row, "plan", cohort.own_plan_by_need)
        self._write_milled(row, cohort.milled_grains)

    def _write_pairs(self, row: int, group: str, held: Mapping[str, float]) -> None:
        if len(held) > getattr(self.table, WIDE_GROUPS[group][0]).shape[1]:
            self._widen(group, len(held))
        need_column, value_column, typed_column = (getattr(self.table, name) for name in WIDE_GROUPS[group])
        need_column[row, :], value_column[row, :], typed_column[row, :] = 0, 0.0, 0
        for place, (name, value) in enumerate(held.items()):
            need_column[row, place] = self._name("needs", name)
            value_column[row, place] = value
            typed_column[row, place] = isinstance(value, np.floating)
        getattr(self.table, group + "_count")[row] = len(held)

    def _write_milled(self, row: int, grains) -> None:
        if len(grains) > self.table.milled_good.shape[1]:
            self._widen("milled", len(grains))
        self.table.milled_good[row, :] = 0
        for place, name in enumerate(grains):
            self.table.milled_good[row, place] = self._name("goods", name)
        self.table.milled_count[row] = len(grains)
        self._milled[row] = tuple(grains)

    def set_fields(self, cohort_id: str, **changes) -> None:
        """The fields named of one cohort take the values (the scalar fields, the two mappings, `milled_grains`, `tile`, `income_class`)."""
        row = self.row_of[cohort_id]
        for name, value in changes.items():
            if name == "unmet_floor_by_need":
                self._write_pairs(row, "unmet", value)
            elif name == "own_plan_by_need":
                self._write_pairs(row, "plan", value)
            elif name == "milled_grains":
                self._write_milled(row, value)
            elif name == "tile":
                self.table.tile[row] = self._name("tiles", value)
                self._members += 1
            elif name == "income_class":
                self.table.income_class[row] = value
                self._members += 1
            else:
                self._scalar(name)[row] = np.nan if value is None else value
                bit = FLOAT_BIT[name]
                self.table.numpy_typed[row] = (int(self.table.numpy_typed[row]) & ~bit) | (bit if isinstance(value, np.floating) else 0)
        self._objects[row] = None
        self.version += 1

    def set_rows(self, name: str, rows: np.ndarray, values, typed=False) -> None:
        """One float field of the rows takes the values. `typed` (a flag, or one per row) says the values are numpy floats, which a
        `Cohort` built from the rows hands back as such; a field written without it reads back as a Python float."""
        self._scalar(name)[rows] = values
        bit = FLOAT_BIT[name]
        self.table.numpy_typed[rows] = (self.table.numpy_typed[rows] & ~bit) | np.where(typed, bit, 0)
        self.written(rows)

    def set_column(self, name: str, cohort_ids: Iterable[str], values: Iterable[float]) -> None:
        """One float field of the cohorts named takes the values (an id the table does not hold is skipped); a numpy value stays one."""
        pairs = [(self.row_of[each], value) for each, value in zip(cohort_ids, values) if each in self.row_of]
        if pairs:
            self.set_rows(name, np.array([row for row, _value in pairs], dtype=np.int64), np.array([value for _row, value in pairs]),
                          typed=np.array([isinstance(value, np.floating) for _row, value in pairs], dtype=np.bool_))

    def write_pairs(self, group: str, rows: np.ndarray, mappings: List[Mapping[str, float]]) -> None:
        """The mapping field of `group` ("unmet" or "plan") of each row is the matching mapping of `mappings`, all written as one block."""
        counts = np.fromiter(map(len, mappings), dtype=np.int64, count=len(mappings))
        if len(counts) and int(counts.max()) > getattr(self.table, WIDE_GROUPS[group][0]).shape[1]:
            self._widen(group, int(counts.max()))
        need_column, value_column, typed_column = (getattr(self.table, name) for name in WIDE_GROUPS[group])
        need_column[rows, :], value_column[rows, :], typed_column[rows, :] = 0, 0.0, 0
        getattr(self.table, group + "_count")[rows] = counts
        if int(counts.sum()):
            values = [value for held in mappings for value in held.values()]
            entry_rows = np.repeat(rows, counts)
            place = np.arange(len(entry_rows), dtype=np.int64) - np.repeat(np.cumsum(counts) - counts, counts)
            need_column[entry_rows, place] = self.names["needs"].admit([name for held in mappings for name in held])
            value_column[entry_rows, place] = values
            if set(map(type, values)) != {float}:
                typed_column[entry_rows, place] = [isinstance(value, np.floating) for value in values]
        self.written(rows)

    def milled_of(self, row: int) -> tuple:
        """The grains the cohort in `row` buys milled (kept until the row's grains are written)."""
        kept = self._milled[row]
        if kept is None:
            goods = self.names["goods"].name_list
            kept = self._milled[row] = tuple(goods[number] for number in self.table.milled_good[row, :int(self.table.milled_count[row])].tolist())
        return kept

    def pairs_of(self, group: str, row: int) -> Dict[str, float]:
        """The mapping field of `group` ("unmet" or "plan") of the cohort in `row`, as `Cohort` holds it."""
        return self._pairs(row, group)

    def write_milled(self, rows: np.ndarray, grains: List[tuple]) -> None:
        """The grains bought milled of each row are the matching tuple of `grains`."""
        for row, each in zip(rows.tolist(), grains):
            self._write_milled(row, each)
        self.written(rows)

    def written(self, rows: Optional[np.ndarray] = None) -> None:
        """A block of columns was written in place: the rows' kept `Cohort` snapshots are stale (all rows when `rows` is None)."""
        if rows is None:
            self._objects = [None] * len(self._objects)
        else:
            for row in rows.tolist():
                self._objects[row] = None
        self.version += 1

    # ---- reading blocks --------------------------------------------------------------------------------------------------

    def _scalar(self, name: str) -> np.ndarray:
        if name not in SCALAR_FLOATS + OPTIONAL_FLOATS:
            raise KeyError("%r is not a float column of the cohort table" % name)
        return getattr(self.table, name)

    def column(self, name: str) -> np.ndarray:
        """A float column over the rows in use (NaN where `share_wealth` is none), the live array: never write to it."""
        return self._scalar(name)[:self.count]

    def floats(self, name: str, rows: np.ndarray) -> list:
        """The float field of the rows as a list: a numpy float where the value was written as one, else a Python float."""
        column = self._scalar(name)
        values = column[rows].tolist()
        bit = FLOAT_BIT[name]
        for place in np.nonzero(self.table.numpy_typed[rows] & bit)[0].tolist():
            values[place] = column[rows[place]]
        return values

    def order(self) -> np.ndarray:
        """The rows in sorted id order."""
        if self._order is None or self._order_members != self._members:
            self._order = np.array(sorted(range(len(self.ids)), key=self.ids.__getitem__), dtype=np.int64)
            self._order_members = self._members
        return self._order

    def rows_of(self, cohort_ids: Iterable[str]) -> np.ndarray:
        return np.array([self.row_of[each] for each in cohort_ids], dtype=np.int64)

    def tile_numbers(self) -> np.ndarray:
        """The number (in `names["tiles"]`) of each row's tile."""
        return self.table.tile[:self.count]

    def tile_names(self, rows: Optional[np.ndarray] = None) -> List[str]:
        """The tile of each row (all rows in table order when `rows` is None)."""
        names = self.names["tiles"].name_list
        return [names[number] for number in (self.table.tile[:self.count] if rows is None else self.table.tile[rows]).tolist()]

    def tiles_present(self) -> List[str]:
        """The tiles that have a cohort, in the order their first cohort entered."""
        names = self.names["tiles"].name_list
        numbers = self.table.tile[:self.count]
        _unique, first = np.unique(numbers, return_index=True)
        return [names[numbers[place]] for place in np.sort(first).tolist()]

    def figures(self, rows: np.ndarray, with_plan: bool = False) -> List[CohortFigures]:
        """The figures of the cohorts in `rows` (in that order), each as a `CohortFigures`; no `Cohort` is built."""
        people, working, income = self.floats("people", rows), self.floats("working_people", rows), self.floats("last_year_income", rows)
        hired = self.floats("hired_work_per_person", rows)
        plans = [self._pairs(row, "plan") for row in rows.tolist()] if with_plan else [None] * len(rows)
        return [CohortFigures(self.ids[row], tile, people[place], working[place], income[place], hired[place], self.milled_of(row), plans[place])
                for place, (row, tile) in enumerate(zip(rows.tolist(), self.tile_names(rows)))]

    def tile_of(self, cohort_id: str) -> Optional[str]:
        """The tile of the cohort, None for an id the table does not hold."""
        row = self.row_of.get(cohort_id)
        return None if row is None else self.names["tiles"].name_list[self.table.tile[row]]

    def rows_on_tile(self, tile: str) -> np.ndarray:
        """The rows, in table order, of the cohorts on `tile` (empty where there are none); kept until a cohort enters or moves."""
        if self._tile_rows_members != self._members:
            numbers = self.table.tile[:self.count]
            names = self.names["tiles"].name_list
            self._tile_rows = {names[number]: np.nonzero(numbers == number)[0] for number in np.unique(numbers).tolist()}
            self._tile_rows_members = self._members
        return self._tile_rows.get(tile, np.zeros(0, dtype=np.int64))

    def richest_class(self, tile: str) -> Optional[int]:
        """Income class of the tile's richest cohort, None where the tile has none."""
        rows = self.rows_on_tile(tile)
        return int(self.table.income_class[rows].max()) if len(rows) else None

    def poorest_on_tile(self, tile: str) -> Optional[str]:
        """The id of the tile's poorest cohort (lowest income class, then lowest id), None where the tile has none."""
        rows = self.rows_on_tile(tile)
        if not len(rows):
            return None
        classes = self.table.income_class[rows]
        return min(self.ids[row] for row in rows[classes == classes.min()].tolist())

    def ids_on_tiles(self, wanted) -> List[str]:
        """The ids, in table order, of the cohorts whose tile `wanted(tile)` accepts (asked once for each tile)."""
        numbers = self.table.tile[:self.count]
        names = self.names["tiles"].name_list
        verdict = {number: wanted(names[number]) for number in np.unique(numbers).tolist()}
        return [each for each, number in zip(self.ids, numbers.tolist()) if verdict[number]]

    def exact_total(self, name: str, rows: Optional[np.ndarray] = None) -> float:
        """The exact sum (`math.fsum`) of a float field over the rows (all, in table order, when `rows` is None)."""
        column = self.column(name)
        return math.fsum((column if rows is None else column[rows]).tolist())

    def unmet_of(self, need: str) -> np.ndarray:
        """Each row's need units short of the floor for `need` (0.0 where the cohort has no figure for it)."""
        return self._need_units("unmet", need)

    def _need_units(self, group: str, need: str) -> np.ndarray:
        number = self.names["needs"].numbers.get(need)
        count = self.count
        if number is None:
            return np.zeros(count)
        needs, units = getattr(self.table, group + "_need")[:count], getattr(self.table, group + "_units")[:count]
        used = np.arange(needs.shape[1])[None, :] < getattr(self.table, group + "_count")[:count, None]
        return np.where((needs == number) & used, units, 0.0).sum(axis=1)

    # ---- building a record -----------------------------------------------------------------------------------------------

    def _build(self, row: int) -> Cohort:
        record = object.__new__(Cohort)
        record.__dict__.update(self._fields(row))
        return record

    def _pairs(self, row: int, group: str) -> Dict[str, float]:
        count = int(getattr(self.table, group + "_count")[row])
        needs = self.names["needs"].name_list
        numbers = getattr(self.table, group + "_need")[row, :count].tolist()
        values = getattr(self.table, group + "_units")[row, :count]
        typed = getattr(self.table, group + "_typed")[row, :count].tolist()
        return {needs[number]: (values[place] if typed[place] else values[place].item()) for place, number in enumerate(numbers)}

    def _fields(self, row: int) -> Dict[str, object]:
        """The fields of the cohort in `row`, in the order of `Cohort`, each a plain Python value (a numpy float where it was written as one)."""
        table = self.table
        typed = int(table.numpy_typed[row])
        fields = {
            "agent_id": self.ids[row], "tile": self.names["tiles"].name_list[table.tile[row]], "income_class": int(table.income_class[row]),
            "unmet_floor_by_need": self._pairs(row, "unmet"), "own_plan_by_need": self._pairs(row, "plan"),
            "milled_grains": self.milled_of(row),
        }
        for name in SCALAR_FLOATS:
            fields[name] = getattr(table, name)[row] if typed & FLOAT_BIT[name] else getattr(table, name)[row].item()
        wealth = float(table.share_wealth[row])
        fields["share_wealth"] = None if wealth != wealth else (table.share_wealth[row] if typed & FLOAT_BIT["share_wealth"] else wealth)
        return {name: fields[name] for name in _FIELDS}

    # ---- the save --------------------------------------------------------------------------------------------------------

    def seat_sorted(self) -> None:
        """Rows in sorted id order (a live game then iterates as a loaded one does); nothing moves when they already are."""
        order = self.order()
        if (order == np.arange(len(order))).all():
            return
        cohorts = [self.at(row) for row in order.tolist()]
        self.clear()
        for cohort in cohorts:
            self.put(cohort)

    def to_plain(self) -> Dict[str, dict]:
        """{id: the record's fields as plain data} in id order, written from the columns."""
        plain = {}
        for row in self.order().tolist():
            plain[self.ids[row]] = self._fields(row)
        return plain

    @classmethod
    def from_plain(cls, saved: Mapping[str, dict]) -> "CohortStore":
        """The store a save's cohorts describe, in the saved order."""
        store = cls()
        for fields in saved.values():
            store.put(Cohort(**fields))
        return store
