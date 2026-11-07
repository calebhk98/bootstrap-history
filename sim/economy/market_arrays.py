"""Market figures held as arrays indexed by (first, area) ids, with the dictionary methods callers already use.

A market is named by a string key (`market_key(good_or_trade, area)`). `MarketIds` numbers the goods (or trades) and
the areas once, in the order they are first met, and keeps each key's two ids, so the string is split once per key and never
again. `MarketStore` holds one figure per market in a growable (first by area) array, read and written like a dictionary
(`get`, `[]`, `in`, `pop`, `items`, ...) for the callers that read one value, and as arrays (`gather`, `present`,
`cells`) for the phases that read many. Iteration is in sorted key order, so a game and its reload walk the markets alike.

An absent market is NaN in a float store, -1 in an integer store and -1 in a text store (whose strings are small integer
codes into `MarketStore.words`)."""
from collections.abc import MutableMapping
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np

KEY_SEPARATOR = "|"
_FIRST_CAPACITY = 8
FLOAT, INTEGER, TEXT = "float", "integer", "text"
_DTYPE = {FLOAT: np.float64, INTEGER: np.int64, TEXT: np.int32}


_SPLIT: Dict[str, Tuple[str, str]] = {}      # market key -> (first part, area), each key split once per process


def split_key(key: str) -> Tuple[str, str]:
    """(good or trade, area) of a market key, `key.split(KEY_SEPARATOR, 1)` kept: a key is split once, not on every pass over a store."""
    found = _SPLIT.get(key)
    if found is None:
        first, _separator, area = key.partition(KEY_SEPARATOR)
        found = _SPLIT[key] = (first, area)
    return found


class MarketIds:
    """The numbering of the goods (or trades) and of the areas a set of stores shares."""

    def __init__(self) -> None:
        self.first_row: Dict[str, int] = {}
        self.first_names: List[str] = []
        self.area_column: Dict[str, int] = {}
        self.area_names: List[str] = []
        self.cells: Dict[str, Tuple[int, int]] = {}                 # key -> (row, column)
        self.cell_of_pair: Dict[str, Dict[str, Tuple[int, int]]] = {}    # first -> area -> (row, column)
        self.key_of_cell: Dict[Tuple[int, int], str] = {}

    def admit(self, key: str) -> Tuple[int, int]:
        """The (row, column) of a market key, numbering its first part and its area if they are new."""
        cell = self.cells.get(key)
        if cell is not None:
            return cell
        first, _separator, area = key.partition(KEY_SEPARATOR)
        row = self.first_row.get(first)
        if row is None:
            row = self.first_row[first] = len(self.first_names)
            self.first_names.append(first)
            self.cell_of_pair[first] = {}
        column = self.area_column.get(area)
        if column is None:
            column = self.area_column[area] = len(self.area_names)
            self.area_names.append(area)
        cell = (row, column)
        self.cells[key] = cell
        self.cell_of_pair[first][area] = cell
        self.key_of_cell[cell] = key
        return cell

    def admit_pair(self, first: str, area: str) -> Tuple[int, int]:
        return self.admit(first + KEY_SEPARATOR + area)

    def rows_of(self, names: Iterable[str]) -> np.ndarray:
        """The row of each first part, -1 for one never met."""
        return np.array([self.first_row.get(name, -1) for name in names], dtype=np.int64)

    def columns_of(self, areas: Iterable[str]) -> np.ndarray:
        """The column of each area, -1 for one never met."""
        return np.array([self.area_column.get(area, -1) for area in areas], dtype=np.int64)


class MarketStore(MutableMapping):
    """One figure per market in a (first by area) array; a mapping from market key to figure."""

    def __init__(self, ids: MarketIds, kind: str = FLOAT, items=()) -> None:
        self.ids = ids
        self.kind = kind
        self.words: List[str] = []             # a text store's strings, by code
        self._code_of: Dict[str, int] = {}
        self._absent = np.nan if kind == FLOAT else -1
        self.grid = np.full((_FIRST_CAPACITY, _FIRST_CAPACITY), self._absent, dtype=_DTYPE[kind])
        self._count = 0
        self._version = 0                       # moves when a market enters or leaves
        self._sorted: Optional[tuple] = None    # (version, keys, rows, columns)
        self.update(items)

    def _fit(self, row: int, column: int) -> None:
        rows, columns = self.grid.shape
        if row < rows and column < columns:
            return
        new_rows = rows if row < rows else max(2 * rows, row + 1)
        new_columns = columns if column < columns else max(2 * columns, column + 1)
        grown = np.full((new_rows, new_columns), self._absent, dtype=_DTYPE[self.kind])
        grown[:rows, :columns] = self.grid
        self.grid = grown

    def fit_to_ids(self) -> np.ndarray:
        """The array, grown to cover every first part and area the ids number (so a gather never leaves it)."""
        if self.ids.first_names or self.ids.area_names:
            self._fit(max(0, len(self.ids.first_names) - 1), max(0, len(self.ids.area_names) - 1))
        return self.grid

    def _read(self, row: int, column: int):
        """The stored figure of a cell, None where absent."""
        values = self.grid
        if row >= values.shape[0] or column >= values.shape[1]:
            return None
        found = values.item(row, column)
        if self.kind == FLOAT:
            return None if found != found else found
        if found < 0:
            return None
        return self.words[found] if self.kind == TEXT else found

    def read_cell(self, cell: Tuple[int, int]):
        return self._read(cell[0], cell[1])

    def get(self, key, default=None):
        cell = self.ids.cells.get(key)
        if cell is None:
            return default
        found = self._read(cell[0], cell[1])
        return default if found is None else found

    def get_pair(self, first: str, area: str, default=None):
        """`get(first + KEY_SEPARATOR + area)` without building the string."""
        by_area = self.ids.cell_of_pair.get(first)
        cell = None if by_area is None else by_area.get(area)
        if cell is None:
            return default
        found = self._read(cell[0], cell[1])
        return default if found is None else found

    def __getitem__(self, key):
        found = self.get(key)
        if found is None:
            raise KeyError(key)
        return found

    def __contains__(self, key) -> bool:
        cell = self.ids.cells.get(key)
        return cell is not None and self._read(cell[0], cell[1]) is not None

    def _code(self, word: str) -> int:
        code = self._code_of.get(word)
        if code is None:
            code = self._code_of[word] = len(self.words)
            self.words.append(word)
        return code

    def __setitem__(self, key, value) -> None:
        row, column = self.ids.admit(key)
        self._fit(row, column)
        if self.kind == TEXT:
            value = self._code(value)
        values = self.grid
        before = values.item(row, column)
        if (before != before) if self.kind == FLOAT else before < 0:
            self._count += 1
            self._version += 1
        values[row, column] = value

    def __delitem__(self, key) -> None:
        if self.pop(key, None) is None:
            raise KeyError(key)

    def pop(self, key, *default):
        cell = self.ids.cells.get(key)
        found = None if cell is None else self._read(cell[0], cell[1])
        if found is None:
            if default:
                return default[0]
            raise KeyError(key)
        self.grid[cell[0], cell[1]] = self._absent
        self._count -= 1
        self._version += 1
        return found

    def clear(self) -> None:
        self.grid[:] = self._absent
        self._count = 0
        self._version += 1

    def __len__(self) -> int:
        return self._count

    def __bool__(self) -> bool:
        return self._count > 0

    def _walk(self) -> tuple:
        """(version, keys, rows, columns) of the present markets in sorted key order, kept until a market enters or leaves."""
        kept = self._sorted
        if kept is not None and kept[0] == self._version:
            return kept
        present = ~np.isnan(self.grid) if self.kind == FLOAT else self.grid >= 0
        rows, columns = np.nonzero(present)
        key_of_cell = self.ids.key_of_cell
        keys = [key_of_cell[cell] for cell in zip(rows.tolist(), columns.tolist())]
        order = sorted(range(len(keys)), key=keys.__getitem__)
        index = np.array(order, dtype=np.int64)
        kept = self._sorted = (self._version, [keys[each] for each in order], rows[index], columns[index])
        return kept

    def __iter__(self):
        return iter(self._walk()[1])

    def keys(self):
        return list(self._walk()[1])

    def values(self):
        return self.values_list()

    def values_list(self) -> list:
        """The figures in sorted key order, as Python numbers (or strings)."""
        _version, _keys, rows, columns = self._walk()
        found = self.grid[rows, columns].tolist()
        return [self.words[each] for each in found] if self.kind == TEXT else found

    def items(self):
        return list(zip(self._walk()[1], self.values_list()))

    def positions(self) -> tuple:
        """(keys, rows, columns) of the present markets in sorted key order, for a reader that works on arrays."""
        _version, keys, rows, columns = self._walk()
        return keys, rows, columns

    def present(self) -> np.ndarray:
        """A boolean array shaped like `grid`: where a market holds a figure."""
        return ~np.isnan(self.grid) if self.kind == FLOAT else self.grid >= 0

    def gather(self, rows: np.ndarray, columns: np.ndarray) -> np.ndarray:
        """The figures of the (rows by columns) block, a row or column of -1 (an id never met) all absent. The block is a copy;
        a text store gives codes (absent -1)."""
        found = np.full((len(rows), len(columns)), self._absent, dtype=_DTYPE[self.kind])
        keep_rows, keep_columns = np.flatnonzero(rows >= 0), np.flatnonzero(columns >= 0)
        if len(keep_rows) and len(keep_columns):
            values = self.fit_to_ids()
            found[np.ix_(keep_rows, keep_columns)] = values[np.ix_(rows[keep_rows], columns[keep_columns])]
        return found

    def at(self, rows: np.ndarray, columns: np.ndarray) -> np.ndarray:
        """The figure of each cell (rows[i], columns[i]), one array of the length of the cells; absent where none."""
        return self.fit_to_ids()[rows, columns]

    def add_to_all(self, amount) -> None:
        """Every present figure of an integer store grows by `amount`."""
        self.grid[self.grid >= 0] += amount

    def copy_dict(self) -> dict:
        return dict(self.items())

    def __repr__(self) -> str:
        return repr(dict(self.items()))
