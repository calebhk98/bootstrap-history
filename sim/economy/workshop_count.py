"""How many independent workshops one producer stands for (Complaint 550), from the recipe's plant or its land.

A recipe's plant is physical: each `PlantPart` turns out `runs_per_year` runs a year (one kiln, press or loom), so one
workshop is one of each part and works as many runs a year as its smallest part allows. A producer's yearly runs over that
is the number of workshops it stands for, rounded to whole workshops, at least one. A recipe with no plant has nothing in
the data that bounds a workshop, so a producer of it counts one workshop and only entry (entry_year.py) adds to the count.

A plantless recipe on land has a household for its unit. A crop is worked in holdings: one workshop is the cropped land a
household of `PERSONS_PER_HOUSEHOLD` people needs to feed itself (`farmland_for_population`, from the farming year's labour and
harvest window). A herd is worked in herder-years: one workshop is the herd one herder's working year tends. A seam, pit or
quarry, and a wood, has no crew or holding size in the data, so it counts one workshop."""
import math
from typing import Dict, Mapping, Optional, Sequence

import numpy as np

from sim.world.agriculture import farmland_for_population
from sim.world.climate_needs import PERSONS_PER_HOUSEHOLD

from .types import PlantPart, Recipe

ARABLE_GROUND = "arable land"
PASTURE_GROUND = "pasture"


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


def household_holding_hectares() -> float:
    """Hectares a household of `PERSONS_PER_HOUSEHOLD` people crops to feed itself, at the farming domain's reference crop and toolkit."""
    return farmland_for_population(PERSONS_PER_HOUSEHOLD).hectares


def land_runs_per_workshop(ground: str, hours_per_run: float, land_per_run: float, holding_hectares: float,
                           working_hours_per_year: float) -> Optional[float]:
    """The runs one household's workshop works on land: a holding's worth of a crop, a herder's year of a herd; None for other ground."""
    if ground == ARABLE_GROUND and land_per_run > 0.0 and holding_hectares > 0.0:
        return holding_hectares / land_per_run
    if ground == PASTURE_GROUND and hours_per_run > 0.0 and working_hours_per_year > 0.0:
        return working_hours_per_year / hours_per_run
    return None


def runs_per_workshop_by_recipe(recipes: Mapping[str, Recipe], land_per_run: Mapping[str, float], holding_hectares: float,
                                working_hours_per_year: float) -> Dict[str, float]:
    """{recipe id: runs a year of one workshop}: by plant where the recipe has one, else by the household's land or herd."""
    sizes = {}
    for recipe_id, recipe in recipes.items():
        size = runs_per_workshop(recipe.plant_parts)
        if size is None:
            size = land_runs_per_workshop(recipe.ground, math.fsum(recipe.labour_hours.values()), land_per_run.get(recipe_id, 0.0),
                                          holding_hectares, working_hours_per_year)
        if size is not None:
            sizes[recipe_id] = size
    return sizes


def runs_per_workshop_of_setup(setup) -> Dict[str, float]:
    """`runs_per_workshop_by_recipe` for the setup's recipes, land and working year."""
    return runs_per_workshop_by_recipe(setup.recipes, setup.land_per_run, household_holding_hectares(), setup.working_hours_per_year)


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
