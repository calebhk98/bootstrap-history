"""How much capacity a producer sheds when its realised cash flow after every cost is negative.

`shed_share(net_earnings_history, revenue_history)` -> the share of capacity to close this year: the share of
the remembered outlay (revenue less earnings: wages, inputs, rent, interest, plant wear) that revenue failed to
cover, no more than a year's change in output (producers.OUTPUT_CHANGE_SHARE_PER_YEAR). A business covering
its costs sheds nothing; one covering nine tenths of them runs a tenth smaller.
"""
from typing import Sequence

from .producers import OUTPUT_CHANGE_SHARE_PER_YEAR


def shed_share(net_earnings_history: Sequence[float], revenue_history: Sequence[float]) -> float:
    if not net_earnings_history or not revenue_history:
        return 0.0
    earnings = sum(net_earnings_history) / len(net_earnings_history)
    revenue = sum(revenue_history) / len(revenue_history)
    outlay = revenue - earnings
    if earnings >= 0.0 or outlay <= 0.0:
        return 0.0
    return min(OUTPUT_CHANGE_SHARE_PER_YEAR, -earnings / outlay)
