"""What households grow for themselves at the opening, by the rule a year applies.

In a year the hours nobody hires go into the household's own plot (households_own.own_production) and the
floors that grows are not bought (year_goods._less_what_it_grew). At the opening nobody has hired yet: the
producers are sized to what is left to buy, and they hire part of the offered hours, so the rest are idle.
The two depend on each other; the opening iterates them with its income (opening._settle_income) and
`idle_share` carries the answer between passes.
"""
import math
from typing import Mapping

from . import households_own
from .year_goods import _less_what_it_grew

# The idle share moves this far toward its new value each pass, so the demand and the hiring it implies settle
# instead of swinging between grown-everything and grown-nothing. A numerical damping, not a model parameter.
IDLE_SHARE_STEP = 0.5


def own_options(setup):
    return households_own.own_production_options(setup.recipes, setup.land_per_run, setup.basket)


def less_what_it_grew(setup, cohort, orders, options, idle_share: float):
    """The cohort's orders without the floors its idle hours grow on its own tile, as a year cuts them."""
    if idle_share <= 0.0 or not options:
        return orders
    tile = setup.tiles.get(cohort.tile)
    idle_hours = idle_share * cohort.working_people * setup.working_hours_per_year
    _moves, _grown, units = households_own.own_production(
        cohort, idle_hours, options, setup.recipes, tile.fertility if tile else 0.0, setup.basket_for(cohort.tile))
    return _less_what_it_grew(orders, cohort, setup.basket_for(cohort.tile), units)


def idle_share_after(setup, record, runs: Mapping[str, float], previous: float) -> float:
    """The share of offered hours the producers sized to `runs` leave unhired, moved toward from `previous`."""
    offered = math.fsum(cohort.working_people for cohort in record.cohorts.values()) * setup.working_hours_per_year
    if offered <= 0.0:
        return 0.0
    hired = math.fsum(count * math.fsum(setup.recipes[recipe_id].labour_hours.values())
                      for recipe_id, count in runs.items())
    target = min(1.0, max(0.0, 1.0 - hired / offered))
    return previous + IDLE_SHARE_STEP * (target - previous)
