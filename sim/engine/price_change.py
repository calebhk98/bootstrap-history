"""How far a price moved, relative to its size, for a price of either sign."""
from sim.constants import declare

PRICE_CHANGE_SCALE_FLOOR_HOURS_PER_UNIT = declare(
    "PRICE_CHANGE_SCALE_FLOOR_HOURS_PER_UNIT", 1e-9, kind="temporary_heuristic",
    unit="labour-hours per unit", source=None, confidence="D",
    why="A price crossing zero has no size to be relative to, so a change is measured against at least "
        "this much; it keeps a price near zero from reading as converged while it still moves.")


def relative_price_change(previous_price, new_price):
    return abs(new_price - previous_price) / max(abs(previous_price), PRICE_CHANGE_SCALE_FLOOR_HOURS_PER_UNIT)


def reference_prices_for_demand(prices):
    """`prices` with a negative price (a disposal cost) replaced by its size, so a demand search that
    centres on the current price can still see whether the waste has found a buyer."""
    return {material: abs(price) for material, price in prices.items()}
