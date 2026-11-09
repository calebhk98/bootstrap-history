"""Packs the baskets and cohorts of the year's close for `households_close_kernel.unmet_floors`, and unpacks its answer as the dictionaries
`households_close.unmet_floor_by_need` made.

`PackedBaskets` holds each distinct basket once (a basket is a key the caller names, the same key the cohorts of one basket share): its needs
with their floors, goods (the book's good numbers), effects and service lives, and the places of its durables among the cells a cohort's
held stock is read at (`held_cells`)."""
from typing import Dict, List, Mapping, Sequence

import numpy as np

from .households_close_kernel import unmet_floors
from .households_cohort import Cohort
from .priced_need_tables import GOODS, basket_rows
from .stock_block import numbers_of, stock_block
from .types import GoodSpec


class PackedBaskets:
    """The baskets added so far as arrays (`add`), in the order they were added."""

    def __init__(self, book, specs: Mapping[str, GoodSpec]) -> None:
        self._book = book
        self._specs = specs
        self._by_good = None      # per good number of GOODS: (the book's number of the good or -1, its service life or 0)
        self.index: Dict[object, int] = {}
        self.baskets: List[object] = []
        self.need_start = [0]
        self.need_floor: List[float] = []
        self.row_start = [0]
        self.row_good: List[np.ndarray] = []
        self.row_effect: List[np.ndarray] = []
        self.row_life: List[np.ndarray] = []
        self.row_held_place: List[np.ndarray] = []
        self.rows = 0
        self.durables: List[List[str]] = []      # per basket: its durable goods in the order of their held places

    def _good_columns(self):
        """(book number, service life) by good number, made for the goods of GOODS known now."""
        if self._by_good is None or len(self._by_good[0]) != len(GOODS.names):
            numbers = self._book.good_ids.numbers
            lives = [self._specs[good].service_life_years if good in self._specs else 0.0 for good in GOODS.names]
            self._by_good = (np.array([numbers.get(good, -1) for good in GOODS.names], dtype=np.int64),
                             np.array([life if life > 0.0 else 0.0 for life in lives], dtype=np.float64))
        return self._by_good

    def add(self, key, basket) -> int:
        """The basket's number (it is packed on first sight of `key`)."""
        found = self.index.get(key)
        if found is not None:
            return found
        found = self.index[key] = len(self.baskets)
        self.baskets.append(basket)
        _held, specs, first, goods, effects, *_rest = basket_rows(basket.needs)
        book_number, life_of_good = self._good_columns()
        goods = np.array(goods, dtype=np.int64)
        life = life_of_good[goods]
        place = np.full(len(goods), -1, dtype=np.int64)
        durable = np.flatnonzero(life > 0.0)
        names: List[str] = []
        if len(durable):         # a durable's place is the order of its first row among the basket's durables
            distinct, first_row = np.unique(goods[durable], return_index=True)
            by_first = np.argsort(first_row)
            place_of_distinct = np.empty(len(distinct), dtype=np.int64)
            place_of_distinct[by_first] = np.arange(len(distinct))
            place[durable] = place_of_distinct[np.searchsorted(distinct, goods[durable])]
            names = GOODS.name_array()[distinct[by_first]].tolist()
        self.need_floor.extend(spec.subsistence_per_person for spec in specs)
        self.row_good.append(book_number[goods])
        self.row_effect.append(np.array(effects, dtype=np.float64))
        self.row_life.append(life)
        self.row_held_place.append(place)
        self.row_start.extend(self.rows + end for end in first[1:] + [len(goods)])
        self.rows += len(goods)
        self.durables.append(names)
        self.need_start.append(len(self.need_floor))
        return found


def _joined(blocks: List[np.ndarray], dtype) -> np.ndarray:
    return np.concatenate(blocks) if blocks else np.zeros(0, dtype=dtype)


def unmet_by_cohort(book, packed: PackedBaskets, cohorts: Sequence[Cohort], basket_numbers: Sequence[int], receipt_start: np.ndarray,
                    receipt_goods: np.ndarray, receipt_amounts: np.ndarray) -> List[Dict[str, float]]:
    """`households_close.unmet_floor_by_need` for each cohort, in the order given: `basket_numbers` are `packed`'s numbers, the receipts the
    arrays of `receipts_with_grown` (cohorts in the same order). The held stocks of the durables are read from the book in one block."""
    count = len(cohorts)
    held_start = np.zeros(count + 1, dtype=np.int64)
    held_agents, held_goods, held_tiles = [], [], []
    for position, cohort in enumerate(cohorts):
        durables = packed.durables[basket_numbers[position]]
        held_start[position + 1] = held_start[position] + len(durables)
        held_agents.extend([cohort.agent_id] * len(durables))
        held_goods.extend(durables)
        held_tiles.extend([cohort.tile] * len(durables))
    held = stock_block(book, numbers_of(book.agent_ids, held_agents), numbers_of(book.good_ids, held_goods), numbers_of(book.tile_ids, held_tiles))
    widest = max((len(basket.needs) for basket in packed.baskets), default=0)
    unmet = np.full((count, max(widest, 1)), np.nan)
    unmet_floors(np.array([cohort.people for cohort in cohorts], dtype=np.float64), np.array(basket_numbers, dtype=np.int64), receipt_start,
                 receipt_goods, receipt_amounts, np.array(packed.need_start, dtype=np.int64), np.array(packed.need_floor, dtype=np.float64),
                 np.array(packed.row_start, dtype=np.int64), _joined(packed.row_good, np.int64), _joined(packed.row_effect, np.float64),
                 _joined(packed.row_life, np.float64), _joined(packed.row_held_place, np.int64), held_start, held,
                 len(book.good_ids), unmet)
    answers = []
    for position in range(count):
        basket = packed.baskets[basket_numbers[position]]
        row = unmet[position].tolist()
        answers.append({need.need_id: row[place] for place, need in enumerate(basket.needs) if row[place] == row[place]})
    return answers
