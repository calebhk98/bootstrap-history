"""The offers of the producers whose turn it is, in a batch: what `producers.offers` gives each producer, for all of them in one
kernel call.

A producer offers each output it holds beyond what its own runs need at the reservation `inventory.holding_reservation`
gives from the price it expects, lowered (`inventory.distressed_reservation`) by the cash it still has to raise against
the runs it could work next year (`producers.shortfall_at_working_scale`). `offer_reservations` is that for every
(producer, output) pair of the batch, the share of its plant a run pays read from `OfferCosts.pays`. An output with no price
expected falls back to the variable cost of a unit, and a storage cost would need the area's money: a producer with either goes
through `producers.offers` itself (year_goods._quick_outputs hands it back)."""
import numpy as np

from sim.jit import njit

from .inventory import DISTRESS_CURVE_EXPONENT
from .producers import OUTPUT_CHANGE_SHARE_PER_YEAR, STORAGE_COST_PER_UNIT

KERNEL = {"error_model": "numpy"}


@njit(**KERNEL)
def offer_reservations(pair_ptr, expected, spoilage, quantity, shortfall, capacity, cash_target, last_runs, expected_sales,
                       pays, rate, change_share, exponent):
    """The reservation of each (producer, output) pair; pair_ptr[i]:pair_ptr[i + 1] are producer i's pairs."""
    reservation = np.zeros(len(expected))
    discount = 1.0 + max(rate, -0.99)
    for producer in range(len(pair_ptr) - 1):
        first, last = pair_ptr[producer], pair_ptr[producer + 1]
        stock_value = 0.0
        for pair in range(first, last):
            reservation[pair] = expected[pair] * (1.0 - min(1.0, max(0.0, spoilage[pair]))) / discount
            stock_value += quantity[pair] * max(reservation[pair], 0.0)
        lacking = shortfall[producer]
        if capacity[producer] > 0.0:
            if not lacking > 0.0:
                lacking = 0.0
            else:
                ceiling = capacity[producer]
                if last_runs[producer] >= 0.0:
                    ceiling = min(ceiling, max(last_runs[producer], expected_sales[producer]) + change_share * capacity[producer])
                unused = 1.0 - ceiling * pays[producer] / capacity[producer]
                lacking = max(0.0, lacking - unused * cash_target[producer])
        if lacking > 0.0:
            for pair in range(first, last):
                if reservation[pair] > 0.0:
                    if stock_value <= 0.0:
                        reservation[pair] = 0.0
                    else:
                        reservation[pair] = reservation[pair] * (1.0 - min(1.0, lacking / stock_value) ** exponent)
    return reservation


def usable() -> bool:
    return STORAGE_COST_PER_UNIT == 0.0


def reservations_for(arrays, costs, rows, pair_ptr, expected, spoilage, quantity, shortfall, rate) -> np.ndarray:
    """`offer_reservations` for producers at `rows` of the year arrays with the given pairs and cash shortfalls to raise."""
    producers = arrays.producers
    rows = np.array(rows, dtype=np.int64)
    return offer_reservations(
        np.array(pair_ptr, dtype=np.int64), np.array(expected, dtype=float), np.array(spoilage, dtype=float),
        np.array(quantity, dtype=float), np.array(shortfall, dtype=float), producers.capacity_runs[rows],
        producers.cash_target[rows], producers.last_runs[rows], producers.expected_sales[rows], costs.pays[rows], float(rate),
        OUTPUT_CHANGE_SHARE_PER_YEAR, DISTRESS_CURVE_EXPONENT)
