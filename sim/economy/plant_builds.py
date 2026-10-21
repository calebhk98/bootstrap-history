"""Which way a recipe's plant is built from what the society has: each part's preferred build when its
materials are there, else the next alternative the data names. Nothing here names a good or a recipe."""
import dataclasses
from typing import Container

from .recipes import fold_plant
from .types import GoodId, PlantBuild, PlantPart, Recipe


def chosen_build(part: PlantPart, available: Container[GoodId]):
    """The first build of `part` whose materials are all available, or None."""
    return next((build for build in part.builds if all(good in available for good in build.goods)), None)


def buildable(recipe: Recipe, available: Container[GoodId]) -> bool:
    """Whether every part of the recipe's plant has a build the society can supply."""
    return all(chosen_build(part, available) is not None for part in recipe.plant_parts)


def with_plant_from(recipe: Recipe, available: Container[GoodId]) -> Recipe:
    """The recipe with its plant folded from the first buildable alternative of each part (the preferred build
    where none is buildable, so the shortfall stays visible)."""
    if not recipe.plant_parts:
        return recipe
    chosen = [(part.runs_per_year, chosen_build(part, available) or part.builds[0]) for part in recipe.plant_parts]
    goods, hours, life = fold_plant(chosen)
    return dataclasses.replace(recipe, plant_goods=goods, plant_labour_hours=hours, plant_life_years=life)
