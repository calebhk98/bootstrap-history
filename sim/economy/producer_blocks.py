"""Block reads of the producer table: a figure of many producers at once, from the columns, with no `Producer` built.

Each takes the store and the producers' ids (or rows) and gives one answer per id, in the order given. An id the table does not
hold is None in the name reads, as `ProducerStore.tile_of` answers one."""
from typing import Dict, Iterable, List, Mapping, NamedTuple, Optional

import numpy as np


def _names_of(store, column: str, kind: str, producer_ids: Iterable[str]) -> List[Optional[str]]:
    """The name in `column` (numbers into the store's `kind` names) of each producer; None for an id the table does not hold."""
    producer_ids = list(producer_ids)
    if not producer_ids:
        return []
    row_of = store.row_of
    rows = [row_of.get(each) for each in producer_ids]
    held = [place for place, row in enumerate(rows) if row is not None]
    answer: List[Optional[str]] = [None] * len(rows)
    if held:
        names = store.names[kind].name_list
        numbers = getattr(store.table, column)[np.array([rows[place] for place in held], dtype=np.int64)].tolist()
        for place, number in zip(held, numbers):
            answer[place] = names[number]
    return answer


def tiles_of(store, producer_ids: Iterable[str]) -> List[Optional[str]]:
    """The tile of each producer (`ProducerStore.tile_of` for each)."""
    return _names_of(store, "tile", "tiles", producer_ids)


def recipes_of(store, producer_ids: Iterable[str]) -> List[Optional[str]]:
    """The recipe id of each producer (`ProducerStore.recipe_id_of` for each)."""
    return _names_of(store, "recipe", "recipes", producer_ids)


def owners_at(store, rows: np.ndarray) -> List[str]:
    """The owner of the producer in each row (`ProducerStore.owner_at` for each)."""
    names = store.names["owners"].name_list
    return [names[number] for number in store.table.owner[rows].tolist()]


def expected_prices_of(store, rows: Iterable[int]) -> List[Mapping[str, float]]:
    """The expected prices ({good: price}, in the order written) of the producer in each row, read from the columns together."""
    rows = np.fromiter(rows, dtype=np.int64)
    table, good_names = store.table, store.names["goods"].name_list
    counts = table.price_count[rows].tolist()
    goods, values = table.price_good[rows], table.price_value[rows]
    return [{good_names[number]: value for number, value in zip(goods[place, :count].tolist(), values[place, :count].tolist())}
            for place, count in enumerate(counts)]


def figures_of(store, name: str, rows: Iterable[int]) -> list:
    """A scalar field of the producer in each row, typed as `ProducerStore.floats` says (a numpy float where it was written as one)."""
    return store.floats(name, np.fromiter(rows, dtype=np.int64))



class RowFigures(NamedTuple):
    """What a rule that prices a producer's runs reads of its row."""
    producer_id: str
    tile: str
    recipe_id: str
    yield_factor: float
    expected_prices: Mapping[str, float]


def row_figures(store, rows: Iterable[int]) -> List[RowFigures]:
    """`RowFigures` of the producer in each row, read as columns: no `Producer` is built."""
    rows = np.fromiter(rows, dtype=np.int64)
    ids = store.ids
    tiles, recipes = store.names["tiles"].name_list, store.names["recipes"].name_list
    return [RowFigures(ids[row], tiles[tile], recipes[recipe], yield_factor, expected) for row, tile, recipe, yield_factor, expected in zip(
        rows.tolist(), store.table.tile[rows].tolist(), store.table.recipe[rows].tolist(), figures_of(store, "yield_factor", rows),
        expected_prices_of(store, rows))]


def figures_by_id(store, producer_ids: Iterable[str]) -> Dict[str, RowFigures]:
    """{id: `RowFigures`} of the producers named that the table holds, in the order given."""
    held = [each for each in producer_ids if each in store.row_of]
    return dict(zip(held, row_figures(store, [store.row_of[each] for each in held])))
