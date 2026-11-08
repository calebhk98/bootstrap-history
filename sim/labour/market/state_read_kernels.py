"""Whole-table reads of the labour core's state (state_tables.py), as small kernels.

Each takes columns of the state's tables and answers for many markets, areas or pairs in one call, adding the numbers the way the
per-item reader it replaces did: `exact_sum` is `math.fsum` and `python_sum` is `sum` of a list (exact_sums.py), so a figure read here
is the figure the dict views gave, last digit included. A row of the grid is `area * trade_count + trade`; a row below zero is a pair
the state does not number and reads as nothing (zero people, zero hours), never a made-up figure. Tests: test_labour_state_reads.py."""
import numpy

from sim.jit import njit

from .exact_sums import exact_sum, python_sum


@njit
def hired_hours_at(rows, hired_first, hired_count, hours):
    """For each grid row, the hours all the market's employers were hired for (`math.fsum` of its HIRED rows); zero for a row below zero
    or a market with no employer. Reads `markets.hired_first`, `markets.hired_count` and `hired.hours`."""
    totals = numpy.zeros(len(rows))
    for place in range(len(rows)):
        row = rows[place]
        if row >= 0:
            first = hired_first[row]
            count = hired_count[row]
            totals[place] = exact_sum(hours[first:first + count], count)
    return totals


@njit
def people_at(rows, present, people, length):
    """For each grid row, the people working the pair (`math.fsum` of its band list); zero for a row below zero or a pair with no entry."""
    totals = numpy.zeros(len(rows))
    for place in range(len(rows)):
        row = rows[place]
        if row >= 0 and present[row]:
            totals[place] = exact_sum(people[row], length[row])
    return totals


@njit
def trade_people_over_areas(areas, trade_count, present, people, length):
    """Working people by trade over the listed areas (numbers, below zero: none): returns (people, seen), each per trade number.
    A trade's figure is added area by area in the order given, one `math.fsum` of bands per pair; `seen` marks a trade with an entry in
    some listed area, even an empty one."""
    totals = numpy.zeros(trade_count)
    seen = numpy.zeros(trade_count, numpy.bool_)
    for place in range(len(areas)):
        if areas[place] >= 0:
            for trade in range(trade_count):
                row = areas[place] * trade_count + trade
                if present[row]:
                    seen[trade] = True
                    totals[trade] += exact_sum(people[row], length[row])
    return totals, seen


@njit
def working_people_in_areas(areas, trade_count, present, people, length):
    """For each listed area (below zero: none), `math.fsum` of its trades' people, each trade's people being the `math.fsum` of its bands."""
    totals = numpy.zeros(len(areas))
    pair_people = numpy.zeros(trade_count)
    for place in range(len(areas)):
        if areas[place] >= 0:
            count = 0
            for trade in range(trade_count):
                row = areas[place] * trade_count + trade
                if present[row]:
                    pair_people[count] = exact_sum(people[row], length[row])
                    count += 1
            totals[place] = exact_sum(pair_people, count)
    return totals


@njit
def ordered_people_totals(worker_rows, worker_starts, worker_people, worker_length,
                          cohort_rows, cohort_starts, cohort_people, cohort_length):
    """Everyone counted in each area, working or learning: area `a` adds, with `sum`, the band lists of `worker_rows[worker_starts[a]:
    worker_starts[a + 1]]` in that order and then those of the cohort rows likewise, left to right as the per-area reader did."""
    totals = numpy.zeros(len(worker_starts) - 1)
    for area in range(len(totals)):
        total = 0.0
        for place in range(worker_starts[area], worker_starts[area + 1]):
            row = worker_rows[place]
            total += python_sum(worker_people[row], worker_length[row])
        for place in range(cohort_starts[area], cohort_starts[area + 1]):
            row = cohort_rows[place]
            total += python_sum(cohort_people[row], cohort_length[row])
        totals[area] = total
    return totals


@njit
def scale_pairs(first_row, stop_row, factor, present, people, length):
    """Multiply the people of every pair with an entry in grid rows `first_row .. stop_row - 1` by `factor`, band by band."""
    for row in range(first_row, stop_row):
        if present[row]:
            for band in range(length[row]):
                people[row, band] = people[row, band] * factor


@njit
def scale_cohorts(first_row, stop_row, factor, people, length):
    """Multiply the people of the trainee cohorts in rows `first_row .. stop_row - 1` by `factor`, band by band."""
    for row in range(first_row, stop_row):
        for band in range(length[row]):
            people[row, band] = people[row, band] * factor


@njit
def _weighted_mean(wage, weight, product, count):
    """(whether the weights add to something, `math.fsum(wage * weight) / math.fsum(weight)`) over the first `count` entries."""
    total = exact_sum(weight, count)
    if total > 0.0:
        for place in range(count):
            product[place] = wage[place] * weight[place]
        return True, exact_sum(product, count) / total
    return False, 0.0


@njit
def _wage_mean(wage, first_weight, second_weight, product, count):
    """The wage averaged by the first weights, else by the second, else plainly (`math.fsum(wage) / count`)."""
    weighted, mean = _weighted_mean(wage, first_weight, product, count)
    if not weighted:
        weighted, mean = _weighted_mean(wage, second_weight, product, count)
    if not weighted:
        mean = exact_sum(wage, count) / count
    return mean


@njit
def wage_means_by_group(group_ends, kept, wage, hours, people):
    """One mean wage per group of consecutive markets (group `g` is places `group_ends[g - 1] .. group_ends[g] - 1`) over the places
    marked in `kept`: weighted by the hours hired there, else by the people working there, else plain. Returns (mean, exists); a group
    with no kept place does not exist."""
    means = numpy.zeros(len(group_ends))
    exists = numpy.zeros(len(group_ends), numpy.bool_)
    wage_kept = numpy.zeros(len(wage))
    hours_kept = numpy.zeros(len(wage))
    people_kept = numpy.zeros(len(wage))
    product = numpy.zeros(len(wage))
    start = 0
    for group in range(len(group_ends)):
        count = 0
        for place in range(start, group_ends[group]):
            if kept[place]:
                wage_kept[count], hours_kept[count], people_kept[count] = wage[place], hours[place], people[place]
                count += 1
        if count > 0:
            exists[group] = True
            means[group] = _wage_mean(wage_kept, hours_kept, people_kept, product, count)
        start = group_ends[group]
    return means, exists


@njit
def people_weighted_wage_by_area(trade_count, wages_named, wage, present, people, length):
    """For each area whose wages view has an entry: the mean of its trades' wages weighted by the people working each trade there, the
    plain mean where nobody works any of them. Returns (mean, exists); an area with no wage does not exist."""
    area_count = len(wages_named)
    means = numpy.zeros(area_count)
    exists = numpy.zeros(area_count, numpy.bool_)
    wage_found = numpy.zeros(trade_count)
    people_found = numpy.zeros(trade_count)
    product = numpy.zeros(trade_count)
    for area in range(area_count):
        count = 0
        if wages_named[area]:
            for trade in range(trade_count):
                row = area * trade_count + trade
                if not numpy.isnan(wage[row]):
                    wage_found[count] = wage[row]
                    people_found[count] = exact_sum(people[row], length[row]) if present[row] else 0.0
                    count += 1
        if count > 0:
            exists[area] = True
            weighted, mean = _weighted_mean(wage_found, people_found, product, count)
            means[area] = mean if weighted else exact_sum(wage_found, count) / count
    return means, exists
