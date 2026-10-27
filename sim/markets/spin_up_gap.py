"""How far the agent economy moved between hidden spin-up years: pure arithmetic over per-year states.

A state is {"price_level", "rate", "prices": {good: price}, plus the quantities of `QUANTITY_FLOORS`}. A
change is relative to the earlier value, with the earlier value no smaller than a floor where the quantity
can sit near zero (a rate, unmet need), so such a quantity shrinking toward zero can still count as settled.
"""
from sim.constants import declare

SPIN_UP_RATE_FLOOR = declare(
    "SPIN_UP_RATE_FLOOR", 0.01, kind="temporary_heuristic",
    unit="interest rate below which a change in the rate is measured against this instead of the rate",
    source=None, confidence="D", retire="Complaints/473: a spin-up that settles needs no floor on its measure",
    why="A rate shrinking by a fixed share toward zero would otherwise show that share as its yearly change "
        "for ever; below this rate the change is read as an absolute one.")
SPIN_UP_UNMET_FLOOR = declare(
    "SPIN_UP_UNMET_FLOOR", 1.0, kind="temporary_heuristic",
    unit="food floor units short below which a change in unmet need is measured against this instead",
    source=None, confidence="D", retire="Complaints/473: a spin-up that settles needs no floor on its measure",
    why="Unmet need is zero in a fed economy; a change from nothing to a fraction of one floor unit is not "
        "an economy that has stopped settling.")

# the state's scalar quantities and the floor each is measured against (zero: purely relative)
QUANTITY_FLOORS = {"price_level": 0.0, "rate": SPIN_UP_RATE_FLOOR, "real_output": 0.0, "hired_hours": 0.0,
                   "inventory_value": 0.0, "unmet_need": SPIN_UP_UNMET_FLOOR}


def change_gap(new, old, floor=0.0):
    """|new - old| over the larger of |old| and `floor`; none to none is no change and none to some is whole."""
    base = max(abs(old), floor)
    if base <= 0.0:
        return 0.0 if new == old else 1.0
    return abs(new - old) / base


def price_gap(new_prices, old_prices):
    """The largest relative change among goods priced in both years (a good with no earlier price is skipped)."""
    return max((change_gap(new_prices.get(good, 0.0), old) for good, old in old_prices.items() if old > 0.0),
               default=0.0)


def state_gaps(before, after):
    """{quantity: change between two states}; "prices" is the largest relative change of the watched prices."""
    gaps = {name: change_gap(after[name], before[name], floor) for name, floor in QUANTITY_FLOORS.items()
            if name in before and name in after}
    gaps["prices"] = price_gap(after["prices"], before["prices"])
    return gaps


def window_gaps(states):
    """{quantity: largest change between consecutive states}; None when fewer than two states are given."""
    if len(states) < 2:
        return None
    worst = {}
    for before, after in zip(states, states[1:]):
        for name, gap in state_gaps(before, after).items():
            worst[name] = max(gap, worst.get(name, 0.0))
    return worst
