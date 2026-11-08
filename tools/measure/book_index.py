"""Why the book finds a stock slot through a hash index: lookups in a hash against a binary search of a sorted key array, and
what adding a key costs each. Run from the repository root:

    python3 tools/measure/book_index.py

It prints, for a table the size of a warm Rome year's stock slots, the time of a million lookups by each method, and the time to
add one key to a sorted array (it must move the keys after it) against adding to the hash. The book's kernels add slots as
they post, which is the reason for the hash; the lookup times show it costs nothing in speed."""
import sys
import time

import numpy

sys.path.insert(0, ".")
from sim.book_index import EMPTY, index_add, index_find, index_size_for   # noqa: E402
from sim.jit import njit   # noqa: E402

SLOTS = 70000
LOOKUPS = 1000000


@njit
def sorted_find(sorted_keys, key):
    """Binary search: the position of the key in the sorted array, or -1."""
    low, high = 0, len(sorted_keys)
    while low < high:
        middle = (low + high) // 2
        if sorted_keys[middle] < key:
            low = middle + 1
        else:
            high = middle
    if low < len(sorted_keys) and sorted_keys[low] == key:
        return low
    return -1


@njit
def hash_lookups(keys, index, probes):
    found = 0
    for position in range(len(probes)):
        if index_find(keys, index, probes[position]) != EMPTY:
            found += 1
    return found


@njit
def sorted_lookups(sorted_keys, probes):
    found = 0
    for position in range(len(probes)):
        if sorted_find(sorted_keys, probes[position]) >= 0:
            found += 1
    return found


def timed(function, *arguments):
    function(*arguments)
    began = time.perf_counter()
    result = function(*arguments)
    return time.perf_counter() - began, result


def main():
    generator = numpy.random.default_rng(1)
    keys = numpy.unique(generator.integers(0, 1 << 60, SLOTS)).astype(numpy.int64)
    index = numpy.full(index_size_for(len(keys)), EMPTY, dtype=numpy.int64)
    for row in range(len(keys)):
        index_add(keys, index, row)
    probes = keys[generator.integers(0, len(keys), LOOKUPS)]
    sorted_keys = numpy.sort(keys)
    seconds, _ = timed(hash_lookups, keys, index, probes)
    print("hash index: %d lookups in %.3f s" % (LOOKUPS, seconds))
    seconds, _ = timed(sorted_lookups, sorted_keys, probes)
    print("sorted array with binary search: %d lookups in %.3f s" % (LOOKUPS, seconds))
    began = time.perf_counter()
    for _ in range(200):
        numpy.insert(sorted_keys, 17, 1)
    print("adding a key to the sorted array: %.1f microseconds" % ((time.perf_counter() - began) / 200 * 1e6))
    print("adding a key to the hash: a probe and one write, inside the posting kernel (no table to move)")


if __name__ == "__main__":
    main()
