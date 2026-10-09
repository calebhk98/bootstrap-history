"""The lowest a worker's ask falls to: what keeping his household alive and working costs, less what the
family's own plot gives it.

The household's costs are the floors of every need in the basket (food, shelter, clothing, fuel) at the
tile's prices, for the worker and the people he supports. Hours nobody hires go into the household's own
plot (households_own.py), which grows the floors of the needs its land-only recipes can serve, so a family
that feeds itself needs a wage only for the rest. Below that wage people leave the trade, move on or go
short, rather than keep selling hours; the shortfall is what the population model reads.
"""
from typing import Dict, Mapping, Sequence

from sim.world.need_basket import PricedNeed, subsistence_cost_per_person

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


def wage_floor_per_worker_year(priced: Sequence[PricedNeed], options: Mapping[str, Sequence[Option]],
                               fertility: float, hours_per_worker_year: float, people_per_worker: float) -> float:
    """Money a worker must earn a year: his household's floors for every need at these prices, less what
    its plot gives (plot_value_per_worker_year); never below nothing."""
    household_cost = subsistence_cost_per_person(priced) * people_per_worker
    plot = plot_value_per_worker_year(priced, options, fertility, hours_per_worker_year, people_per_worker)
    return max(0.0, household_cost - plot)


def ask_floor_by_tile(setup, record, view, options: Mapping[str, Sequence[Option]]) -> Dict[str, float]:
    """Per tile, the wage floor of one worker (wage_floor_per_worker_year)."""
    floors: Dict[str, float] = {}
    for tile in sorted({cohort.tile for cohort in record.cohorts.values()}):
        people = sum(cohort.people for cohort in record.cohorts.values() if cohort.tile == tile)
        working = sum(cohort.working_people for cohort in record.cohorts.values() if cohort.tile == tile)
        tile_data = setup.tiles.get(tile)
        priced = need_prices(setup.basket_for(tile), view, tile)
        floors[tile] = wage_floor_per_worker_year(
            priced, options, tile_data.fertility if tile_data else 0.0, setup.working_hours_per_year,
            people / working if working > 0.0 else 1.0)
    return floors


def mean_floor_per_hour(floor_by_area: Mapping[str, float], workers_by_area: Mapping[str, float],
                        hours_per_worker_year: float) -> float:
    """The wage floor per hour averaged over areas, weighted by their workers (for the run's figures)."""
    total = sum(workers_by_area.get(area, 0.0) for area in floor_by_area)
    if total <= 0.0 or hours_per_worker_year <= 0.0:
        return 0.0
    return sum(floor * workers_by_area.get(area, 0.0) for area, floor in floor_by_area.items()) / (
        total * hours_per_worker_year)
