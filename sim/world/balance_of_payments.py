"""Paying for goods that cross a border in the coin metal that crosses with them.

An economy holds a stock of coin. Imports are paid for by exports first; what exports do not cover
leaves as coin and arrives in the partner's stock, and a surplus brings coin in. A stock above or
below its opening level moves the economy's prices in proportion (more coin chasing the same goods),
so a deficit makes its goods cheaper and its imports dearer until flows balance. An economy cannot
pay out more coin than it holds.

Standalone: amounts in, amounts out; a caller supplies the opening stock and the money values.
"""
from sim.constants import declare

MONEY_STOCK_YEARS_OF_WAGES = declare(
    "MONEY_STOCK_YEARS_OF_WAGES", 0.5, kind="temporary_heuristic",
    unit="years of the working population's unskilled wages", source=None, confidence="D",
    why="Sets the opening coin stock of an economy whose money supply is not modelled: the stock "
        "is a fixed share of its yearly wage bill. Stands in for the real stock and its velocity.")
PRICE_LEVEL_PASS_THROUGH = declare(
    "PRICE_LEVEL_PASS_THROUGH", 1.0, kind="temporary_heuristic",
    unit="proportional change of traded prices per proportional change of the coin stock",
    source=None, confidence="D",
    why="Quantity theory with output and velocity held fixed: prices follow the coin stock one for "
        "one. The domestic revaluation of every price is not built; only traded prices follow.")
PRICE_LEVEL_FLOOR = declare(
    "PRICE_LEVEL_FLOOR", 0.05, kind="temporary_heuristic",
    unit="share of the opening price level", source=None, confidence="D",
    why="Keeps an emptied stock from pricing everything at zero; payments stop at an empty stock.")


def opening_stock_units(workers: float, wage_per_year: float) -> float:
    """Coin units an economy opens with."""
    return max(0.0, workers) * max(0.0, wage_per_year) * MONEY_STOCK_YEARS_OF_WAGES


def price_level(stock_units: float, opening_units: float) -> float:
    """Traded-price level against the opening one."""
    if opening_units <= 0.0:
        return 1.0
    return max(PRICE_LEVEL_FLOOR, stock_units / opening_units) ** PRICE_LEVEL_PASS_THROUGH


def coin_paid(net_value_owed: float, stock_units: float) -> float:
    """Coin units that leave a payer owing `net_value_owed` (negative: it is owed coin and none leaves);
    never more than the payer holds."""
    return max(0.0, min(net_value_owed, stock_units))
