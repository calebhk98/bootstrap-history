"""Shares in producers, on the economy's record: who holds what part of each producer and what the dividends are.

`record.shares[producer][holder]` is the part of the producer's whole equity a holder bought; what no one bought
is the owner's, and goes to the owner's tile as before (`ownership.spread`). A dividend is split by these parts
(`split_dividend`). A producer whose expansion lenders would not fully fund sells shares for the rest
(`raise_equity`): the buyers are the households with savings left after the year's lending, the price is the
present value of the dividends the producer is expected to pay once the new plant is built (share_market.py),
and the money reaches the producer, which builds with it through the ordinary expansion path.
"""
from typing import Dict, List, Mapping, Sequence

from sim.world import capital_market

from . import credit, credit_claims, share_market
from .share_market import ShareBid, ShareFill, ShareIssue
from .types import AgentId, FundsOffer, LoanRequest, Transfer

EXPAND_PURPOSE = "expand"      # the purpose producers_close gives a loan for plant that grows capacity
SHARE_PURPOSE = "share issue"
SHARE_DIVIDEND_PURPOSE = "dividend on shares"    # paid to the holder itself; not shared on across its tile
EPSILON = 1e-9


def outside_share(record, producer_id: AgentId) -> float:
    """The part of the producer's equity held by buyers of its shares."""
    return sum((record.shares.get(producer_id) or {}).values())


def note_dividend(record, producer_id: AgentId, payout: Sequence[Transfer]) -> None:
    """Remember the dividend a producer paid at its year's close; the expectation the next buyer prices on."""
    record.last_dividends[producer_id] = sum(transfer.amount for transfer in payout if transfer.purpose == "dividend")


def split_dividend(record, payment: Transfer) -> List[Transfer]:
    """A producer's dividend as payments: each holder of its shares its part, the rest to its owner (paid on
    to the owner's tile by the caller). Other payments pass through."""
    if payment.purpose != "dividend":
        return [payment]
    held = record.shares.get(payment.payer)
    if not held or payment.payer not in record.producers:
        return [payment]
    paid = [Transfer(payment.payer, holder, payment.currency, payment.amount * share, SHARE_DIVIDEND_PURPOSE)
            for holder, share in sorted(held.items()) if share > EPSILON and holder in record.cohorts]
    rest = payment.amount - sum(transfer.amount for transfer in paid)
    if rest > EPSILON:
        paid.append(Transfer(payment.payer, payment.payee, payment.currency, rest, payment.purpose))
    return paid


def whole_value(record, producer_id: AgentId, rate: float, rate_floor: float) -> float:
    """What the producer's whole equity is worth: the present value of the dividend it paid last."""
    return share_market.equity_value(record.last_dividends.get(producer_id, 0.0), rate, rate_floor)


def prune(record) -> None:
    """Drop the shares of producers that have closed."""
    for producer_id in [each for each in record.shares if each not in record.producers]:
        del record.shares[producer_id]
        record.last_dividends.pop(producer_id, None)
    for producer_id in [each for each in record.last_dividends if each not in record.producers]:
        del record.last_dividends[producer_id]


def issues_for(record, requests: Sequence[LoanRequest], market_rate: float) -> List[ShareIssue]:
    """One issue per producer whose plant request lenders left unmet and whose plant would earn more than its
    shares cost: the money it lacks, the dividend expected once that money is plant (the dividend it pays now plus
    what the money earns), the part still unsold, and the premium a lender would charge it, which a buyer of its
    shares, who ranks behind its lenders, asks at least."""
    debts = credit_claims.principal_by_borrower(record.loans)
    arrears = credit_claims.arrears_history(record.loans, record.remembered_defaults)
    issues = []
    for request in sorted(requests, key=lambda each: each.borrower):
        if request.purpose != EXPAND_PURPOSE or request.borrower not in record.producers or request.amount <= 0.0:
            continue
        premium = credit.risk_premium(debts.get(request.borrower, 0.0) + request.amount, request.collateral_value,
                                      arrears.get(request.borrower, 0.0))
        if request.maximum_rate <= market_rate + premium:
            continue
        expected = record.last_dividends.get(request.borrower, 0.0) + request.amount * request.maximum_rate
        issues.append(ShareIssue(request.borrower, request.amount, expected,
                                 max(0.0, 1.0 - outside_share(record, request.borrower)), premium))
    return issues


def bids_from(record, offers: Sequence[FundsOffer], lent_by_lender: Mapping[AgentId, float]) -> List[ShareBid]:
    """What each household saver has left after its lending, asking at least the rate it asked as a lender."""
    return [ShareBid(offer.lender, offer.amount - lent_by_lender.get(offer.lender, 0.0), offer.minimum_rate)
            for offer in offers if offer.lender in record.cohorts
            and offer.amount - lent_by_lender.get(offer.lender, 0.0) > EPSILON]


def apply(record, fills: Sequence[ShareFill], currency: str) -> Dict[AgentId, float]:
    """Book the sales: the buyers pay the producers, the producers' earlier holders are diluted by the part sold,
    and the buyers hold it. Returns the money each producer raised."""
    raised: Dict[AgentId, float] = {}
    sold: Dict[AgentId, float] = {}
    for fill in fills:
        raised[fill.issuer] = raised.get(fill.issuer, 0.0) + fill.paid
        sold[fill.issuer] = sold.get(fill.issuer, 0.0) + fill.share
    record.book.transfer_many([Transfer(fill.buyer, fill.issuer, currency, fill.paid, SHARE_PURPOSE) for fill in fills])
    for issuer, part in sorted(sold.items()):
        held = record.shares.setdefault(issuer, {})
        for holder in held:
            held[holder] *= 1.0 - part
        for fill in fills:
            if fill.issuer == issuer:
                held[fill.buyer] = held.get(fill.buyer, 0.0) + fill.share
    return raised


def raise_equity(record, currency: str, unmet: Sequence[LoanRequest], offers: Sequence[FundsOffer],
                 loans: Sequence, market_rate: float, rate_floor: float) -> Dict[AgentId, float]:
    """The producers whose plant request went unfunded sell shares to the savers who still hold funds; the money
    each raised (empty when none did)."""
    prune(record)
    lent: Dict[AgentId, float] = {}
    for loan in loans:
        lent[loan.lender] = lent.get(loan.lender, 0.0) + loan.principal
    issues = issues_for(record, unmet, market_rate)
    bids = bids_from(record, offers, lent)
    if not issues or not bids:
        return {}
    fills, _rate = share_market.clear(issues, bids, market_rate, rate_floor)
    return apply(record, fills, currency)


def rate_floor_of(setup) -> float:
    return capital_market.RATE_FLOOR_SHARE * setup.opening_rate


def held_value(record, holder: AgentId, rate: float, rate_floor: float) -> float:
    """What a holder's shares are worth at the market: its part of each producer's equity at the present value of
    that producer's dividends."""
    return sum(held[holder] * whole_value(record, producer_id, rate, rate_floor)
               for producer_id, held in record.shares.items() if holder in held and producer_id in record.producers)
