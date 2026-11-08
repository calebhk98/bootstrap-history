"""The carrier accounts' wear for every merchant at once (`carriage_wear_batch.settle_all`): which of a merchant's carrier stock is used up."""
import numpy

from sim.jit import njit


@njit
def wear_takes(group, wanted_of_row, quantity):
    """How much each carrier stock row gives up to the year's wear. The rows are merchants' carrier-account stock, grouped by `group` (one
    per merchant and good, equal neighbours) and, in a group, tiles by name; `wanted_of_row[row]` is the units its merchant wore of the
    row's good. A group is used up in row order, each row giving the lesser of what is left to take and what it holds, and nothing
    once the wear is met. Returns the units taken from each row (zero: none)."""
    taken = numpy.zeros(len(group))
    left = 0.0
    for row in range(len(group)):
        if row == 0 or group[row] != group[row - 1]:
            left = wanted_of_row[row]
        give = quantity[row] if quantity[row] < left else left
        if give > 0.0:
            taken[row] = give
            left -= give
    return taken
