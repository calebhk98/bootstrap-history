"""The market for new shares: producers sell parts of their equity and savers buy them at one clearing price.

Pure functions. A share is a part of a producer's whole equity and earns that part of its dividends. What the
whole equity is worth to a buyer is the present value of the dividends the producer is expected to pay,
discounted at the buyer's required rate plus a premium for the issuer's risk, and no buyer pays more. Buyers are taken cheapest-required-rate first
until the issues are covered; the last buyer needed sets the rate for everyone (never below the market rate), so
the price falls when only buyers who ask a high rate are left, and the issuer sells more of itself for the same
money. Issues that the buyers' funds cannot cover are filled in proportion.
"""
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from sim.world import capital_market

from .types import AgentId


@dataclass(frozen=True)
class ShareIssue:
    issuer: AgentId
    amount: float                # the money the issuer wants to raise
    expected_dividend: float     # the yearly dividend the whole equity is expected to pay once the money is spent
    available: float = 1.0       # the part of the whole equity not yet sold
    premium: float = 0.0         # what a buyer asks over the market rate for the issuer's risk (a lender's premium)


@dataclass(frozen=True)
class ShareBid:
    buyer: AgentId
    funds: float                 # the most the buyer will put into shares this year
    required_rate: float         # the lowest yearly return it accepts


@dataclass(frozen=True)
class ShareFill:
    issuer: AgentId
    buyer: AgentId
    paid: float
    share: float                 # part of the issuer's whole equity bought


def equity_value(expected_dividend: float, rate: float, rate_floor: float = 1e-9) -> float:
    """What a whole equity paying `expected_dividend` a year for good is worth at `rate`: its present value. The
    rate is held at the floor so a nil rate does not make a share worth infinity."""
    return capital_market.perpetuity_value(expected_dividend, rate, rate_floor)


def clear(issues: Sequence[ShareIssue], bids: Sequence[ShareBid], market_rate: float,
          rate_floor: float = 1e-9) -> Tuple[List[ShareFill], float]:
    """(fills, clearing rate). The clearing rate is what every share bought is discounted at; the price of an
    issuer's whole equity is `equity_value(expected_dividend, clearing rate)`."""
    issues = sorted((issue for issue in issues if issue.amount > 0.0 and issue.expected_dividend > 0.0
                     and issue.available > 0.0), key=lambda issue: issue.issuer)
    bids = sorted((bid for bid in bids if bid.funds > 0.0), key=lambda bid: (bid.required_rate, bid.buyer))
    wanted = sum(issue.amount for issue in issues)
    if wanted <= 0.0 or not bids:
        return [], market_rate
    joined: List[ShareBid] = []
    funds = 0.0
    for bid in bids:
        joined.append(bid)
        funds += bid.funds
        if funds >= wanted:
            break
    rate = max(market_rate, joined[-1].required_rate)
    raised = min(wanted, funds)
    fills: List[ShareFill] = []
    for issue in issues:
        money = issue.amount * raised / wanted
        whole = equity_value(issue.expected_dividend, rate + issue.premium, rate_floor)
        if whole <= 0.0:
            continue
        share = min(issue.available, money / whole)
        # the buyers pay for the share sold, in proportion to the funds they brought
        paid_for_it = share * whole
        for bid in joined:
            part = paid_for_it * bid.funds / funds
            if part > 0.0:
                fills.append(ShareFill(issue.issuer, bid.buyer, part, share * bid.funds / funds))
    return fills, rate
