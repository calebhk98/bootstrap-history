"""The base rate the credit market aims at: where the funds lenders offer meet the funds borrowers request.

Lenders ask a rate that covers what their money earns elsewhere and the loss they expect; a borrower pays that base
rate plus its own premium. The target is the crossing of the cumulative funds offered (each lender's amount at its ask)
with the cumulative funds requested (each borrower's amount at its ceiling), so it moves smoothly as lenders or borrowers
change rather than jumping to one marginal party's limit. Where borrowers queue for scarce funds, `credit.clear_with_cause`
rations the queue by quantity (the least risky borrower first), as in the agent-based credit models (Eurace@Unibi sets a
loan rate from a base rate and a default markup, Caiani et al. 2016 ration case by case).
"""
from typing import Optional, Sequence, Tuple

from .order_book import supply_demand_crossing


def base_rate_target(floors: Sequence[Tuple[float, float]], caps: Sequence[Tuple[float, float]]) -> Optional[float]:
    """`floors` are (ask, funds) of the lenders, `caps` (highest base rate, amount) of the borrowers who can pay the
    cheapest ask. The rate where the funds offered meet the funds requested."""
    return supply_demand_crossing(floors, caps)
