"""Small kernels that turn the state's tables and the year's bid columns into the cells `clearing_kernel.market_heads` reads."""
import numpy

from sim.jit import njit

from .exact_sums import python_sum


@njit
def people_hours(people, present, in_play, hours_per_worker, trade_count, everyone, with_people):
    """For every grid row (area * trade_count + trade): the hours its workers have, `sum(bands) * hours_per_worker`, where the pair is
    held and its trade is in play, else zero (`everyone`); and whether the people (`sum(bands)`) are above zero (`with_people`)."""
    for row in range(people.shape[0]):
        everyone[row] = 0.0
        with_people[row] = False
        if present[row] and in_play[row % trade_count]:
            total = python_sum(people[row], people.shape[1])
            everyone[row] = total * hours_per_worker
            with_people[row] = total > 0.0


@njit
def bid_totals(market_row, hours, maximum_wage, wanted, most):
    """Per grid row: the hours bid for it (each bid's hours floored at zero, added in bid order) and the highest maximum wage."""
    for bid in range(market_row.shape[0]):
        row = market_row[bid]
        wanted[row] += max(hours[bid], 0.0)
        if maximum_wage[bid] > most[row]:
            most[row] = maximum_wage[bid]


@njit
def hired_keys(hired_count, hired_employer, employer_count, keys):
    """For every HIRED row, `grid row * employer_count + employer`: the key a bid looks its market's held hours up by."""
    row = 0
    for market in range(hired_count.shape[0]):
        for _held in range(hired_count[market]):
            keys[row] = market * employer_count + hired_employer[row]
            row += 1


def previous_hours(hired_count, hired_employer, hired_hours, employer_count, bid_market_row, bid_employer):
    """The hours each bid's employer held in the bid's market last year (zero where it held none)."""
    rows = len(hired_employer)
    if not rows:
        return numpy.zeros(len(bid_market_row))
    keys = numpy.empty(rows, dtype=numpy.int64)
    hired_keys(hired_count, hired_employer, employer_count, keys)
    order = numpy.argsort(keys, kind="stable")
    sorted_keys = keys[order]
    wanted = bid_market_row * employer_count + bid_employer
    found = numpy.minimum(numpy.searchsorted(sorted_keys, wanted), rows - 1)
    return numpy.where(sorted_keys[found] == wanted, hired_hours[order[found]], 0.0)
