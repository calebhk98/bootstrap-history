"""Packs the baskets and cohorts of the year's close for `households_close_kernel.unmet_floors`, and unpacks its answer as the dictionaries
`households_close.unmet_floor_by_need` made.

`PackedBaskets` holds each distinct basket once (a basket is a key the caller names, the same key the cohorts of one basket share): its needs
with their floors, goods (the book's good numbers), effects and service lives, and the places of its durables among the cells a cohort's
held stock is read at (`held_cells`)."""
from typing import Dict, List, Mapping, Sequence

import numpy as np

from .households_close_kernel import unmet_floors
from .stock_block import numbers_of, stock_block
from .types import GoodSpec


class PackedBaskets:
    """The baskets added so far as arrays (`add`), in the order they were added."""

    def __init__(self, book, specs: Mapping[str, GoodSpec]) -> None:
        self._book = book
        self._specs = specs
        self.index: Dict[object, int] = {}
        self.baskets: List[object] = []
        self.need_start = [0]
        self.need_floor: List[float] = []
        self.row_start = [0]
        self.row_good: List[int] = []
        self.row_effect: List[float] = []
        self.row_life: List[float] = []
        self.row_held_place: List[int] = []
        self.durables: List[List[str]] = []      # per basket: its durable goods in the order of their held places

    def add(self, key, basket) -> int:
        """The basket's number (it is packed on first sight of `key`)."""
        found = self.index.get(key)
        if found is not None:
            return found
        found = self.index[key] = len(self.baskets)
        self.baskets.append(basket)
        durables: List[str] = []
        place_of: Dict[str, int] = {}
        numbers = self._book.good_ids.numbers
        for need in basket.needs:
            self.need_floor.append(need.subsistence_per_person)
            for good, effect in need.goods:
                spec = self._specs.get(good)
                life = spec.service_life_years if spec is not None and spec.service_life_years > 0.0 else 0.0
                self.row_good.append(numbers.get(good, -1))
                self.row_effect.append(effect)
                self.row_life.append(life)
                if life > 0.0:
                    place = place_of.setdefault(good, len(durables))
                    if place == len(durables):
                        durables.append(good)
                    self.row_held_place.append(place)
                else:
                    self.row_held_place.append(-1)
            self.row_start.append(len(self.row_good))
        self.durables.append(durables)
        self.need_start.append(len(self.need_floor))
        return found


def unmet_by_cohort(book, packed: PackedBaskets, agent_ids: Sequence[str], tiles: Sequence[str], people: Sequence[float],
                    basket_numbers: Sequence[int], receipt_start: np.ndarray, receipt_goods: np.ndarray,
                    receipt_amounts: np.ndarray) -> List[Dict[str, float]]:
    """`households_close.unmet_floor_by_need` for each cohort, in the order given (its id, tile and people): `basket_numbers` are `packed`'s
    numbers, the receipts the arrays of `receipts_with_grown` (cohorts in the same order). The held stocks of the durables are read from
    the book in one block."""
    count = len(agent_ids)
    held_start = np.zeros(count + 1, dtype=np.int64)
    held_agents, held_goods, held_tiles = [], [], []
    for position in range(count):
        durables = packed.durables[basket_numbers[position]]
        held_start[position + 1] = held_start[position] + len(durables)
        held_agents.extend([agent_ids[position]] * len(durables))
        held_goods.extend(durables)
        held_tiles.extend([tiles[position]] * len(durables))
    held = stock_block(book, numbers_of(book.agent_ids, held_agents), numbers_of(book.good_ids, held_goods), numbers_of(book.tile_ids, held_tiles))
    widest = max((len(basket.needs) for basket in packed.baskets), default=0)
    unmet = np.full((count, max(widest, 1)), np.nan)
    unmet_floors(np.array(people, dtype=np.float64), np.array(basket_numbers, dtype=np.int64), receipt_start,
                 receipt_goods, receipt_amounts, np.array(packed.need_start, dtype=np.int64), np.array(packed.need_floor, dtype=np.float64),
                 np.array(packed.row_start, dtype=np.int64), np.array(packed.row_good, dtype=np.int64), np.array(packed.row_effect, dtype=np.float64),
                 np.array(packed.row_life, dtype=np.float64), np.array(packed.row_held_place, dtype=np.int64), held_start, held,
                 len(book.good_ids), unmet)
    answers = []
    for position in range(count):
        basket = packed.baskets[basket_numbers[position]]
        row = unmet[position].tolist()
        answers.append({need.need_id: row[place] for place, need in enumerate(basket.needs) if row[place] == row[place]})
    return answers
