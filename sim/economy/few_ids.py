"""Membership of a column in a few ids, cheaper than `numpy.isin` (which sorts and searches) when the ids are a handful."""
import numpy

FEW = 8     # more ids than this go to `numpy.isin`


def in_ids(values: numpy.ndarray, ids) -> numpy.ndarray:
    """Per value: whether it is one of `ids` (a sequence of ints), as `numpy.isin(values, ids)` answers."""
    if len(ids) > FEW:
        return numpy.isin(values, numpy.array(ids, dtype=numpy.int64))
    found = numpy.zeros(len(values), dtype=numpy.bool_)
    for each in ids:
        found |= values == each
    return found
