"""How far a market's price moves in one year under the clearing rules: to the price that clears it, but by no more than a
set share of last year's price, up or down by the same factor. Inside that band the market clears; beyond it the short
side is served in full and the long side goes short (`goods_market.clear_at_price`), so a market with next to nothing on
offer rations its buyers and does not take all their coin, and a glut leaves stock with its sellers."""
from typing import Optional

from sim.constants import declare

PRICE_MOVE_LIMIT_PER_YEAR = declare(
    "PRICE_MOVE_LIMIT_PER_YEAR", 0.25, kind="temporary_heuristic",
    unit="share of last year's price a market's price may rise by in a year (it may fall by the same factor)",
    source=None, confidence="D",
    retire="Complaints/473: a measured spread of year-on-year price moves by kind of good (a staple in a bad harvest, a made good) gives it",
    why="Buyers set aside for a need what it cost last year and a margin (households_orders.FLOOR_BUDGET_PRICE_MARGIN), so a "
        "price that rises further in one year only moves coin, not goods: the same units are sold and the buyers' whole "
        "budgets go with them. Held to the margin buyers allow for, the price still climbs every year a shortage lasts, "
        "which is the signal that brings sellers in. No source found for the figure; it is set equal to that margin.")


def within_a_years_move(clearing_price: Optional[float], last_price: Optional[float],
                        limit: float = PRICE_MOVE_LIMIT_PER_YEAR) -> Optional[float]:
    """The year's price: `clearing_price` held within `limit` of `last_price` (up to it times one plus the limit, down
    to it over one plus the limit); the clearing price itself where the market has no price yet. None where there is no
    clearing price."""
    if clearing_price is None or last_price is None or not last_price > 0.0:
        return clearing_price
    return min(max(clearing_price, last_price / (1.0 + limit)), last_price * (1.0 + limit))
