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


@njit
def _product(left, right):
    """left * right as (rounded product, exact rounding error): Dekker's split product, which gives what a fused multiply-add gives."""
    split = 134217729.0         # 2 ** 27 + 1
    product = left * right
    scaled = split * left
    left_high = scaled - (scaled - left)
    left_low = left - left_high
    scaled = split * right
    right_high = scaled - (scaled - right)
    right_low = right - right_high
    error = ((left_high * right_high - product) + left_high * right_low + left_low * right_high) + left_low * right_low
    return product, error


@njit
def float_sumprod(left, right, count):
    """`math.sumprod(left[:count], right[:count])` for finite floats: CPython's triple-length accumulation of exact products."""
    high = 0.0
    low = 0.0
    tiny = 0.0
    for position in range(count):
        product, error = _product(left[position], right[position])
        # error-free sums: the running high part and the product's high part, then the low parts
        sum_high = high + product
        z = sum_high - high
        sum_low = (high - (sum_high - z)) + (product - z)
        first_high = low + error
        z = first_high - low
        first_low = (low - (first_high - z)) + (error - z)
        second_high = first_high + sum_low
        z = second_high - first_high
        second_low = (first_high - (second_high - z)) + (sum_low - z)
        high = sum_high
        low = second_high
        tiny = tiny + first_low + second_low
    last_high = low + high
    z = last_high - low
    last_low = (low - (last_high - z)) + (high - z)
    return tiny + last_low + last_high
