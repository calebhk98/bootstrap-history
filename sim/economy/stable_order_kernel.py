"""The order of rows by several keys with ties kept in arrival order, inside a kernel (numba has no `numpy.lexsort`).

Successive stable argsorts, the least significant key first, order exactly as `numpy.lexsort` over the same keys does."""
import numpy

from sim.jit import njit


@njit
def stable_order(keys_least_significant_first):
    """The order of the rows by the keys (a tuple of arrays of one length, the least significant first), as `numpy.lexsort` gives it."""
    order = numpy.arange(len(keys_least_significant_first[0]))
    for keys in keys_least_significant_first:
        order = order[numpy.argsort(keys[order], kind="mergesort")]
    return order
