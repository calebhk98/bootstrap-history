"""Question 4: ways to append a million rows to a table inside a kernel (docs/architecture/COMPILED_TABLES.md).

    python3 -c "from tools.measure.compiled_tables import growth; growth.main()"
"""
import sys
import time

sys.path.insert(0, ".")
import collections
import numpy as np

from sim.jit import njit  # noqa: E402

Bids = collections.namedtuple("Bids", ["size", "market", "price", "quantity"])   # size: one-element count


def new_bids(capacity):
    return Bids(np.zeros(1, np.int64), np.empty(capacity, np.int64), np.empty(capacity), np.empty(capacity))


@njit
def reserve(bids, extra):
    """The table with room for `extra` more rows: the same table when it fits, else a doubled copy."""
    needed = bids.size[0] + extra
    capacity = bids.market.shape[0]
    if needed <= capacity:
        return bids
    new_capacity = max(needed, 2 * capacity)
    market = np.empty(new_capacity, np.int64)
    price = np.empty(new_capacity)
    quantity = np.empty(new_capacity)
    count = bids.size[0]
    market[:count] = bids.market[:count]
    price[:count] = bids.price[:count]
    quantity[:count] = bids.quantity[:count]
    return Bids(bids.size, market, price, quantity)


@njit
def add_bid(bids, market, price, quantity):
    row = bids.size[0]
    bids.market[row] = market
    bids.price[row] = price
    bids.quantity[row] = quantity
    bids.size[0] = row + 1
    return row


@njit
def fill_known_bound(bids, count):
    """Pattern B: the phase knows an upper bound, reserves once, then appends without checks of its own."""
    bids = reserve(bids, count)
    for i in range(count):
        add_bid(bids, i % 100, 1.0 * i, 2.0)
    return bids


@njit
def fill_reserve_each(bids, count):
    """Pattern C: every append asks for room first (the table may be replaced inside the loop)."""
    for i in range(count):
        bids = reserve(bids, 1)
        add_bid(bids, i % 100, 1.0 * i, 2.0)
    return bids


@njit
def fill_raw_arrays(market, price, quantity, count):
    """The floor: plain presized arrays and a local counter."""
    for i in range(count):
        market[i] = i % 100
        price[i] = 1.0 * i
        quantity[i] = 2.0
    return count


@njit
def fill_reserve_when_full(bids, count):
    """Pattern C2: reserve only when the table is full (the check is in the loop, the copy is not)."""
    for i in range(count):
        if bids.size[0] == bids.market.shape[0]:
            bids = reserve(bids, 1)
        add_bid(bids, i % 100, 1.0 * i, 2.0)
    return bids


@njit
def fill_raw_fresh(count):
    market, price, quantity = np.empty(count, np.int64), np.empty(count), np.empty(count)
    for i in range(count):
        market[i] = i % 100
        price[i] = 1.0 * i
        quantity[i] = 2.0
    return count


def python_boundary(count):
    """Pattern D: Python grows a table by doubling and the kernel only fills what fits (one kernel call per chunk)."""
    bids = new_bids(16)
    done = 0
    while done < count:
        free = bids.market.shape[0] - bids.size[0]
        if free == 0:
            bids = Bids(bids.size, np.concatenate([bids.market, np.empty_like(bids.market)]),
                        np.concatenate([bids.price, np.empty_like(bids.price)]),
                        np.concatenate([bids.quantity, np.empty_like(bids.quantity)]))
            continue
        chunk = min(free, count - done)
        fill_chunk(bids, done, chunk)
        done += chunk
    return bids


@njit
def fill_chunk(bids, start, chunk):
    for i in range(start, start + chunk):
        add_bid(bids, i % 100, 1.0 * i, 2.0)


def best(function, repeats=15):
    function()
    times = []
    for _ in range(repeats):
        a = time.perf_counter()
        function()
        times.append(time.perf_counter() - a)
    return 1000 * min(times)




def main():
    count = 1_000_000
    check = fill_reserve_each(new_bids(16), 1000)
    assert check.size[0] == 1000 and check.price[999] == 999.0
    market, price, quantity = np.empty(count, np.int64), np.empty(count), np.empty(count)
    print("floor, presized plain arrays:                %6.2f ms" % best(lambda: fill_raw_arrays(market, price, quantity, count)))
    print("floor, fresh arrays inside the kernel:       %6.2f ms" % best(lambda: fill_raw_fresh(count)))
    fill_reserve_when_full(new_bids(16), 100)
    print("C2 reserve only when full (from 16):          %6.2f ms" % best(lambda: fill_reserve_when_full(new_bids(16), count)))
    print("A  presized table, count in the table:       %6.2f ms" % best(lambda: fill_known_bound(new_bids(count), count)))
    print("B  reserve once with a known bound (from 16): %6.2f ms" % best(lambda: fill_known_bound(new_bids(16), count)))
    print("C  reserve before every append (from 16):     %6.2f ms" % best(lambda: fill_reserve_each(new_bids(16), count)))
    print("D  Python doubles, kernel fills chunks:       %6.2f ms" % best(lambda: python_boundary(count)))
    print("   (table construction alone, 1M rows:        %6.2f ms)" % best(lambda: new_bids(count)))

