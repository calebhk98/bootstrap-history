"""Question 2: one large kernel against the same rule as small helper kernels (batch of small markets).

    python3 -c "from tools.measure.compiled_tables import small_functions; small_functions.main()"
    python3 -c "from tools.measure.compiled_tables import small_functions; small_functions.main('large', 40)"   # for valgrind

Instructions: PYTHONHASHSEED=0 NUMBA_CPU_NAME=generic valgrind --tool=cachegrind --cache-sim=no python3 -c "..." with
repetitions 0 and 40, for 'large' and for 'small'; the difference is the cost of the repetitions."""
import sys
import time

import numpy as np

sys.path.insert(0, ".")
from sim.jit import njit  # noqa: E402


# ---- one large function: for each market, find the price where demand meets supply by bisection, settle, accumulate
@njit
def clear_large(starts, bid_price, bid_qty, offer_price, offer_qty, traded, price_out):
    for market in range(starts.shape[0] - 1):
        first = starts[market]
        last = starts[market + 1]
        low = 0.0
        high = 100.0
        for _ in range(40):
            mid = 0.5 * (low + high)
            demand = 0.0
            for slot in range(first, last):
                if bid_price[slot] >= mid:
                    demand += bid_qty[slot]
            supply = 0.0
            for slot in range(first, last):
                if offer_price[slot] <= mid:
                    supply += offer_qty[slot]
            if demand > supply:
                low = mid
            else:
                high = mid
        price = 0.5 * (low + high)
        demand = 0.0
        for slot in range(first, last):
            if bid_price[slot] >= price:
                demand += bid_qty[slot]
        supply = 0.0
        for slot in range(first, last):
            if offer_price[slot] <= price:
                supply += offer_qty[slot]
        traded[market] = min(demand, supply)
        price_out[market] = price


# ---- the same rule as small helpers
@njit
def demand_at(price, first, last, bid_price, bid_qty):
    total = 0.0
    for slot in range(first, last):
        if bid_price[slot] >= price:
            total += bid_qty[slot]
    return total


@njit
def supply_at(price, first, last, offer_price, offer_qty):
    total = 0.0
    for slot in range(first, last):
        if offer_price[slot] <= price:
            total += offer_qty[slot]
    return total


@njit
def clearing_price(first, last, bid_price, bid_qty, offer_price, offer_qty):
    low = 0.0
    high = 100.0
    for _ in range(40):
        mid = 0.5 * (low + high)
        if demand_at(mid, first, last, bid_price, bid_qty) > supply_at(mid, first, last, offer_price, offer_qty):
            low = mid
        else:
            high = mid
    return 0.5 * (low + high)


@njit
def quantity_traded(price, first, last, bid_price, bid_qty, offer_price, offer_qty):
    return min(demand_at(price, first, last, bid_price, bid_qty), supply_at(price, first, last, offer_price, offer_qty))


@njit
def clear_small(starts, bid_price, bid_qty, offer_price, offer_qty, traded, price_out):
    for market in range(starts.shape[0] - 1):
        first = starts[market]
        last = starts[market + 1]
        price = clearing_price(first, last, bid_price, bid_qty, offer_price, offer_qty)
        traded[market] = quantity_traded(price, first, last, bid_price, bid_qty, offer_price, offer_qty)
        price_out[market] = price


def make(markets, per_market, seed=1):
    rng = np.random.default_rng(seed)
    starts = np.arange(0, (markets + 1) * per_market, per_market).astype(np.int64)
    size = markets * per_market
    return (starts, rng.uniform(1, 60, size), rng.uniform(1, 10, size), rng.uniform(1, 60, size), rng.uniform(1, 10, size),
            np.zeros(markets), np.zeros(markets))


def run(kernel, data, repeats):
    kernel(*data)
    start = time.process_time()
    for _ in range(repeats):
        kernel(*data)
    return (time.process_time() - start) / repeats


def main(which="time", repetitions=20):
    data = make(3000, 6)
    if which == "time":
        for name, kernel in (("large", clear_large), ("small helpers", clear_small)) * 4:
            print("%-14s %.2f ms per 3000 markets" % (name, 1000 * run(kernel, data, 100)))
        a = make(3000, 6); b = make(3000, 6)
        clear_large(*a); clear_small(*b)
        print("same answer:", bool((a[5] == b[5]).all() and (a[6] == b[6]).all()))
    else:
        kernel = clear_large if which == "large" else clear_small
        kernel(*data)                          # compile / load from cache
        for _ in range(repetitions):
            kernel(*data)

