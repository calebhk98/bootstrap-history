"""Question 1: a table as a namedtuple of arrays, a structref or a jitclass: build cost, per-call cost, and whether the
kernel loads from numba's disk cache in a second process (docs/architecture/COMPILED_TABLES.md).

    python3 -c "from tools.measure.compiled_tables import table_kinds; table_kinds.main()"     # run twice: cold, then warm
    ROME_NO_JIT=1 python3 -c "from tools.measure.compiled_tables import table_kinds; table_kinds.main()"

Delete tools/measure/compiled_tables/__pycache__ first for a cold run. The classes must be importable from a module (as
here), not defined in the script that is run: a namedtuple defined in `__main__` was measured not to load from the cache."""
import collections
import sys
import time

import numpy as np

sys.path.insert(0, ".")
from sim import jit  # noqa: E402
from sim.jit import njit  # noqa: E402

Loans = collections.namedtuple("Loans", ["amount", "rate"])


@njit
def total_of_namedtuple(table, count):
    total = 0.0
    for row in range(count):
        total += table.amount[row] * table.rate[row]
    return total


@njit
def total_of_arrays(amount, rate, count):
    total = 0.0
    for row in range(count):
        total += amount[row] * rate[row]
    return total


def structref_kernel():
    """Built on demand: numba's experimental classes are only imported when this comparison runs."""
    from numba import njit as numba_njit, types
    from numba.experimental import structref

    @structref.register
    class LoansType(types.StructRef):
        def preprocess_fields(self, fields):
            return tuple((name, types.unliteral(typ)) for name, typ in fields)

    class LoansRef(structref.StructRefProxy):
        pass

    structref.define_proxy(LoansRef, LoansType, ["amount", "rate"])

    @numba_njit(cache=True)
    def total_of_structref(table, count):
        total = 0.0
        for row in range(count):
            total += table.amount[row] * table.rate[row]
        return total
    return LoansRef, total_of_structref


def jitclass_kernel():
    import numba
    from numba import njit as numba_njit
    from numba.experimental import jitclass

    @jitclass([("amount", numba.float64[:]), ("rate", numba.float64[:])])
    class LoansJit:
        def __init__(self, amount, rate):
            self.amount = amount
            self.rate = rate

    @numba_njit(cache=True)
    def total_of_jitclass(table, count):
        total = 0.0
        for row in range(count):
            total += table.amount[row] * table.rate[row]
        return total
    return LoansJit, total_of_jitclass


def timed(function):
    start = time.perf_counter()
    result = function()
    return result, time.perf_counter() - start


def calls_per_second_cost(function, calls=100000):
    start = time.perf_counter()
    for _ in range(calls):
        function()
    return (time.perf_counter() - start) / calls * 1e6


def main():
    jit.load_numba()
    count = 1000
    table = Loans(np.ones(count), np.full(count, 0.1))
    total_of_arrays(table.amount, table.rate, count)       # one-time cost of the first cached call, kept out of the rest
    _result, seconds = timed(lambda: total_of_arrays(table.amount, table.rate, count))
    print("plain arrays, first call:        %.3f s" % seconds)
    _result, seconds = timed(lambda: total_of_namedtuple(table, count))
    print("namedtuple, first call:          %.3f s" % seconds)
    print("per call, plain arrays:          %.2f us" % calls_per_second_cost(lambda: total_of_arrays(table.amount, table.rate, count)))
    print("per call, namedtuple:            %.2f us" % calls_per_second_cost(lambda: total_of_namedtuple(table, count)))
    if not jit.ENABLED:
        return
    for label, factory in (("structref", structref_kernel), ("jitclass", jitclass_kernel)):
        (cls, kernel), seconds = timed(factory)
        made, build = timed(lambda: cls(table.amount, table.rate))
        _result, first = timed(lambda: kernel(made, count))
        print("%-9s define %.3f s, construct %.3f s, first call %.3f s, per call %.2f us"
              % (label, seconds, build, first, calls_per_second_cost(lambda: kernel(made, count))))
