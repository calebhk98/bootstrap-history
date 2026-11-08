"""Sums in a fixed order. A kernel adds a column left to right in row order and nothing else.

numpy's `sum`, `dot` and `@` add in pairs and blocks, so in plain Python (ROME_NO_JIT=1) they give other last digits than
numba's loop, and `math.fsum` does not exist in nopython. Use `ordered_total` over rows in id order (ids in sorted order, see
IdTable) so the compiled and plain runs agree and a loaded game sums as the live one did."""
from sim.jit import njit


@njit
def ordered_total(values, count):
    """values[0] + values[1] + ... + values[count - 1], added left to right."""
    total = 0.0
    for row in range(count):
        total += values[row]
    return total


@njit
def python_sum(values, count):
    """`sum(list(values[:count]))` as Python 3.12 and later computes it: Neumaier's compensated loop, the compensation added at the end
    (no value may be infinite or NaN). Use it where the rule being ported added floats with the built-in `sum`."""
    total = 0.0
    compensation = 0.0
    for row in range(count):
        value = values[row]
        step = total + value
        if abs(total) >= abs(value):
            compensation += (total - step) + value
        else:
            compensation += (value - step) + total
        total = step
    if compensation != 0.0:
        total += compensation
    return total
