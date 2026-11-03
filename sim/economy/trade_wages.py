"""The one rule for the wage per hour a trade is priced at, wherever a bid, a quote or a crew needs it:
the wage its labour market paid (a recorded zero is a wage), else the wage the economy opened with for the trade
scaled by the chained price level (an opening-year nominal wage is out of date after inflation), else the unskilled
wage of the same scope plus the trade's training premium; None when none exists.

The unskilled wage is of the scope the caller asks about: one labour area (`wage_in_area`, `wage_in_view`) or the
country's hours-weighted figure (sim/economy/api.py `unpaid_trade_wage`). The opening wage is a labour quote, positive
by construction (sim/markets/port_setup.py)."""
from typing import Optional

from .market_memory import market_key
from .year_labour import trade_premium


def priced_trade_wage(setup, trade: str, paid: Optional[float], unskilled: Optional[float],
                      price_level: float) -> Optional[float]:
    """The wage per hour of `trade` given what its market paid (None if nothing), the unskilled wage of the same
    scope (None if none) and the chained price level of the economy's currency."""
    if paid is not None:
        return paid
    opening = setup.opening_wages.get(trade)
    if opening is not None:
        return opening * price_level
    if unskilled is None:
        return None
    return unskilled * (1.0 + trade_premium(setup, trade))


def wage_in_area(setup, memory, trade: str, area: str) -> Optional[float]:
    """The wage per hour of `trade` in a labour area, on the area's unskilled wage and the memory's price level."""
    return priced_trade_wage(setup, trade, memory.wages.get(market_key(trade, area)),
                             memory.wages.get(market_key(setup.unskilled_trade, area)),
                             memory.price_levels.get(setup.currency_id, 1.0))


def wage_in_view(setup, view, trade: str, area: str) -> Optional[float]:
    """`wage_in_area` read through a market view."""
    return priced_trade_wage(setup, trade, view.wage(trade, area), view.wage(setup.unskilled_trade, area),
                             view.chained_price_level(setup.currency_id))
