"""The lowest a worker's ask falls to: what an hour is worth on the household's own plot.

An hour sold is an hour not spent on the plot (households_own.py), so the least a household accepts for it is
the output the next hour would add there, at the prices of the tile. The plot is the land that grows the
family's floors; the worker's year of hours spread over it sets how hard it is worked, and output on fixed
land rises with hours to the labour elasticity (world/land.py's intensive margin), so the next hour adds the
elasticity times the output per hour at that intensity. A family with plenty of hours per hectare gets little
from one more, which is why a worker with idle hours takes little for them; a plot that grows nothing
leaves only what the family needs beyond the plot to keep it fed.
"""
import math
from typing import Dict, Mapping, Sequence

from sim.world.need_basket import PricedNeed, subsistence_cost_per_person
from sim.world.shared_constants import LABOUR_OUTPUT_ELASTICITY

from .households_basket import need_prices
from .households_own import Option


def plot_value_per_worker_year(priced: Sequence[PricedNeed], options: Mapping[str, Sequence[Option]],
                               fertility: float, hours_per_worker_year: float, people_per_worker: float) -> float:
    """Money a worker's family gets a year from its plot, at the prices of the needs it grows: the floors of
    the needs the plot can grow, limited by the hours one worker's year can put into it."""
    if fertility <= 0.0 or hours_per_worker_year <= 0.0:
        return 0.0
    value_per_person = hours_per_person = 0.0
    for need in priced:
        rows = options.get(need.spec.need_id)
        if not rows:
            continue
        value_per_person += need.price_index * need.spec.subsistence_per_person
        hours_per_person += need.spec.subsistence_per_person * rows[0][0] / fertility
    if hours_per_person <= 0.0:
        return 0.0
    return min(value_per_person * people_per_worker, value_per_person / hours_per_person * hours_per_worker_year)


def plot_return_per_hour(priced: Sequence[PricedNeed], options: Mapping[str, Sequence[Option]],
                         fertility: float, hours_per_worker_year: float, people_per_worker: float,
                         hectares_per_hour: Mapping[str, float]) -> float:
    """Money the next hour on the family's plot adds, with the worker's year of hours on it.

    `hectares_per_hour` is the land by recipe that one hour of its work takes at the recipe's own intensity.
    The plot is the land that grows the floors of the needs it can (households_own.own_production_options),
    for the worker and the people he supports. Hours per hectare on it is the year over that land; a need's
    yield per hectare is its reference yield times (hours per hectare over the reference hours) to the
    labour elasticity, and the next hour adds elasticity times yield over hours per hectare, in need units at
    the need's price. Needs weigh by the land they take."""
    if fertility <= 0.0 or hours_per_worker_year <= 0.0:
        return 0.0
    grown = []        # (price, hectares, hectares per need unit, reference hours per hectare)
    for need in priced:
        rows = options.get(need.spec.need_id)
        if not rows or rows[0][0] <= 0.0:
            continue
        per_hour = hectares_per_hour.get(rows[0][1], 0.0)
        if per_hour <= 0.0:
            continue
        per_unit = per_hour * rows[0][0]
        hectares = need.spec.subsistence_per_person * people_per_worker * per_unit
        grown.append((need.price_index, hectares, per_unit, 1.0 / (fertility * per_hour)))
    plot = math.fsum(row[1] for row in grown)
    if plot <= 0.0:
        return 0.0
    hours_per_hectare = hours_per_worker_year / plot
    elasticity = LABOUR_OUTPUT_ELASTICITY
    total = 0.0
    for price, hectares, per_unit, reference_hours in grown:
        yield_per_hectare = (hours_per_hectare / reference_hours) ** elasticity / per_unit
        total += hectares * price * elasticity * yield_per_hectare / hours_per_hectare
    return total / plot


def survival_cost_per_worker_year(priced: Sequence[PricedNeed], options: Mapping[str, Sequence[Option]],
                                  fertility: float, hours_per_worker_year: float, people_per_worker: float) -> float:
    """Money a worker must earn a year to keep his household fed and clothed: its floors for every need at
    these prices, less what the plot gives when his year goes into it; never below nothing."""
    household_cost = subsistence_cost_per_person(priced) * people_per_worker
    plot = plot_value_per_worker_year(priced, options, fertility, hours_per_worker_year, people_per_worker)
    return max(0.0, household_cost - plot)


def wage_floor_per_worker_year(priced: Sequence[PricedNeed], options: Mapping[str, Sequence[Option]],
                               fertility: float, hours_per_worker_year: float, people_per_worker: float,
                               hectares_per_hour: Mapping[str, float]) -> float:
    """The least a worker sells his year for: the greater of what the hours would add on the plot
    (plot_return_per_hour) and what his household needs to stay fed beyond what the plot gives."""
    opportunity = plot_return_per_hour(priced, options, fertility, hours_per_worker_year, people_per_worker,
                                       hectares_per_hour) * max(0.0, hours_per_worker_year)
    return max(opportunity, survival_cost_per_worker_year(priced, options, fertility, hours_per_worker_year,
                                                          people_per_worker))


def hectares_per_hour_by_recipe(recipes, land_per_run: Mapping[str, float]) -> Dict[str, float]:
    """Land one hour of each recipe's work takes at the recipe's own intensity."""
    per_hour: Dict[str, float] = {}
    for recipe_id, recipe in recipes.items():
        hours = math.fsum(recipe.labour_hours.values())
        if hours > 0.0 and land_per_run.get(recipe_id, 0.0) > 0.0:
            per_hour[recipe_id] = land_per_run[recipe_id] / hours
    return per_hour


def ask_floor_by_tile(setup, record, view, options: Mapping[str, Sequence[Option]]) -> Dict[str, float]:
    """Per tile, the wage floor of one worker (wage_floor_per_worker_year)."""
    floors: Dict[str, float] = {}
    hectares_per_hour = hectares_per_hour_by_recipe(setup.recipes, setup.land_per_run)
    for tile in sorted({cohort.tile for cohort in record.cohorts.values()}):
        people = sum(cohort.people for cohort in record.cohorts.values() if cohort.tile == tile)
        working = sum(cohort.working_people for cohort in record.cohorts.values() if cohort.tile == tile)
        tile_data = setup.tiles.get(tile)
        priced = need_prices(setup.basket_for(tile), view, tile)
        floors[tile] = wage_floor_per_worker_year(
            priced, options, tile_data.fertility if tile_data else 0.0, setup.working_hours_per_year,
            people / working if working > 0.0 else 1.0, hectares_per_hour)
    return floors


def mean_floor_per_hour(floor_by_area: Mapping[str, float], workers_by_area: Mapping[str, float],
                        hours_per_worker_year: float) -> float:
    """The wage floor per hour averaged over areas, weighted by their workers (for the run's figures)."""
    total = sum(workers_by_area.get(area, 0.0) for area in floor_by_area)
    if total <= 0.0 or hours_per_worker_year <= 0.0:
        return 0.0
    return sum(floor * workers_by_area.get(area, 0.0) for area, floor in floor_by_area.items()) / (
        total * hours_per_worker_year)
