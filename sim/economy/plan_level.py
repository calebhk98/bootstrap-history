"""The cost a producer's plan judges whether to work on: the level pair of a crew still learning.

`producers.plan` and `plan_kernel.plan_rows` choose the share of workplaces that work from a run's revenue and variable cost. For a crew
still learning those are taken at the hours multipliers and usable share averaged over the learning path (`practice_path`), not at this
year's, so a new crew whose first year loses but whose practised years pay still runs and so practises. Everything that pays or bids
stays on this year's practised hours and yield. A crew at the floor has no level pair apart from the plan's own.
"""
import dataclasses
from typing import Callable, Dict, Mapping, Tuple

import numpy as np

from . import practice, practice_path, unit_cost
from .types import Recipe


def level_figures(recipe: Recipe, crew_runs: Mapping[str, float], capacity_runs: float, workshops: int,
                  rate) -> Tuple[Dict[str, float], float]:
    """(each of the recipe's trades' level hours multiplier, the level usable share) of a crew: the pace is the capacity per workshop,
    the horizon the plant's life or `YEARS_A_WORKSHOP_EXPECTS_TO_KEEP_A_TRADE`, the discount the market rate (none: no discount)."""
    pace = max(0.0, capacity_runs) / max(1, workshops)
    return practice_path.learning_path_scales(crew_runs, recipe.labour_hours, pace, practice_path.horizon_years(recipe.plant_life_years),
                                              0.0 if rate is None else rate)


def level_recipe(recipe: Recipe, multipliers: Mapping[str, float]) -> Recipe:
    """The booked recipe with each trade's hours times its level multiplier."""
    return dataclasses.replace(recipe, labour_hours={trade: hours * multipliers.get(trade, 1.0) for trade, hours in recipe.labour_hours.items()})


def level_share_working(recipe: Recipe, crew_runs: Mapping[str, float], capacity_runs: float, workshops: int, rate, base_yield_factor: float,
                        outputs: Mapping[str, float], inputs: Mapping[str, float], wages: Mapping[str, float], rent: float,
                        share_working: Callable[[float, float], float]) -> float:
    """Share of the producer's workplaces that work, judged on the level pair: revenue at the level usable share of the base yield factor
    and variable cost (inputs, wages, rent) at the level hours, by `share_working` (`producers.share_working`). `base_yield_factor` is
    the producer's own, before the spoilage of this year's practice."""
    multipliers, usable = level_figures(recipe, crew_runs, capacity_runs, workshops, rate)
    leveled = level_recipe(recipe, multipliers)
    revenue = unit_cost.revenue_per_run(leveled, outputs) * base_yield_factor * usable
    variable = (unit_cost.input_cost_per_run(leveled, inputs, wages) + unit_cost.labour_cost_per_run(leveled, wages) + rent)
    return share_working(revenue, variable)


def level_columns(columns, recipes: Mapping[str, Recipe], rate_of_row: Callable[[int], object]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(level hours scale by producer and trade column, level usable share by producer, whether the producer's crew is still learning)
    for the kernel: the figures of `level_figures` for each producer with a crew, ones elsewhere. `rate_of_row` is the market rate
    of the producer's row."""
    count = len(columns.ids)
    scale = np.ones_like(columns.hours_scale)
    usable = np.ones(count)
    learning = np.zeros(count, dtype=bool)
    trade_row = columns.matrices.trades.row
    recipe_ids = columns.matrices.recipes.ids
    for position, crew in columns.crews.items():
        recipe = recipes[recipe_ids[columns.recipe_row[position]]]
        multipliers, share = level_figures(recipe, crew, float(columns.capacity_runs[position]), int(columns.workshops[position]),
                                           rate_of_row(position))
        for trade, multiplier in multipliers.items():
            scale[position, trade_row[trade]] = multiplier
        usable[position] = share
        learning[position] = True
    return scale, usable, learning
