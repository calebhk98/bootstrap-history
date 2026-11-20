"""How far the agent economy moved between hidden spin-up years: pure arithmetic over per-year states.

A state is {"price_level", "rate", "prices": {good: price}, "price_weights": {good: share of the watched goods'
spending}, plus the quantities of `QUANTITY_FLOORS`, and "food_need"}. A change is relative to the earlier value, with the earlier value no smaller than a floor where the
quantity can sit near zero: the rate against a declared floor, unmet need against the economy's whole food need
(the food floor units its people need, sim/economy/spin_up_state.py `food_floor_units`), so a shortfall on one tile is read as the share of
the economy's food it is, and producers' inventory value against the year's real output (both are quantities at the opening's
prices): the goods markets clear inside the year, so the stock left is a small residual of a year's output, and a change in it
is read as the share of a year's output it is (the owner's answer to question 11 of Complaints/reports/473-owner-questions.md).
"""
from sim.constants import declare

SPIN_UP_RATE_FLOOR = declare(
    "SPIN_UP_RATE_FLOOR", 0.01, kind="temporary_heuristic",
    unit="interest rate below which a change in the rate is measured against this instead of the rate",
    source=None, confidence="D", retire="Complaints/473: a spin-up that settles needs no floor on its measure",
    why="A rate shrinking by a fixed share toward zero would otherwise show that share as its yearly change "
        "for ever; below this rate the change is read as an absolute one.")
# the state's scalar quantities and the floor each is measured against (zero: purely relative; unmet need's is the
# earlier state's food need and inventory value's its real output, `state_gaps`)
QUANTITY_FLOORS = {"price_level": 0.0, "rate": SPIN_UP_RATE_FLOOR, "real_output": 0.0, "hired_hours": 0.0,
                   "inventory_value": 0.0, "unmet_need": 0.0}


def change_gap(new, old, floor=0.0):
    """|new - old| over the larger of |old| and `floor`; none to none is no change and none to some is whole."""
    base = max(abs(old), floor)
    if base <= 0.0:
        return 0.0 if new == old else 1.0
    return abs(new - old) / base


def price_gaps(new_prices, old_prices):
    """{good: change} for the goods priced last year: a good priced in both years by its relative change, one priced last
    year and not now by a whole change; a good with no price last year is skipped."""
    return {good: 1.0 if new_prices.get(good) is None else change_gap(new_prices[good], old)
            for good, old in old_prices.items() if old is not None and old > 0.0}


def price_gap(new_prices, old_prices, weights=None):
    """The watched prices' change as one figure: each good's change (`price_gaps`) by its share of the basket's spending
    (`weights`, over all the watched goods), so a good that is a sliver of the spending moves the figure by a sliver
    whatever its own price does, and one with no price last year adds nothing. With no shares every good priced last
    year counts alike. None priced last year is no change."""
    gaps = price_gaps(new_prices, old_prices)
    if not gaps:
        return 0.0
    if not weights:
        return sum(gaps.values()) / len(gaps)
    total = sum(weights.values())
    return sum(weights.get(good, 0.0) * gap for good, gap in gaps.items()) / total if total > 0.0 else 0.0


def worst_price_change(states):
    """(good, change): the watched good with the largest change between any two consecutive `states`; (None, 0.0) when
    no good changed or fewer than two states are given."""
    worst = (None, 0.0)
    for before, after in zip(states, states[1:]):
        for good, gap in price_gaps(after["prices"], before["prices"]).items():
            if gap > worst[1]:
                worst = (good, gap)
    return worst


def state_gaps(before, after):
    """{quantity: change between two states}; "prices" is the watched prices' change weighted by the earlier state's shares
    of spending ("price_weights", `price_gap`). A quantity
    stated before and gone now is a whole change; one stated in neither state is skipped."""
    gaps = {}
    for name, floor in QUANTITY_FLOORS.items():
        if before.get(name) is None:
            continue
        if name == "unmet_need":
            floor = before.get("food_need") or 0.0
        if name == "inventory_value":
            floor = before.get("real_output") or 0.0
        gaps[name] = 1.0 if after.get(name) is None else change_gap(after[name], before[name], floor)
    gaps["prices"] = price_gap(after["prices"], before["prices"], before.get("price_weights"))
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



def unsettled_cause(states):
    """Why a window of `states` cannot be called settled whatever its gaps, or None: fewer than two years, a pair of
    consecutive years with no watched good priced (as a trade) in both, or no real output or no hired hours in the last
    year (an economy that makes nothing does not move)."""
    if len(states) < 2:
        return "too_few_years"
    if any(not set(before["prices"]) & set(after["prices"]) for before, after in zip(states, states[1:])):
        return "no_price_in_two_years"
    for name in ("real_output", "hired_hours"):
        value = states[-1].get(name)
        if value is None:
            return name + "_not_measured"
        if value <= 0.0:
            return "zero_" + name
    return None
