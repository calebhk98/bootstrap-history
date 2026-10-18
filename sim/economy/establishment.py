"""How many independent establishments a recipe's capacity on one tile stands for (Complaint 550).

A recipe may state `establishment_workers`, the crew of one workshop, farm or mine gang. One establishment
then works `workers * HOURS_PER_PERSON_YEAR / labour hours per run` runs a year; capacity beyond that is
more owners. A recipe without the figure has no datum for its size, so its capacity counts as one."""
import math

from sim.unit_conversions import HOURS_PER_PERSON_YEAR

from .types import Recipe


def runs_per_establishment(recipe: Recipe) -> float:
    """Runs a year one establishment works; 0.0 when the recipe states no crew (or needs no labour)."""
    hours_per_run = math.fsum(recipe.labour_hours.values())
    if recipe.establishment_workers <= 0.0 or hours_per_run <= 0.0:
        return 0.0
    return recipe.establishment_workers * HOURS_PER_PERSON_YEAR / hours_per_run


def workshops_for(recipe: Recipe, runs: float) -> int:
    """Independent establishments that `runs` a year stand for: at least one."""
    size = runs_per_establishment(recipe)
    if size <= 0.0 or runs <= size:
        return 1
    return max(1, int(round(runs / size)))
