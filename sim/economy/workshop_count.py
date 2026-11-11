"""How many independent workshops one producer stands for (Complaint 550), from the recipe's plant.

A recipe's plant is physical: each `PlantPart` turns out `runs_per_year` runs a year (one kiln, press or loom), so one
workshop is one of each part and works as many runs a year as its smallest part allows. A producer's yearly runs over that
is the number of workshops it stands for, rounded to whole workshops, at least one. A recipe with no plant has nothing in
the data that bounds a workshop, so a producer of it counts one workshop and only entry (entry_year.py) adds to the count."""
import math
from typing import Dict, Mapping, Optional, Sequence

import numpy as np

from .types import PlantPart, Recipe


def runs_per_workshop(plant_parts: Sequence[PlantPart]) -> Optional[float]:
    """The runs a year one workshop's plant turns out (its smallest part's); None for a recipe with no plant."""
    runs = [part.runs_per_year for part in plant_parts if part.runs_per_year > 0.0]
    return min(runs) if runs else None


def workshops_for_runs(runs: float, plant_parts: Sequence[PlantPart]) -> int:
    """The whole workshops that make `runs` runs a year with the recipe's plant, at least one; one for a recipe with no plant."""
    per_workshop = runs_per_workshop(plant_parts)
    if per_workshop is None or not runs > 0.0:
        return 1
    return max(1, int(math.floor(runs / per_workshop + 0.5)))


def runs_per_workshop_by_recipe(recipes: Mapping[str, Recipe]) -> Dict[str, float]:
    """{recipe id: runs a year of one workshop} for the recipes that have a plant."""
    sizes = {recipe_id: runs_per_workshop(recipe.plant_parts) for recipe_id, recipe in recipes.items()}
    return {recipe_id: size for recipe_id, size in sizes.items() if size is not None}


def refresh_workshops(store, per_workshop_by_recipe: Mapping[str, float]) -> None:
    """Each producer of a recipe with a plant takes the workshop count its capacity implies; a producer of any other recipe keeps its count.
    Called wherever capacity is written in bulk (the opening, the year's close), so a shrunk producer does not keep a count from its past size."""
    if not per_workshop_by_recipe:
        return
    table = store.table
    rows = store.order()
    if not len(rows):
        return
    names = store.names["recipes"].name_list
    per_workshop = np.array([per_workshop_by_recipe.get(name, np.nan) for name in names])[table.recipe[rows]]
    has_plant = ~np.isnan(per_workshop)
    capacity = table.capacity_runs[rows]
    counted = np.maximum(1, np.floor(capacity / np.where(has_plant, per_workshop, 1.0) + 0.5)).astype(np.int64)
    new = np.where(has_plant, np.where(capacity > 0.0, counted, 1), table.workshops[rows])
    changed = new != table.workshops[rows]
    if changed.any():
        table.workshops[rows] = new
        store.written(rows[changed])
