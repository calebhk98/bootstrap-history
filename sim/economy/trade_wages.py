"""The one rule for the wage per hour a trade is priced at, wherever a bid, a quote or a crew needs it:
the wage its labour market paid (the memory holds only wages above zero, `labour_state.mirror_wages`, so a wage that
is there is positive), else the wage the economy opened with for the trade scaled to today's money
(`MarketMemory.opening_wage_level`: an opening-year nominal wage is out of date after inflation and after the
spin-up's rebase), else the unskilled
wage of the same scope plus the trade's training premium; None when none exists.

The unskilled wage is of the scope the caller asks about: one labour area (`wage_in_area`, `wage_in_view`) or the
country's hours-weighted figure (sim/economy/api.py `unpaid_trade_wage`). The opening wage is a labour quote, positive
by construction (sim/markets/port_setup.py).

Households differ on purpose: a household is a seller, and what it faces in a market with no recorded wage is its own
reservation wage (`faced_wage`), the least it will work for, not the wage an employer would be billed. A tax or land
bid that reads a wage for a cohort reads the recorded one and does without when there is none."""
from typing import Optional

from .market_memory import market_key
from .year_labour import trade_premium


def priced_trade_wage(setup, trade: str, paid: Optional[float], unskilled: Optional[float],
                      opening_wage_level: Optional[float]) -> Optional[float]:
    """The wage per hour of `trade` given what its market paid (None if nothing), the unskilled wage of the same
    scope (None if none) and the level the opening wages are scaled by (`MarketMemory.opening_wage_level`; None for a
    scope the opening set no wages for, a partner country's)."""
    if paid is not None:
        return paid
    opening = None if opening_wage_level is None else setup.opening_wages.get(trade)
    if opening is not None:
        return opening * opening_wage_level
    if unskilled is None:
        return None
    return unskilled * (1.0 + trade_premium(setup, trade))


def wage_in_area(setup, memory, trade: str, area: str) -> Optional[float]:
    """The wage per hour of `trade` in a labour area, on the area's unskilled wage and the memory's price level."""
    return priced_trade_wage(setup, trade, memory.wages.get(market_key(trade, area)),
                             memory.wages.get(market_key(setup.unskilled_trade, area)),
                             memory.opening_wage_level(setup.currency_id))


def wage_in_view(setup, view, trade: str, area: str) -> Optional[float]:
    """`wage_in_area` read through a market view."""
    return priced_trade_wage(setup, trade, view.wage(trade, area), view.wage(setup.unskilled_trade, area),
                             view.opening_wage_level(setup.currency_id))


def faced_wage(recorded: Optional[float], reservation: float) -> float:
    """The wage per hour a household seller faces: the recorded wage of its market, else its reservation wage."""
    return reservation if recorded is None else recorded
