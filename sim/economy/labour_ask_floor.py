"""The lowest a worker's ask falls to: what the family has without selling a single hour.

Hours nobody hires go into the household's own plot (households_own.py), which grows the floors of the
needs its land-only recipes can serve. So a worker whose family can feed itself from its plot does not need
a wage to eat and sells hours for whatever they fetch, while a family with no land asks at least what the
plot would have given it. A family with nothing else (no plot, no savings) has no floor under its ask; it
sells cheaper until it is hired or goes short, and the shortfall is what the population model reads.
"""
from typing import Dict, Mapping, Sequence

from sim.world.need_basket import PricedNeed

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


def ask_floor_by_tile(setup, record, view, options: Mapping[str, Sequence[Option]]) -> Dict[str, float]:
    """Per tile, the plot's yearly value to one worker's family (plot_value_per_worker_year)."""
    floors: Dict[str, float] = {}
    for tile in sorted({cohort.tile for cohort in record.cohorts.values()}):
        people = sum(cohort.people for cohort in record.cohorts.values() if cohort.tile == tile)
        working = sum(cohort.working_people for cohort in record.cohorts.values() if cohort.tile == tile)
        tile_data = setup.tiles.get(tile)
        priced = need_prices(setup.basket_for(tile), view, tile)
        floors[tile] = plot_value_per_worker_year(
            priced, options, tile_data.fertility if tile_data else 0.0, setup.working_hours_per_year,
            people / working if working > 0.0 else 1.0)
    return floors
