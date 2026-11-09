"""Membership of a column in a set of ids by a lookup table, which costs a few array calls whatever the number of ids (`numpy.isin`
sorts and searches)."""
import numpy


def in_ids(values: numpy.ndarray, ids, bound: int) -> numpy.ndarray:
    """Per value: whether it is one of `ids` (a sequence of ints), as `numpy.isin(values, ids)` answers. Every value and id is
    in 0..`bound` - 1."""
    found = numpy.zeros(bound, dtype=numpy.bool_)
    found[list(ids)] = True
    return found[values]
