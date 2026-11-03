"""The one rule for the wage a trade is priced at when its labour market has paid none: the wage the economy opened with
for the trade, else the unskilled wage plus the trade's training premium. Staff bids, the seat's quote and merchants'
crews all price an unpaid trade by it."""
from typing import Optional

from .market_memory import market_key
from .year_labour import trade_premium


def unpaid_trade_wage(setup, trade: str, unskilled: Optional[float]) -> Optional[float]:
    """The wage per hour of `trade` where its market has no wage, given the unskilled wage to build on; None when
    neither the opening wage nor the unskilled wage exists."""
    opening = setup.opening_wages.get(trade)
    if opening and opening > 0.0:
        return opening
    if unskilled is None:
        return None
    return unskilled * (1.0 + trade_premium(setup, trade))


def wage_in_area(setup, memory, trade: str, area: str) -> Optional[float]:
    """The wage per hour of `trade` in a labour area: what the area's market paid last, else the unpaid-trade wage
    on the area's unskilled wage; None when none exists."""
    paid = memory.wages.get(market_key(trade, area))
    if paid is not None:
        return paid
    return unpaid_trade_wage(setup, trade, memory.wages.get(market_key(setup.unskilled_trade, area)))
