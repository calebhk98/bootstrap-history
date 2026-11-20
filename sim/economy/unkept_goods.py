"""Makers of goods that cannot be kept a year (bread, milk) under the clearing rules (rule_sets.py).

A maker of goods that keep is held by its stock: what it holds beyond its target takes runs off its plan, and the
market's price does the rest. A good that spoils within the year leaves no stock to read, so with nothing else to hold
it the plan follows the expected price alone, runs answer that price more than one for one near break-even, buyers of a
staple answer its price little, and output and price chase each other up and down in alternate years. So such a
maker's plan holds to its expected sales, and its expected sales follow the runs its takings would have sold at the
prices it expected: one that sold out dear grows, one that sold cheap shrinks, a share a year. Plain functions."""
import math
from typing import Mapping, Optional

import numpy as np


def cannot_be_kept(recipe, specs: Mapping[str, object]) -> bool:
    """Whether nothing the recipe makes keeps a year: every output has a spec and spoils whole within the year."""
    outputs = list(recipe.outputs)
    return bool(outputs) and all(good in specs and specs[good].spoilage_per_year >= 1.0 for good in outputs)


def recipes_that_cannot_be_kept(recipes: Mapping[str, object], specs: Mapping[str, object]) -> frozenset:
    """The ids of the recipes none of whose outputs keeps a year."""
    return frozenset(recipe_id for recipe_id, recipe in recipes.items() if cannot_be_kept(recipe, specs))


def stock_alone_where_kept(expected_sales: np.ndarray, output_cannot_be_kept: np.ndarray) -> np.ndarray:
    """The sales each producer's plan holds its runs to: none (NaN: its stock alone holds them, `plan_kernel.plan_rows`)
    for a maker of goods that keep, its expected sales for one whose goods do not."""
    return np.where(output_cannot_be_kept, expected_sales, np.nan)


def runs_its_takings_would_have_sold(takings: float, expected_takings_per_run: float) -> Optional[float]:
    """The runs a year's takings would have sold at the prices the maker expected; None where it expected a run to bring
    in nothing (or had no price to expect)."""
    if not expected_takings_per_run > 0.0 or not math.isfinite(expected_takings_per_run):
        return None
    return takings / expected_takings_per_run


def expected_sales_as_closed(closed: np.ndarray, _old, _takings, _expected_takings_per_run, _output_cannot_be_kept, _share) -> np.ndarray:
    """The expected sales the close worked out, for every producer."""
    return closed


def expected_sales_by_takings_where_unkept(closed: np.ndarray, old: np.ndarray, takings: np.ndarray, expected_takings_per_run: np.ndarray,
                                           output_cannot_be_kept: np.ndarray, share: float) -> np.ndarray:
    """Each producer's expected sales in runs after the year: for a maker of goods that do not keep, last year's moved
    `share` of the way to the runs its takings would have sold at the prices it expected (that figure whole where it
    expected no sales); the close's figure for every other, and where a run was expected to bring in nothing."""
    priced = np.isfinite(expected_takings_per_run) & (expected_takings_per_run > 0.0)
    sold = np.where(priced, takings / np.where(priced, expected_takings_per_run, 1.0), 0.0)
    moved = np.where(old <= 0.0, sold, old + share * (sold - old))
    return np.where(output_cannot_be_kept & priced, moved, closed)


def rows_that_cannot_be_kept(recipe_ids_by_row, recipe_row: np.ndarray, recipes: Mapping[str, object], specs: Mapping[str, object]) -> np.ndarray:
    """Per producer row, whether nothing its recipe makes keeps a year: `recipe_ids_by_row` are the recipe ids in the
    order the producers' `recipe_row` numbers them."""
    unkept = recipes_that_cannot_be_kept(recipes, specs)
    flags = np.array([recipe_id in unkept for recipe_id in recipe_ids_by_row], dtype=np.bool_)
    return flags[recipe_row] if len(flags) else np.zeros(len(recipe_row), dtype=np.bool_)


def outputs_by_slot(outputs: np.ndarray, slot_goods: np.ndarray, slot_is_output: np.ndarray, recipe_row: np.ndarray) -> np.ndarray:
    """Per producer row and slot, the units of the slot's good a run makes (nothing in a slot that is no output):
    `outputs` is recipes by goods, `slot_goods` and `slot_is_output` recipes by slots (a slot with no good holds a
    number under nothing)."""
    goods = slot_goods[recipe_row]
    made = outputs[recipe_row[:, None], np.maximum(goods, 0)]
    return np.where(slot_is_output[recipe_row] & (goods >= 0), made, 0.0)


def expected_takings_per_run(outputs_per_run: np.ndarray, expected_prices: np.ndarray, yield_factor: np.ndarray) -> np.ndarray:
    """Per producer row, what a run was expected to bring in: its outputs a run (rows by slots, nothing in a slot that
    is no output) at the prices it expected (NaN: none), times its yield."""
    return np.nansum(outputs_per_run * expected_prices, axis=1) * yield_factor
