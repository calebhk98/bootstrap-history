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
from typing import Dict, Mapping, Optional, Sequence

from sim.world.need_basket import PricedNeed
from sim.world.shared_constants import LABOUR_OUTPUT_ELASTICITY

from .households_basket import tile_need_prices
from .priced_need_list import priced_needs_of
from . import cohort_prime, household_work_year, land_bid, titles_plots
from .cohort_store import table_of
from .households_own import Option


def _grown(priced: Sequence[PricedNeed], options: Mapping[str, Sequence[Option]], fertility: float,
           people_per_worker: float, hectares_per_hour: Mapping[str, float]) -> list:
    """(price, hectares, hectares per need unit, reference hours per hectare) of each need the plot grows for a worker's household."""
    grown = []
    for spec, price_index, _first, _end in priced_needs_of(priced).blocks():
        rows = options.get(spec.need_id)
        if not rows or rows[0][0] <= 0.0:
            continue
        per_hour = hectares_per_hour.get(rows[0][1], 0.0)
        if per_hour <= 0.0:
            continue
        per_unit = per_hour * rows[0][0]
        grown.append((price_index, spec.subsistence_per_person * people_per_worker * per_unit, per_unit,
                      1.0 / (fertility * per_hour)))
    return grown


def plot_value_per_worker_year(priced: Sequence[PricedNeed], options: Mapping[str, Sequence[Option]],
                               fertility: float, hours_per_worker_year: float, people_per_worker: float,
                               hectares_per_hour: Optional[Mapping[str, float]] = None,
                               hectares_held: Optional[float] = None) -> float:
    """Money a worker's family gets a year from its plot, at the prices of the needs it grows: the floors of
    the needs the plot can grow, limited by the hours one worker's year can put into it and, when `hectares_held`
    is given, by the land the worker has (the share of the plot's land held)."""
    if fertility <= 0.0 or hours_per_worker_year <= 0.0:
        return 0.0
    value_per_person = hours_per_person = 0.0
    for spec, price_index, _first, _end in priced_needs_of(priced).blocks():
        rows = options.get(spec.need_id)
        if not rows:
            continue
        value_per_person += price_index * spec.subsistence_per_person
        hours_per_person += spec.subsistence_per_person * rows[0][0] / fertility
    if hours_per_person <= 0.0:
        return 0.0
    value = min(value_per_person * people_per_worker, value_per_person / hours_per_person * hours_per_worker_year)
    if hectares_held is not None and hectares_per_hour is not None:
        plot = math.fsum(row[1] for row in _grown(priced, options, fertility, people_per_worker, hectares_per_hour))
        if plot > 0.0:
            value *= min(1.0, max(0.0, hectares_held) / plot)
    return value


def plot_return_per_hour(priced: Sequence[PricedNeed], options: Mapping[str, Sequence[Option]],
                         fertility: float, hours_per_worker_year: float, people_per_worker: float,
                         hectares_per_hour: Mapping[str, float], hectares_held: Optional[float] = None) -> float:
    """Money the next hour on the family's plot adds, with the worker's year of hours on it. `hectares_held`, when
    given and less than the land the floors take, is the land the worker has: the hours are worked on that.

    `hectares_per_hour` is the land by recipe that one hour of its work takes at the recipe's own intensity.
    The plot is the land that grows the floors of the needs it can (households_own.own_production_options),
    for the worker and the people he supports. Hours per hectare on it is the year over that land; a need's
    yield per hectare is its reference yield times (hours per hectare over the reference hours) to the
    labour elasticity, and the next hour adds elasticity times yield over hours per hectare, in need units at
    the need's price. Needs weigh by the land they take."""
    if fertility <= 0.0 or hours_per_worker_year <= 0.0:
        return 0.0
    grown = _grown(priced, options, fertility, people_per_worker, hectares_per_hour)
    plot = math.fsum(row[1] for row in grown)
    if plot <= 0.0:
        return 0.0
    worked = plot if hectares_held is None else min(plot, hectares_held)
    if worked <= 0.0:
        return 0.0
    hours_per_hectare = hours_per_worker_year / worked
    elasticity = LABOUR_OUTPUT_ELASTICITY
    total = 0.0
    for price, hectares, per_unit, reference_hours in grown:
        yield_per_hectare = (hours_per_hectare / reference_hours) ** elasticity / per_unit
        total += hectares * price * elasticity * yield_per_hectare / hours_per_hectare
    return total / plot


def survival_cost_per_worker_year(priced: Sequence[PricedNeed], options: Mapping[str, Sequence[Option]],
                                  fertility: float, hours_per_worker_year: float, people_per_worker: float,
                                  hectares_per_hour: Optional[Mapping[str, float]] = None,
                                  hectares_held: Optional[float] = None) -> float:
    """Money a worker must earn a year to keep his household fed and clothed: its floors for every need at
    these prices, less what the plot gives when his year goes into it; never below nothing."""
    household_cost = priced_needs_of(priced).subsistence_cost_per_person() * people_per_worker
    plot = plot_value_per_worker_year(priced, options, fertility, hours_per_worker_year, people_per_worker,
                                      hectares_per_hour, hectares_held)
    return max(0.0, household_cost - plot)


def wage_floor_per_worker_year(priced: Sequence[PricedNeed], options: Mapping[str, Sequence[Option]],
                               fertility: float, hours_per_worker_year: float, people_per_worker: float,
                               hectares_per_hour: Mapping[str, float], hectares_held: Optional[float] = None) -> float:
    """The least a worker sells his year for: the greater of what the hours would add on the plot
    (plot_return_per_hour) and what his household needs to stay fed beyond what the plot gives, both on the land
    he holds (`hectares_held`, per worker; None: the whole plot)."""
    opportunity = plot_return_per_hour(priced, options, fertility, hours_per_worker_year, people_per_worker,
                                       hectares_per_hour, hectares_held) * max(0.0, hours_per_worker_year)
    return max(opportunity, survival_cost_per_worker_year(priced, options, fertility, hours_per_worker_year,
                                                          people_per_worker, hectares_per_hour, hectares_held))


def hectares_per_hour_by_recipe(recipes, land_per_run: Mapping[str, float]) -> Dict[str, float]:
    """Land one hour of each recipe's work takes at the recipe's own intensity."""
    per_hour: Dict[str, float] = {}
    for recipe_id, recipe in recipes.items():
        hours_per_hectare = land_bid.hours_per_hectare(recipe, land_per_run.get(recipe_id, 0.0))
        if hours_per_hectare > 0.0:
            per_hour[recipe_id] = 1.0 / hours_per_hectare
    return per_hour


def ask_floor_by_tile(setup, record, view, options: Mapping[str, Sequence[Option]]) -> Dict[str, float]:
    """Per tile, the wage floor of one worker (wage_floor_per_worker_year): each cohort's, on the land it holds
    (titles_plots.hectares_held, as the hours schedule reads it), averaged by working people."""
    floors: Dict[str, float] = {}
    hectares_per_hour = hectares_per_hour_by_recipe(setup.recipes, setup.land_per_run)
    held = titles_plots.hectares_held(setup, record)
    cohort_prime.prime_cohort_baskets(setup, record, view, False)
    store = table_of(record.cohorts)
    for tile in sorted(store.tiles_present()):
        rows = store.rows_on_tile(tile)
        rows = rows[store.column("working_people")[rows] > 0.0]            # the tile's cohorts that have workers, in table order
        tile_data = setup.tiles.get(tile)
        fertility = tile_data.fertility if tile_data else 0.0
        working_people, people = store.floats("working_people", rows), store.floats("people", rows)
        working = sum(working_people)
        if working <= 0.0:
            floors[tile] = wage_floor_per_worker_year(tile_need_prices(setup, view, tile), options, fertility, setup.working_hours_per_year, 1.0,
                                                      hectares_per_hour, 0.0)
            continue
        signatures = household_work_year.signatures_of(record, store, rows, buying=False)
        floors[tile] = sum(working_people[place] * wage_floor_per_worker_year(
            household_work_year.priced_basket_of(setup, view, tile, signatures[place]), options, fertility, setup.working_hours_per_year,
            people[place] / working_people[place], hectares_per_hour, held.get(store.ids[row], 0.0) / working_people[place])
            for place, row in enumerate(rows.tolist())) / working
    return floors


def mean_floor_per_hour(floor_by_area: Mapping[str, float], workers_by_area: Mapping[str, float],
                        hours_per_worker_year: float) -> float:
    """The wage floor per hour averaged over areas, weighted by their workers (for the run's figures)."""
    total = sum(workers_by_area.get(area, 0.0) for area in floor_by_area)
    if total <= 0.0 or hours_per_worker_year <= 0.0:
        return 0.0
    return sum(floor * workers_by_area.get(area, 0.0) for area, floor in floor_by_area.items()) / (
        total * hours_per_worker_year)
