"""`math.fsum` as a kernel: Shewchuk's exact partial sums, rounded once, for a rule that summed with `math.fsum`. The package wall keeps
the economy from importing the labour package's copy (sim/labour/market/exact_sums.py, tested against the built-in in
sim/tests/test_labour_exact_sums.py)."""
import numpy

from sim.jit import njit


@njit
def _add_partial(partials, used, value):
    """`value` joins the non-overlapping partial sums; returns how many partials remain."""
    kept = 0
    for position in range(used):
        other = partials[position]
        if abs(value) < abs(other):
            value, other = other, value
        high = value + other
        low = other - (high - value)
        if low != 0.0:
            partials[kept] = low
            kept += 1
        value = high
    if value != 0.0:
        partials[kept] = value
        kept += 1
    return kept


@njit
def _round_partials(partials, used):
    """The partials added from the top and rounded half to even across them, as `math.fsum` ends."""
    if used == 0:
        return 0.0
    used -= 1
    high = partials[used]
    low = 0.0
    while used > 0:
        used -= 1
        other = partials[used]
        step = high + other
        low = other - (step - high)
        high = step
        if low != 0.0:
            break
    if used > 0 and ((low < 0.0 and partials[used - 1] < 0.0) or (low > 0.0 and partials[used - 1] > 0.0)):
        doubled = low * 2.0
        moved = high + doubled
        if doubled == moved - high:
            high = moved
    return high


@njit
def exact_sum(values, count):
    """`math.fsum(values[:count])` (finite values only)."""
    partials = numpy.zeros(count + 1)
    used = 0
    for position in range(count):
        used = _add_partial(partials, used, values[position])
    return _round_partials(partials, used)
