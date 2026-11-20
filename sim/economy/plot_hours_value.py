"""What a household reckons an hour on its own plot is worth when it decides how many hours to keep for it.

The plot grows the same crop for every hour it takes (`households_own.own_production`: the floors of the needs it can
grow, on the land held), so an hour there is worth that crop at the prices of the needs. The hours schedule
(`households_hours_offered.plot_hours_kept`) reads one figure, the return of the next hour with the whole year on the
plot, and keeps hours down to where a falling return meets the wage. Two rules give it that figure (rule_sets.py): the
return of the next hour on the land's intensive margin (`labour_ask_floor.plot_return_per_hour`), which keeps few
hours and leaves the plot to the hours nobody hired; and the figure under which the schedule keeps every hour the plot
takes while the crop is worth the wage or more, and fewer as the wage rises above it."""
import math
from typing import Mapping, Optional, Sequence

from sim.world.need_basket import PricedNeed
from sim.world.shared_constants import LABOUR_OUTPUT_ELASTICITY

from . import harvest_tax
from .households_own import Option
from .labour_ask_floor import plot_return_per_hour
from .priced_need_list import priced_needs_of


def crop_value_per_hour(priced: Sequence[PricedNeed], options: Mapping[str, Sequence[Option]], fertility: float,
                        share_by_good: Optional[Mapping[str, float]] = None) -> float:
    """Money an hour on the plot grows: the floors of the needs the plot can grow, at the needs' prices net of the
    state's share of each good, over the hours those floors take at this fertility. Nothing where it grows none."""
    if fertility <= 0.0:
        return 0.0
    values, hours = [], []
    for spec, price_index, _first, _end in priced_needs_of(priced).blocks():
        rows = options.get(spec.need_id)
        if not rows or rows[0][0] <= 0.0:
            continue
        values.append(price_index * harvest_tax.kept_share(rows[0][2], share_by_good or {}) * spec.subsistence_per_person)
        hours.append(spec.subsistence_per_person * rows[0][0] / fertility)
    total = math.fsum(hours)
    return math.fsum(values) / total if total > 0.0 else 0.0


def return_that_keeps_the_usable_hours(crop_value: float, usable_hours: float, hours_available: float,
                                       elasticity: float = LABOUR_OUTPUT_ELASTICITY) -> float:
    """The return figure (of the next hour with all of `hours_available` on the plot) under which `plot_hours_kept`
    keeps every one of the `usable_hours` at a wage up to `crop_value`, and above it the usable hours times (crop value
    over the wage) to the power the schedule falls by."""
    if crop_value <= 0.0 or usable_hours <= 0.0 or hours_available <= 0.0:
        return 0.0
    return crop_value * min(1.0, usable_hours / hours_available) ** (1.0 - elasticity)


def return_of_the_next_hour(priced, options, fertility: float, hours_per_worker: float, people_per_worker: float,
                            hectares_per_hour: Mapping[str, float], hectares_held: Optional[float],
                            share_by_good: Optional[Mapping[str, float]], _usable_hours: float) -> float:
    """The plot's return as the ask floor reads it: what the next hour adds with the worker's whole year on the plot."""
    return plot_return_per_hour(priced, options, fertility, hours_per_worker, people_per_worker, hectares_per_hour, hectares_held,
                                share_by_good)


def return_keeping_what_the_plot_grows(priced, options, fertility: float, hours_per_worker: float, _people_per_worker: float,
                                       _hectares_per_hour: Mapping[str, float], _hectares_held: Optional[float],
                                       share_by_good: Optional[Mapping[str, float]], usable_hours: float) -> float:
    """The plot's return under which a worker keeps the hours the plot takes while their crop is worth the wage."""
    return return_that_keeps_the_usable_hours(crop_value_per_hour(priced, options, fertility, share_by_good), usable_hours,
                                              hours_per_worker)
