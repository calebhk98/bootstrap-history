"""`sum` over floats as CPython 3.12 and later does it, for the close's kernels (the shares of a dividend are added with `sum`).

`python_sum(values, count)` is `sum(list(values[:count]))`: Neumaier's compensated loop with the compensation added at the end (no
value may be infinite or NaN). The package wall keeps the economy from importing the labour package's copy."""
from sim.jit import njit


@njit
def python_sum(values, count):
    """`sum(list(values[:count]))` as Python 3.12+ computes it."""
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
