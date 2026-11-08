"""Python's own sums, as kernels: `sum` over floats and `math.fsum`, so a rule moved into a kernel adds the numbers the way the
Python it replaces did (a plain left-to-right loop would differ in the last digits).

`python_sum` is `sum` of a list of floats as CPython 3.12 and later does it: Neumaier's compensated loop, the compensation added
at the end. `exact_sum` is `math.fsum`: Shewchuk's exact partial sums, rounded once. Each takes the first `count` entries of an
array. Tests compare them with the built-ins on random inputs (sim/tests/test_labour_exact_sums.py)."""
import numpy

from sim.jit import njit


@njit
def python_sum(values, count):
    """`sum(list(values[:count]))` as Python 3.12+ computes it (no value may be infinite or NaN)."""
    total = 0.0
    compensation = 0.0
    for position in range(count):
        value = values[position]
        step = total + value
        if abs(total) >= abs(value):
            compensation += (total - step) + value
        else:
            compensation += (value - step) + total
        total = step
    if compensation != 0.0:
        total += compensation
    return total


@njit
def _add_partial(partials, used, value):
    """Shewchuk's step: `value` joins the non-overlapping partial sums; returns how many partials remain."""
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
