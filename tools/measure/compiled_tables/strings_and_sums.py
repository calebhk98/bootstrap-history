"""Questions 6 and 7: what a string costs inside a kernel, and which sums agree with a plain left-to-right loop.

    python3 -c "from tools.measure.compiled_tables import strings_and_sums; strings_and_sums.main()"
"""
import math
import sys
import time

import numpy as np

sys.path.insert(0, ".")
from sim import jit  # noqa: E402
from sim.jit import njit  # noqa: E402


@njit
def count_name_matches(names):
    matches = 0
    for row in range(names.shape[0]):
        if names[row] == "wheat_kg":
            matches += 1
    return matches


@njit
def count_id_matches(ids, wanted):
    matches = 0
    for row in range(ids.shape[0]):
        if ids[row] == wanted:
            matches += 1
    return matches


@njit
def loop_total(values):
    total = 0.0
    for row in range(values.shape[0]):
        total += values[row]
    return total


@njit
def method_total(values):
    return values.sum()


def milliseconds(function):
    function()
    start = time.perf_counter()
    function()
    return 1000 * (time.perf_counter() - start)


def main():
    jit.load_numba()
    names = np.array(["wheat_kg", "iron_kg", "copper_kg"] * 100000)
    ids = np.array([0, 1, 2] * 100000)
    print("string array compared in a kernel, 300000 rows: %.2f ms" % milliseconds(lambda: count_name_matches(names)))
    print("id array compared in a kernel, 300000 rows:     %.2f ms" % milliseconds(lambda: count_id_matches(ids, 0)))
    random = np.random.default_rng(0)
    values = random.uniform(0, 1e6, 100000) * random.choice([1, 1e-7], 100000)
    in_python = 0.0
    for value in values.tolist():
        in_python += value
    print("python left to right: %r" % in_python)
    print("kernel loop:          %r" % loop_total(values))
    print("kernel values.sum():  %r" % method_total(values))
    print("numpy values.sum():   %r   (pairwise: the plain-Python run of values.sum() would differ from the kernel)" % values.sum())
    print("math.fsum:            %r   (not available in a kernel)" % math.fsum(values))
