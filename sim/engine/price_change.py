"""How far a price moved, relative to its size, for a price of either sign."""
from sim.constants import declare

PRICE_CHANGE_SCALE_FLOOR_HOURS_PER_UNIT = declare(
    "PRICE_CHANGE_SCALE_FLOOR_HOURS_PER_UNIT", 1e-9, kind="temporary_heuristic",
    unit="labour-hours per unit", source=None, confidence="D",
    why="A price crossing zero has no size to be relative to, so a change is measured against at least "
        "this much; it keeps a price near zero from reading as converged while it still moves.")


def relative_price_change(previous_price, new_price):
    return abs(new_price - previous_price) / max(abs(previous_price), PRICE_CHANGE_SCALE_FLOOR_HOURS_PER_UNIT)
