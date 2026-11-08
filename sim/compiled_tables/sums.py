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
