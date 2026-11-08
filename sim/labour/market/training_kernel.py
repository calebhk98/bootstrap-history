"""Training over the state's tables: every cohort ages a year and the finished ones graduate (`training.advance`)."""
import math

import numpy

from sim.jit import njit

from .exact_sums import exact_sum


@njit
def completion_chance(ability, difficulty, bonus, spread):
    """`aptitude.completion_chance`: the chance that someone of this ability finishes a training of this difficulty."""
    exponent = -(ability + bonus - difficulty) / spread
    if exponent > 700.0:
        return 0.0
    return 1.0 / (1.0 + math.exp(exponent))


@njit
def _name_worker_cell(row, workers_present, workers_order, area, area_named, area_order, counter):
    """The pair has an entry in the workers view (`aptitude.bands_of` on the area's dict), the area too, stamped in the order made."""
    if not area_named[area]:
        counter[0] += 1
        area_named[area] = True
        area_order[area] = counter[0]
    if not workers_present[row]:
        counter[0] += 1
        workers_present[row] = True
        workers_order[row] = counter[0]


@njit
def graduate_cohort(people_row, chances, workers_people, own_row, fallback_row, finished, failed):
    """Split a finished cohort's people per band into those who finish (people times chance) and those who do not, and add them to
    the trade's workers and the fallback trade's. Returns the people who finished, summed as `math.fsum` sums them."""
    bands = people_row.shape[0]
    for band in range(bands):
        finished[band] = people_row[band] * chances[band]
        failed[band] = people_row[band] - finished[band]
    for band in range(bands):
        workers_people[own_row, band] += finished[band]
    for band in range(bands):
        workers_people[fallback_row, band] += failed[band]
    return exact_sum(finished, bands)


@njit
def age_cohorts(market, years_left, bonus, people, rows, trade_count, difficulty, has_spec, fallback, ability, spread, tolerance,
                workers_people, workers_present, workers_order, area_named, area_order, counter, graduated, graduated_any, keep):
    """Every cohort ages a year. A cohort whose years reach zero (within `tolerance`) is not kept: its people graduate into the trade
    with each band's chance of finishing (zero for a trade the year does not list, `has_spec` false) and the rest join the
    fallback trade. `graduated[row]` adds the people who finished, `graduated_any[row]` marks the pair as having had a graduation.
    Cohorts are visited in table order, which is (area, trade, enrolment) order."""
    bands = people.shape[1]
    chances = numpy.zeros(bands)
    finished = numpy.zeros(bands)
    failed = numpy.zeros(bands)
    for row in range(rows):
        years_left[row] -= 1.0
        keep[row] = years_left[row] > tolerance
        if keep[row]:
            continue
        grid = market[row]
        area = grid // trade_count
        trade = grid % trade_count
        fallback_row = area * trade_count + fallback
        for band in range(bands):
            chances[band] = completion_chance(ability[band], difficulty[trade], bonus[row], spread) if has_spec[trade] else 0.0
        _name_worker_cell(grid, workers_present, workers_order, area, area_named, area_order, counter)
        _name_worker_cell(fallback_row, workers_present, workers_order, area, area_named, area_order, counter)
        graduated[grid] += graduate_cohort(people[row], chances, workers_people, grid, fallback_row, finished, failed)
        graduated_any[grid] = True
