"""The base rate the credit market aims at: the lenders' price when borrowers queue for funds.

Lenders ask a rate that covers what their money earns elsewhere and the loss they expect; a borrower pays that base
rate plus its own premium. Where funds are plentiful the rate is the dearest ask needed to fund the demand. Where
borrowers queue for scarce funds the rate stays with the lenders: it is the dearest ask among those who lend, and the
queue is rationed by quantity (the least risky borrower first, in `credit.clear_with_cause`), as in the agent-based
credit models (Eurace@Unibi sets a loan rate from a base rate and a default markup, Caiani et al. 2016 ration case by
case). It is not the cap of whichever borrower is last in the queue, which a few units of lendable money would move
from year to year.
"""
from typing import Optional, Sequence, Tuple

from sim.constants import declare

from .labour import clearing_point

MATERIAL_LENDER_SHARE = declare(
    "MATERIAL_LENDER_SHARE", 0.01, kind="temporary_heuristic",
    unit="share of the funds on offer a lender must hold before its ask can set the rate", source=None, confidence="D",
    retire="Complaints/641: the rate is the loan-weighted price of the funds actually lent, not a marginal ask",
    why="A lender holding a negligible sum cannot fund a market, so its ask does not price loans others make; the "
        "size of 'negligible' is not derived.")


def base_rate_target(floors: Sequence[Tuple[float, float]], caps: Sequence[Tuple[float, float]]) -> Optional[float]:
    """`floors` are (ask, funds) of the lenders, `caps` (highest base rate, amount) of the borrowers who can pay
    the cheapest ask. The plain clearing point, lowered to the dearest ask of the lenders with a worthwhile sum
    when borrowers who would pay it ask for more than those lenders hold."""
    rate = clearing_point(floors, caps)
    if rate is None or not floors or not caps:
        return rate
    total_funds = sum(funds for _ask, funds in floors if funds > 0.0)
    lending = [(ask, funds) for ask, funds in floors if ask <= rate + 1e-12 and funds > 0.0]
    demand = sum(amount for cap, amount in caps if cap >= rate - 1e-12 and amount > 0.0)
    if demand <= sum(funds for _ask, funds in lending) * (1.0 + 1e-9):
        return rate
    worthwhile = [ask for ask, funds in lending if funds >= MATERIAL_LENDER_SHARE * total_funds]
    return max(worthwhile) if worthwhile else rate
