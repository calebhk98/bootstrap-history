"""What a cohort's offers add up to, as kernels over the year's offer rows grouped by worker (`household_offer_reads.py`).

Rows are sorted by worker (a stable sort, so a worker's rows stay in the order the offers were made); `start[worker]` and
`end[worker]` bound a worker's rows (a worker with no offers has an empty range). Sums are Python's own (`python_sum`:
`sum` of a list as CPython 3.12 and later computes it), so each figure is the one the plain loops over `LabourOffer`s gave."""
import numpy

from sim.jit import njit
from sim.labour.api import python_sum


@njit
def hours_by_worker(start, end, hours):
    """For each worker, `sum` of the hours of all its offers, in row order; zero for a worker with none.
    start, end: first and one past the last sorted row of each worker; hours: the sorted offers' hours. -> hours per year."""
    totals = numpy.zeros(start.shape[0])
    for worker in range(start.shape[0]):
        totals[worker] = python_sum(hours[start[worker]:end[worker]], end[worker] - start[worker])
    return totals


@njit
def hour_value_by_worker(start, end, hours, wage_per_hour, scratch_hours, scratch_pay):
    """For each worker, the wage per hour its offers face averaged over the hours they hold, counting only offers of hours
    above zero; zero when it offers none (`households_work.hour_value`, and `household_hours_year.wage_faced_per_hour` where the
    wage is the faced wage alone). wage_per_hour: the sorted offers' wages; the scratch arrays are as long as the offers. -> money per hour."""
    values = numpy.zeros(start.shape[0])
    for worker in range(start.shape[0]):
        used = 0
        for place in range(start[worker], end[worker]):
            if hours[place] > 0.0:
                scratch_hours[used] = hours[place]
                scratch_pay[used] = hours[place] * wage_per_hour[place]
                used += 1
        total = python_sum(scratch_hours, used)
        if total > 0.0:
            values[worker] = python_sum(scratch_pay, used) / total
    return values


@njit
def sum_in_order_by_group(group, group_count, values):
    """For each group, the values added left to right from zero in row order (`total.get(key, 0.0) + value`, as a loop over
    records did): the hours offered in each (trade, area) market, the rows in the order the offers were made."""
    totals = numpy.zeros(group_count)
    for row in range(group.shape[0]):
        totals[group[row]] = totals[group[row]] + values[row]
    return totals
