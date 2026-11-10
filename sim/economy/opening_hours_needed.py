"""Yearly hours each labour area's producers need of each trade for the runs they expect to sell, over arrays.

The producers' recipes are packed into a (recipe, trade) matrix of hours a run and the producers into the row of their
recipe, their area and their expected sales; one kernel adds sales times hours in producer order (the order the plain
loop used, so the sums are the same bits). The answer keeps the order the plain loop gave its dicts: areas and trades as
first met."""
from typing import Dict, List, Tuple

import numpy as np

from sim.jit import njit

NEVER = np.iinfo(np.int64).max


@njit
def hours_by_cell(row_of, area_of, sales, hours, listed, trade_count, area_count):
    """Sum over producers of sales times the row's hours, per (area, trade); `first` is, per cell, the position of the
    first producer to list that trade (producer position times the trade count plus the trade's place in its recipe)."""
    total = np.zeros((area_count, trade_count))
    first = np.full((area_count, trade_count), NEVER, dtype=np.int64)
    for producer in range(row_of.shape[0]):
        row = row_of[producer]
        area = area_of[producer]
        for slot in range(listed.shape[1]):
            trade = listed[row, slot]
            if trade < 0:
                break
            total[area, trade] += sales[producer] * hours[row, trade]
            key = producer * listed.shape[1] + slot
            if key < first[area, trade]:
                first[area, trade] = key
    return total, first


def of_producers(rows: List[Tuple[object, str, float]]) -> Dict[str, Dict[str, float]]:
    """`rows` are (recipe as practised, labour area, expected sales) in producer order; area -> trade -> hours."""
    recipe_index: Dict[int, int] = {}
    recipes: List[object] = []
    area_index: Dict[str, int] = {}
    row_of = np.empty(len(rows), dtype=np.int64)
    area_of = np.empty(len(rows), dtype=np.int64)
    sales = np.empty(len(rows))
    for position, (recipe, area, expected_sales) in enumerate(rows):
        row = recipe_index.get(id(recipe))
        if row is None:
            row = recipe_index[id(recipe)] = len(recipes)
            recipes.append(recipe)
        row_of[position] = row
        area_of[position] = area_index.setdefault(area, len(area_index))
        sales[position] = expected_sales
    trade_names = sorted({trade for recipe in recipes for trade in recipe.labour_hours})
    trade_index = {trade: index for index, trade in enumerate(trade_names)}
    width = max([len(recipe.labour_hours) for recipe in recipes] or [0])
    hours = np.zeros((max(1, len(recipes)), max(1, len(trade_names))))
    listed = np.full((max(1, len(recipes)), max(1, width)), -1, dtype=np.int64)
    for row, recipe in enumerate(recipes):
        for slot, (trade, per_run) in enumerate(recipe.labour_hours.items()):
            hours[row, trade_index[trade]] = per_run
            listed[row, slot] = trade_index[trade]
    if not rows:
        return {}
    total, first = hours_by_cell(row_of, area_of, sales, hours, listed, hours.shape[1], max(1, len(area_index)))
    result: Dict[str, Dict[str, float]] = {}
    for area, area_position in area_index.items():             # areas in the order the first producer met them
        met = sorted((int(first[area_position, trade]), trade) for trade in range(len(trade_names))
                     if first[area_position, trade] != NEVER)
        result[area] = {trade_names[trade]: float(total[area_position, trade]) for _key, trade in met}
    return result
