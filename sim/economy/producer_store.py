"""The producer table: every producer as a row of columns (`producer_rows.py`), and the mapping view over it.

`ProducerStore` is what `record.producers` is. The year loop reads and writes its columns (`table`, `ids`, `order`, the block
writes below); a `Producer` is built only when something asks for one through the mapping (`store[producer_id]`, `.values()`,
`.items()`), which is how the screens, the protocol, mods, tests and the code not yet on columns read it. A `Producer` handed
out is a snapshot: changing the table changes the next one built, never one already held, and `put` (or `store[id] = producer`)
writes a whole record into its row.

Rows are in the order the producers entered (a mapping's insertion order); an exit leaves a dead row (`ids[row]` is None) that
`compact` removes, and every method that reads blocks compacts first. `version` rises on every write, so a reader that
keeps a derived copy (`year_arrays_producers.ProducerColumns`) knows when to read again. `order` is the rows in sorted id order,
the order the year arrays number producers in."""
import math
from collections.abc import MutableMapping
from typing import Dict, Iterable, Iterator, List, Mapping, Optional, Tuple

import numpy as np

from sim.compiled_tables.growth import reserve_rows
from sim.compiled_tables.ids import IdTable

from .producer_rows import (NAME_COLUMNS, OPTIONAL_FLOATS, PRODUCER_ROWS_SPEC, SCALAR_FLOATS, SCALAR_INTS, WIDE_COLUMNS, ProducerRows)
from .producer_blocks import crews_of, owners_at
from .producers import Producer

_FIRST_CAPACITY = 64
_NAME_TABLES = {"owner": "owners", "recipe": "recipes", "tile": "tiles"}
_FIELDS = ("agent_id", "owner", "recipe_id", "tile", "capacity_runs", "yield_factor", "expected_prices", "years_of_loss",
           "cash_target", "expected_sales", "last_runs", "land_rent_per_run", "land_run_cap", "workshops", "net_earnings_history",
           "revenue_history", "idle_years", "staffed_runs", "crew_runs")


class ProducerStore(MutableMapping):
    """The producers by id, as columns; a mapping from agent id to `Producer`."""

    def __init__(self, producers: Optional[Mapping[str, Producer]] = None):
        self.table: ProducerRows = PRODUCER_ROWS_SPEC.new_table(
            ProducerRows, _FIRST_CAPACITY, widths={name: 1 for name in WIDE_COLUMNS})
        self.names: Dict[str, IdTable] = {kind: IdTable(kind) for kind in ("owners", "recipes", "tiles", "goods", "trades")}
        self.ids: List[Optional[str]] = []          # by row; None for a producer that exited and is not yet compacted
        self.row_of: Dict[str, int] = {}
        self.version = 0                            # rises on every write
        self.members_version = 0                    # rises when a producer enters or leaves
        self.layout = 0                             # rises when rows are renumbered (compaction, reseating in id order)
        self._dead = 0
        self._objects: List[Optional[Producer]] = []
        self._order: Optional[np.ndarray] = None
        self._order_version = -1
        if producers:
            for producer in producers.values():
                self.put(producer)

    @property
    def count(self) -> int:
        """Rows in use, dead ones included."""
        return int(self.table.row_count[0])

    # ---- the mapping -----------------------------------------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.row_of)

    def __contains__(self, producer_id) -> bool:
        return producer_id in self.row_of

    def __iter__(self) -> Iterator[str]:
        return iter(self.row_of)

    def __getitem__(self, producer_id: str) -> Producer:
        return self.at(self.row_of[producer_id])

    def __setitem__(self, producer_id: str, producer: Producer) -> None:
        if producer.agent_id != producer_id:
            raise ValueError("producer %r stored under %r" % (producer.agent_id, producer_id))
        self.put(producer)

    def __delitem__(self, producer_id: str) -> None:
        row = self.row_of.pop(producer_id)
        self.ids[row] = None
        self._objects[row] = None
        self._dead += 1
        self.members_version += 1
        self.version += 1

    def __eq__(self, other) -> bool:
        return isinstance(other, Mapping) and dict(self.items()) == dict(other.items())

    __hash__ = None

    def get(self, producer_id, default=None):
        row = self.row_of.get(producer_id)
        return default if row is None else self.at(row)

    def keys(self):
        return self.row_of.keys()

    def values(self):
        return [self.at(row) for row in self.row_of.values()]

    def items(self):
        return [(producer_id, self.at(row)) for producer_id, row in self.row_of.items()]

    def clear(self) -> None:
        version, members, layout, names = self.version + 1, self.members_version + 1, self.layout + 1, self.names
        self.__init__()
        self.version, self.members_version, self.layout, self.names = version, members, layout, names   # counters and numbers never go back

    def at(self, row: int) -> Producer:
        """The producer in `row`, built from the columns and kept until the row is written."""
        kept = self._objects[row]
        if kept is None:
            kept = self._objects[row] = self._build(row)
        return kept

    # ---- writing a record ------------------------------------------------------------------------------------------------

    def put(self, producer: Producer) -> int:
        """`producer` is the table's row for its id, new (a row at the end) or replacing; the row's number."""
        row = self.row_of.get(producer.agent_id)
        if row is None:
            row = self._claim(producer.agent_id)
        self._write(row, producer)
        self._objects[row] = None
        self.version += 1
        return row

    def _claim(self, producer_id: str) -> int:
        self.table = reserve_rows(self.table, 1)
        row = self.count
        self.table.row_count[0] = row + 1
        self.ids.append(producer_id)
        self._objects.append(None)
        self.row_of[producer_id] = row
        self.members_version += 1
        return row

    def _name(self, kind: str, name: str) -> int:
        table = self.names[kind]
        found = table.numbers.get(name)
        return table.admit([name])[0] if found is None else found

    def _widen(self, column: str, width: int) -> None:
        """Room for `width` places a row in the wide columns that go with `column` (all columns of its group grow together)."""
        group = {"earnings_history": ("earnings_history",), "revenue_history": ("revenue_history",),
                 "price_good": ("price_good", "price_value"), "price_value": ("price_good", "price_value"),
                 "crew_trade": ("crew_trade", "crew_units"), "crew_units": ("crew_trade", "crew_units")}[column]
        wanted = max(width, 1)
        fields = {name: getattr(self.table, name) for name in self.table._fields}
        for name in group:
            old = fields[name]
            if old.shape[1] < wanted:
                grown = np.zeros((old.shape[0], max(wanted, 2 * old.shape[1])), dtype=old.dtype)
                grown[:, :old.shape[1]] = old
                fields[name] = grown
        self.table = ProducerRows(**fields)

    def _write(self, row: int, producer: Producer) -> None:
        table = self.table
        table.owner[row] = self._name("owners", producer.owner)
        table.recipe[row] = self._name("recipes", producer.recipe_id)
        table.tile[row] = self._name("tiles", producer.tile)
        for name in SCALAR_FLOATS + SCALAR_INTS:
            getattr(table, name)[row] = getattr(producer, name)
        table.land_run_cap[row] = np.nan if producer.land_run_cap is None else producer.land_run_cap
        table.staffed_runs[row] = np.nan if producer.staffed_runs is None else producer.staffed_runs
        for column, count, values in (("earnings_history", "earnings_count", producer.net_earnings_history),
                                      ("revenue_history", "revenue_count", producer.revenue_history)):
            if len(values) > getattr(self.table, column).shape[1]:
                self._widen(column, len(values))
                table = self.table
            getattr(table, column)[row, :] = 0.0
            getattr(table, column)[row, :len(values)] = values
            getattr(table, count)[row] = len(values)
        self._write_pairs(row, "price_good", "price_value", "price_count", "goods", producer.expected_prices)
        self._write_pairs(row, "crew_trade", "crew_units", "crew_count", "trades", producer.crew_runs)

    def _write_pairs(self, row: int, key_column: str, value_column: str, count_column: str, kind: str, held: Mapping[str, float]) -> None:
        if len(held) > getattr(self.table, key_column).shape[1]:
            self._widen(key_column, len(held))
        keys, values = getattr(self.table, key_column), getattr(self.table, value_column)
        keys[row, :], values[row, :] = 0, 0.0
        for place, (name, value) in enumerate(held.items()):
            keys[row, place] = self._name(kind, name)
            values[row, place] = value
        getattr(self.table, count_column)[row] = len(held)

    def crew_of(self, row: int) -> Dict[str, float]:
        """The crew's practice of the producer in `row` ({trade: runs made}, in the order written)."""
        count = int(self.table.crew_count[row])
        names = self.names["trades"].name_list
        return {names[number]: units for number, units in
                zip(self.table.crew_trade[row, :count].tolist(), self.table.crew_units[row, :count].tolist())}

    def write_crew(self, row: int, crew: Mapping[str, float]) -> None:
        """The crew's practice of the producer in `row` is `crew`."""
        self._write_pairs(row, "crew_trade", "crew_units", "crew_count", "trades", crew)
        self._objects[row] = None
        self.version += 1

    def enter(self, producer_id: str, owner: str, recipe_id: str, tile: str, capacity_runs: float, expected_sales: float,
              yield_factor: float, workshops: int, crew: Mapping[str, float]) -> None:
        """A producer enters as a new row (every field not given is what a `Producer` starts with); the id must not be in the table."""
        if producer_id in self.row_of:
            raise KeyError("producer %r is already in the table" % producer_id)
        row = self._claim(producer_id)
        table = self.table
        table.owner[row] = self._name("owners", owner)
        table.recipe[row] = self._name("recipes", recipe_id)
        table.tile[row] = self._name("tiles", tile)
        for name, value in (("capacity_runs", capacity_runs), ("expected_sales", expected_sales), ("yield_factor", yield_factor),
                            ("workshops", workshops), ("last_runs", -1.0), ("land_run_cap", np.nan), ("staffed_runs", np.nan)):
            getattr(table, name)[row] = value
        self._write_pairs(row, "crew_trade", "crew_units", "crew_count", "trades", crew)
        self._objects[row] = None
        self.version += 1

    def ids_on_tiles(self, wanted) -> List[str]:
        """The ids, in table order, of the producers whose tile `wanted(tile)` accepts (asked once for each tile)."""
        numbers = self.table.tile[:self.count]
        alive = [each is not None for each in self.ids]
        names = self.names["tiles"].name_list
        verdict = {number: wanted(names[number]) for number in np.unique(numbers[np.array(alive, dtype=np.bool_)]).tolist()}
        return [each for each, number, live in zip(self.ids, numbers.tolist(), alive) if live and verdict[number]]

    def tiles_in_use(self) -> List[str]:
        """The tiles some producer is on (each once)."""
        alive = np.array([each is not None for each in self.ids], dtype=np.bool_)
        return self.name_of("tiles", np.unique(self.table.tile[:self.count][alive]))

    def exact_total(self, name: str) -> float:
        """The exact sum (`math.fsum`) of a float field over the producers."""
        alive = np.array([each is not None for each in self.ids], dtype=np.bool_)
        return math.fsum(self._scalar(name)[:self.count][alive].tolist())

    def owners_of(self, producer_ids: Iterable[str]) -> List[str]:
        """The owner of each producer named."""
        return owners_at(self, np.array([self.row_of[each] for each in producer_ids], dtype=np.int64))

    def live_rows(self) -> np.ndarray:
        """The rows of the producers in the table, in table order (the order they entered)."""
        return np.nonzero([each is not None for each in self.ids])[0]

    def tile_of(self, producer_id: str) -> Optional[str]:
        """The tile of the producer, None for an id the table does not hold."""
        row = self.row_of.get(producer_id)
        return None if row is None else self.names["tiles"].name_list[self.table.tile[row]]

    def recipe_id_of(self, producer_id: str) -> Optional[str]:
        """The recipe of the producer, None for an id the table does not hold."""
        row = self.row_of.get(producer_id)
        return None if row is None else self.names["recipes"].name_list[self.table.recipe[row]]

    def rows_with_recipes(self, wanted: Iterable[bool], in_id_order: bool = True) -> np.ndarray:
        """The rows (sorted by id, else in table order) of the producers whose recipe the flag says: `wanted[number]` is the flag of
        the recipe with that number in `names["recipes"]`."""
        rows = self.order() if in_id_order else np.nonzero([each is not None for each in self.ids])[0]
        return rows[np.array(list(wanted), dtype=np.bool_)[self.table.recipe[rows]]]

    def owner_at(self, row: int) -> str:
        """The owner of the producer in `row`."""
        return self.names["owners"].name_list[self.table.owner[row]]

    def crews_by_recipe(self, in_id_order: bool = True) -> Dict[str, List[Mapping[str, float]]]:
        """Each recipe's producers' crews (the practice by trade; an empty mapping where the crew is established), in producer id
        order, or in the order the producers entered."""
        order = self.order() if in_id_order else np.nonzero([each is not None for each in self.ids])[0]
        recipe_names = self.names["recipes"].name_list
        grouped: Dict[str, List[Mapping[str, float]]] = {}
        for recipe, crew in zip(self.table.recipe[order].tolist(), crews_of(self, order)):
            grouped.setdefault(recipe_names[recipe], []).append(crew)
        return grouped

    def set_fields(self, producer_id: str, **changes) -> None:
        """The scalar fields named (a `Producer` field that is a number, or `land_run_cap` / `staffed_runs`, None for none) of one
        producer take the values."""
        row = self.row_of[producer_id]
        for name, value in changes.items():
            self._scalar(name)[row] = np.nan if value is None else value
        self._objects[row] = None
        self.version += 1

    def set_column(self, name: str, producer_ids: Iterable[str], values: Iterable[float]) -> None:
        """One scalar field of the producers named takes the values (an id the table does not hold is skipped)."""
        pairs = [(self.row_of[each], value) for each, value in zip(producer_ids, values) if each in self.row_of]
        if pairs:
            self.set_rows(name, np.array([row for row, _value in pairs], dtype=np.int64), np.array([value for _row, value in pairs]))

    def set_rows(self, name: str, rows: np.ndarray, values: np.ndarray) -> None:
        """One scalar field of the rows takes the values (NaN where the field is optional and the value is NaN: none)."""
        self._scalar(name)[rows] = values
        self.written(rows)

    def floats(self, name: str, rows: np.ndarray) -> list:
        """The scalar field of the rows as a list of Python numbers."""
        return self._scalar(name)[rows].tolist()

    def value(self, row: int, name: str):
        """One scalar field of one row, as a Python number."""
        return self._scalar(name).item(row)

    def _scalar(self, name: str) -> np.ndarray:
        if name not in SCALAR_FLOATS + SCALAR_INTS + OPTIONAL_FLOATS:
            raise KeyError("%r is not a scalar column of the producer table" % name)
        return getattr(self.table, name)

    # ---- building a record -----------------------------------------------------------------------------------------------

    def _build(self, row: int) -> Producer:
        """The `Producer` a row holds."""
        record = object.__new__(Producer)
        record.__dict__.update(self._fields(row))
        return record

    def _fields(self, row: int) -> Dict[str, object]:
        """The fields of the producer in `row`, in the order of `Producer`, each a plain Python value."""
        table, names = self.table, self.names
        earnings, revenue = int(table.earnings_count[row]), int(table.revenue_count[row])
        prices = int(table.price_count[row])
        land_cap, staffed = float(table.land_run_cap[row]), float(table.staffed_runs[row])
        good_names = names["goods"].name_list
        fields = {
            "agent_id": self.ids[row], "owner": names["owners"].name_list[table.owner[row]],
            "recipe_id": names["recipes"].name_list[table.recipe[row]], "tile": names["tiles"].name_list[table.tile[row]],
            "expected_prices": {good_names[number]: value for number, value in
                                zip(table.price_good[row, :prices].tolist(), table.price_value[row, :prices].tolist())},
            "land_run_cap": None if land_cap != land_cap else land_cap,
            "staffed_runs": None if staffed != staffed else staffed,
            "net_earnings_history": tuple(table.earnings_history[row, :earnings].tolist()),
            "revenue_history": tuple(table.revenue_history[row, :revenue].tolist()),
            "crew_runs": self.crew_of(row),
        }
        for name in SCALAR_FLOATS + SCALAR_INTS:
            fields[name] = getattr(table, name)[row].item()
        return {name: fields[name] for name in _FIELDS}

    # ---- blocks ----------------------------------------------------------------------------------------------------------

    def compact(self) -> None:
        """Drop the dead rows, keeping the others in their order; the same table when nothing exited."""
        if not self._dead:
            return
        keep = np.array([each is not None for each in self.ids], dtype=np.bool_)
        kept = int(keep.sum())
        fields = {}
        for name in self.table._fields:
            column = getattr(self.table, name)
            if name == "row_count":
                fields[name] = np.array([kept], dtype=np.int64)
            elif name == "capacity":
                fields[name] = column
            else:
                packed = np.zeros_like(column)
                packed[:kept] = column[:len(keep)][keep]
                fields[name] = packed
        self.table = ProducerRows(**fields)
        self.ids = [each for each in self.ids if each is not None]
        self._objects = [each for each, alive in zip(self._objects, keep.tolist()) if alive]
        self.row_of = {producer_id: row for row, producer_id in enumerate(self.ids)}
        self._dead = 0
        self.members_version += 1
        self.layout += 1
        self.version += 1

    def seat_sorted(self) -> None:
        """Rows in sorted id order (a live game that has had producers enter then iterates as a loaded one does); nothing moves when
        they already are."""
        order = self.order()
        if (order == np.arange(len(order))).all():
            return
        fields = {}
        for name in self.table._fields:
            column = getattr(self.table, name)
            fields[name] = column if name in ("row_count", "capacity") else np.concatenate([column[order], column[len(order):]])
        self.table = ProducerRows(**fields)
        self.ids = [self.ids[row] for row in order.tolist()]
        self._objects = [self._objects[row] for row in order.tolist()]
        self.row_of = {producer_id: row for row, producer_id in enumerate(self.ids)}
        self._order = np.arange(len(order), dtype=np.int64)
        self.members_version += 1
        self._order_version = self.members_version
        self.layout += 1
        self.version += 1

    def order(self) -> np.ndarray:
        """The rows in sorted id order (compacts first)."""
        self.compact()
        if self._order is None or self._order_version != self.members_version:
            self._order = np.array(sorted(range(len(self.ids)), key=self.ids.__getitem__), dtype=np.int64)
            self._order_version = self.members_version
        return self._order

    def rows_of(self, producer_ids: Iterable[str]) -> np.ndarray:
        self.compact()
        return np.array([self.row_of[each] for each in producer_ids], dtype=np.int64)

    def written(self, rows: Optional[np.ndarray] = None) -> None:
        """A block of columns was written in place: the rows' kept `Producer` snapshots are stale (all rows when `rows` is None)."""
        if rows is None:
            self._objects = [None] * len(self._objects)
        else:
            for row in rows.tolist():
                self._objects[row] = None
        self.version += 1

    def name_of(self, kind: str, numbers: np.ndarray) -> List[str]:
        """The names of the numbers (kind: owners, recipes, tiles, goods or trades), in order."""
        names = self.names[kind].name_list
        return [names[number] for number in numbers.tolist()]

    # ---- the save --------------------------------------------------------------------------------------------------------

    def to_plain(self) -> Dict[str, dict]:
        """{id: the record's fields as plain data} in id order, written from the columns."""
        self.compact()
        plain = {}
        for row in self.order().tolist():
            plain[self.ids[row]] = self._fields(row)
        return plain

    @classmethod
    def from_plain(cls, saved: Mapping[str, dict]) -> "ProducerStore":
        """The store a save's producers describe, in the saved order."""
        store = cls()
        for fields in saved.values():
            store.put(Producer(**fields))
        return store
