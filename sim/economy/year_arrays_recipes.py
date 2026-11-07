"""The recipes as matrices: what a run takes in and makes, by recipe row and good (or trade) column.

Rows follow the sorted recipe ids and columns the sorted good or trade ids, so a sum over a row is a fixed-order sum.
`slot_goods` / `slot_trades` list, for each recipe, the columns that recipe touches (sorted, `-1` padding), so a kernel
walks a few slots, not every good."""
from dataclasses import dataclass
from typing import Dict, Mapping, Sequence, Tuple

import numpy as np

from . import idle_capacity

NO_SLOT = -1


@dataclass(frozen=True)
class Names:
    """Sorted ids and their positions."""
    ids: Tuple[str, ...]
    row: Mapping[str, int]

    @classmethod
    def of(cls, ids) -> "Names":
        ordered = tuple(sorted(set(ids)))
        return cls(ordered, {name: position for position, name in enumerate(ordered)})


@dataclass(frozen=True)
class RecipeMatrices:
    recipes: Names
    goods: Names
    trades: Names
    inputs: np.ndarray               # recipe by good: units a run uses up
    outputs: np.ndarray              # recipe by good: units a run makes
    plant_goods: np.ndarray          # recipe by good: units of plant a year of one run's capacity ties up
    labour_hours: np.ndarray         # recipe by trade: hours a run takes
    plant_labour_hours: np.ndarray   # recipe by trade: hours building a run's capacity takes
    plant_life_years: np.ndarray
    idle_wear_share: np.ndarray      # share of idle capacity that wears out in a year (idle_capacity.wear_share_per_year)
    first_output: np.ndarray         # the good (column) that sorts first among the recipe's outputs
    slot_goods: np.ndarray           # recipe by slot: good column, NO_SLOT padded
    slot_trades: np.ndarray          # recipe by slot: trade column, NO_SLOT padded
    slot_is_input: np.ndarray        # recipe by good slot: whether the good is a key of the recipe's inputs
    slot_is_output: np.ndarray
    slot_is_plant: np.ndarray

    @property
    def good_slots(self) -> int:
        return self.slot_goods.shape[1]


def goods_and_trades_of(recipes: Mapping[str, object], extra_goods: Sequence[str] = ()) -> Tuple[Names, Names]:
    goods = set(extra_goods)
    trades = set()
    for recipe in recipes.values():
        goods.update(recipe.inputs)
        goods.update(recipe.outputs)
        goods.update(recipe.plant_goods)
        trades.update(recipe.labour_hours)
        trades.update(recipe.plant_labour_hours)
    return Names.of(goods), Names.of(trades)


def _fill(matrix: np.ndarray, row: int, quantities: Mapping[str, float], columns: Mapping[str, int]) -> None:
    for name, quantity in quantities.items():
        matrix[row, columns[name]] = quantity


def _slots(columns: Sequence[Sequence[int]], width: int) -> np.ndarray:
    slots = np.full((len(columns), max(1, width)), NO_SLOT, dtype=np.int64)
    for row, used in enumerate(columns):
        slots[row, :len(used)] = sorted(used)
    return slots


def build_recipe_matrices(recipes: Mapping[str, object], service_lives: Mapping[str, float],
                          extra_goods: Sequence[str] = ()) -> RecipeMatrices:
    goods, trades = goods_and_trades_of(recipes, extra_goods)
    names = Names.of(recipes)
    count = len(names.ids)
    shape_goods, shape_trades = (count, len(goods.ids)), (count, len(trades.ids))
    inputs, outputs, plant_goods = np.zeros(shape_goods), np.zeros(shape_goods), np.zeros(shape_goods)
    labour, plant_labour = np.zeros(shape_trades), np.zeros(shape_trades)
    life, wear, first = np.zeros(count), np.zeros(count), np.zeros(count, dtype=np.int64)
    used_goods, used_trades = [], []
    keys = []
    for row, recipe_id in enumerate(names.ids):
        recipe = recipes[recipe_id]
        _fill(inputs, row, recipe.inputs, goods.row)
        _fill(outputs, row, recipe.outputs, goods.row)
        _fill(plant_goods, row, recipe.plant_goods, goods.row)
        _fill(labour, row, recipe.labour_hours, trades.row)
        _fill(plant_labour, row, recipe.plant_labour_hours, trades.row)
        life[row] = recipe.plant_life_years
        wear[row] = idle_capacity.wear_share_per_year(recipe, service_lives)
        first[row] = goods.row[min(recipe.outputs)] if recipe.outputs else NO_SLOT
        keys.append((set(recipe.inputs), set(recipe.outputs), set(recipe.plant_goods)))
        used_goods.append([goods.row[good] for good in set(recipe.inputs) | set(recipe.outputs) | set(recipe.plant_goods)])
        used_trades.append([trades.row[trade] for trade in set(recipe.labour_hours) | set(recipe.plant_labour_hours)])
    slot_goods = _slots(used_goods, max((len(used) for used in used_goods), default=0))
    masks = [np.zeros(slot_goods.shape, dtype=bool) for _kind in range(3)]
    for row, (taken, made, planted) in enumerate(keys):
        for slot, column in enumerate(slot_goods[row]):
            if column != NO_SLOT:
                good = goods.ids[column]
                masks[0][row, slot], masks[1][row, slot], masks[2][row, slot] = good in taken, good in made, good in planted
    return RecipeMatrices(names, goods, trades, inputs, outputs, plant_goods, labour, plant_labour, life, wear, first,
                          slot_goods, _slots(used_trades, max((len(used) for used in used_trades), default=0)), *masks)
