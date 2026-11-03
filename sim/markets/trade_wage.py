"""The one rule for the wage of a trade the labour market has not priced, shared by the seat's staff bids and the wage screens."""
from sim.economy import api as economy_api


def unpriced_trade_wage(economy, trade):
    """The wage per hour (economy units) of a trade no market has priced yet: the wage the economy opened with for it, else the
    unskilled wage plus the trade's training premium; None when neither exists."""
    opening = economy_api.opening_wage(economy, trade)
    if opening and opening > 0.0:
        return opening
    unskilled = economy_api.wages_by_trade_weighted(economy).get(economy_api.unskilled_trade(economy))
    if unskilled is None:
        return None
    return unskilled * (1.0 + economy_api.trade_premium_of(economy, trade))
