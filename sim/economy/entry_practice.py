"""The hours a newcomer's crew will need, for the entry decision. A new producer starts at the mean practice of the
recipe's other producers (practice.entrant_crew_runs) and learns on the runs it makes (practice.crew_runs_after_year),
so its first years book more hours than the recipe's. Entry weighs the years a producer is judged over before it
exits (LOSS_YEARS_BEFORE_EXIT, producers_close.py): the hours it plans on are the mean of those years' hours, so a
first year that loses and later years that pay enter when the years together pay, as exit would not close them
before then.
"""
import dataclasses
import math
from typing import Callable, List, Mapping, Sequence

from . import practice
from .producers_close import LOSS_YEARS_BEFORE_EXIT
from .types import Recipe

# recipe id -> the crew_runs of the recipe's existing producers
CrewsOf = Callable[[str], Sequence[Mapping[str, float]]]


def crews_of_recipe(producers: Mapping[str, object]) -> CrewsOf:
    """The crews of each recipe's producers in `producers` (a record's producers)."""
    def crews(recipe_id: str) -> List[Mapping[str, float]]:
        return [each.crew_runs for _name, each in sorted(producers.items()) if each.recipe_id == recipe_id]
    return crews


def first_year_recipe(recipe: Recipe, peers: Sequence[Mapping[str, float]]) -> Recipe:
    """The recipe at the hours an entrant's crew needs in its first year."""
    return practice.recipe_for(recipe, practice.entrant_crew_runs(recipe, peers))


def planned_recipe(recipe: Recipe, peers: Sequence[Mapping[str, float]], runs_per_year: float,
                   years: int = LOSS_YEARS_BEFORE_EXIT) -> Recipe:
    """The recipe with each trade's hours the mean of an entrant's hours over `years` years of `runs_per_year` runs,
    from the peers' mean practice; the recipe itself when it starts at the floor."""
    crew = practice.entrant_crew_runs(recipe, peers)
    if not crew:
        return recipe
    totals = {trade: [] for trade in recipe.labour_hours}
    for _year in range(max(1, years)):
        hours = practice.recipe_for(recipe, crew).labour_hours
        for trade in totals:
            totals[trade].append(hours[trade])
        crew = practice.crew_runs_after_year(crew, max(0.0, runs_per_year), 0.0, {})
    return dataclasses.replace(recipe, labour_hours={trade: math.fsum(each) / len(each) for trade, each in totals.items()})
