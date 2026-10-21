"""The year's secondary trading in the economy's record: holders of shares and of loans sell to savers.

What is traded: a holder's part of a producer's equity (`record.shares`), and a loan or bond a lender holds (a
contract of the shared registry; a sale is a change of lender, the buyer paying the price). A household's own debts,
which pledge its title or bind it, and a bank's deposits are not traded. A bond in this record is a
loan the lender may sell: any contract that is not a household's own debt or a deposit is a claim a lender can sell
once the society holds the bond market. The price of a claim is set in secondary_market.py; this module builds the
asks and bids from the record and books the trades.

A holder asks what the claim is worth to it: the present value of what it is expected to pay, discounted at the
lowest rate the holder takes as a lender plus the premium for its issuer's risk. A holder short of cash (it asked
for a loan to meet its floors) asks the worth at the rate it would pay to borrow, which is lower, so it sells for
less than it values the claim rather than borrow dearer. A saver bids what the claim is worth at the rate it asks
as a lender plus the issuer's premium, with the funds it offered the credit market this year. Trading needs the
institution the society must hold (`SHARE_TRADING`, `BOND_MARKET`); without it nothing is asked or bid.
"""
import dataclasses
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from sim.world import capital_market

from . import banks, credit, credit_claims, secondary_market, shares
from .secondary_market import Ask, Bid, Trade
from .types import AgentId, FundsOffer, Loan, Transfer

SHARE_TRADING = "share_trading"       # the institution a society must hold for its holders to sell shares on
BOND_MARKET = "bond_market"           # the institution a society must hold for its lenders to sell loans and bonds on
SHARE_ITEM = "share:"
LOAN_ITEM = "loan:"
SALE_PURPOSE = "secondary sale"
EPSILON = 1e-9


@dataclasses.dataclass(frozen=True)
class Shortfall:
    """What a household short of cash needs, and the most it would pay to borrow it."""
    amount: float
    borrowing_rate: float


def tradable(record, loan: Loan) -> bool:
    """A claim a lender may sell: not a deposit with a bank, not a household's own debt (it pledges land or binds it)."""
    return (not banks.is_deposit(record, loan) and loan.borrower not in record.cohorts and not loan.collateral_tile
            and loan.principal > EPSILON)


def issuer_premium(record, issuer: AgentId, debts: Mapping[AgentId, float], arrears: Mapping[AgentId, float],
                   security: float) -> float:
    """What a buyer asks over its own rate for the issuer's risk: the premium a lender would charge it, against the
    `security` that stands ahead of or behind the claim."""
    return credit.risk_premium(debts.get(issuer, 0.0), security, arrears.get(issuer, 0.0))


def loan_value(loan: Loan, rate: float) -> float:
    """What a lender expects to collect on a contract, discounted at `rate`: the interest on what is outstanding and
    the principal as it falls due (in equal instalments, as credit.service collects it), and the arrears it does not
    doubt."""
    years = max(1, int(round(loan.years_left))) if loan.years_left < 1e6 else 1
    growth = 1.0 + max(-0.99, rate)
    outstanding = loan.principal
    value = 0.0
    for year in range(1, years + 1):
        installment = outstanding / (years - year + 1)
        value += (outstanding * loan.rate + installment) / growth ** year
        outstanding -= installment
    return value + (credit_claims.claim_value(loan) - loan.principal)


def share_value(record, producer_id: AgentId, rate: float, rate_floor: float) -> float:
    """The whole equity of a producer at `rate`: the present value of the dividend it paid last."""
    return shares.whole_value(record, producer_id, rate, rate_floor)


def _own_rate(offers: Mapping[AgentId, FundsOffer], agent: AgentId, market_rate: float) -> float:
    offer = offers.get(agent)
    return offer.minimum_rate if offer is not None else market_rate


def _loan_items(record, forced: Mapping[AgentId, Shortfall]) -> List[Loan]:
    """The loans a household lender or a lender short of cash may sell."""
    return sorted((loan for loan in record.loans if tradable(record, loan) and (loan.lender in record.cohorts or loan.lender in forced)),
                  key=lambda loan: loan.loan_id)


def asks_and_bids(setup, record, offers: Sequence[FundsOffer], short: Mapping[AgentId, Shortfall], market_rate: float,
                  rate_floor: float, institutions: Sequence[str], sellers: Optional[Sequence[AgentId]] = None,
                  ) -> Tuple[List[Ask], List[Bid]]:
    """Every holder's asks and every saver's bids for the claims its society lets it trade. `short` names the holders
    (households, or any lender such as a bank) that need cash; with `sellers` only those holders ask."""
    money = setup.currency_id
    offered = {offer.lender: offer for offer in offers if offer.currency == money and offer.lender in record.cohorts
               and offer.amount > EPSILON}
    debts = credit_claims.principal_by_borrower(record.loans)
    arrears = credit_claims.arrears_history(record.loans, record.remembered_defaults)
    needed = {holder: shortfall.amount for holder, shortfall in short.items()}
    asks: List[Ask] = []
    bids: List[Bid] = []
    allowed = None if sellers is None else set(sellers)
    if SHARE_TRADING in institutions:
        for producer_id in sorted(record.shares):
            if producer_id not in record.producers:
                continue
            premium = issuer_premium(record, producer_id, debts, arrears,
                                     share_value(record, producer_id, market_rate, rate_floor))
            item = SHARE_ITEM + producer_id
            for holder, part in sorted(record.shares[producer_id].items()):
                if holder in record.cohorts and part > EPSILON and (allowed is None or holder in allowed):
                    asks.extend(_asks(item, holder, part, _own_rate(offered, holder, market_rate) + premium, needed, short.get(holder),
                                      premium, lambda rate: share_value(record, producer_id, rate, rate_floor)))
            bids.extend(Bid(buyer, item, offer.amount, share_value(record, producer_id, offer.minimum_rate + premium, rate_floor))
                        for buyer, offer in sorted(offered.items()))
    if BOND_MARKET in institutions:
        for loan in _loan_items(record, short):
            premium = issuer_premium(record, loan.borrower, debts, arrears, loan.collateral_value)
            item = LOAN_ITEM + loan.loan_id
            per_unit = lambda rate, each=loan: loan_value(each, rate) / each.principal
            if allowed is None or loan.lender in allowed:
                asks.extend(_asks(item, loan.lender, loan.principal, _own_rate(offered, loan.lender, market_rate) + premium, needed,
                                  short.get(loan.lender), premium, per_unit))
            bids.extend(Bid(buyer, item, offer.amount, per_unit(offer.minimum_rate + premium))
                        for buyer, offer in sorted(offered.items()))
    return asks, bids


def _asks(item: str, holder: AgentId, quantity: float, own_rate: float, needed: Dict[AgentId, float],
          shortfall: Optional[Shortfall], premium: float, value_at) -> List[Ask]:
    """The holder's asks for one claim: all of it at what it is worth at the holder's own rate; where the holder is
    short of cash, the part that raises what it still needs at the lower worth at the rate it would pay to borrow
    (`needed` falls by what this claim is asked to raise, so the next claim raises only the rest)."""
    ordinary = value_at(own_rate)
    if shortfall is None or needed.get(holder, 0.0) <= EPSILON:
        return [Ask(holder, item, quantity, ordinary)]
    hurried = min(ordinary, value_at(max(own_rate, shortfall.borrowing_rate + premium)))
    units = quantity if hurried <= 0.0 else min(quantity, needed[holder] / hurried)
    needed[holder] -= units * hurried
    asks = [Ask(holder, item, units, hurried)]
    if quantity - units > EPSILON:
        asks.append(Ask(holder, item, quantity - units, ordinary))
    return asks


def apply(record, trades: Sequence[Trade], money: str) -> Dict[AgentId, float]:
    """Book the trades: buyers pay sellers, and the shares or loans change hands. Returns the money each buyer spent."""
    spent: Dict[AgentId, float] = {}
    payments = []
    loans_by_id = {loan.loan_id: loan for loan in record.loans}
    for trade in trades:
        payments.append(Transfer(trade.buyer, trade.seller, money, trade.quantity * trade.price, SALE_PURPOSE))
        spent[trade.buyer] = spent.get(trade.buyer, 0.0) + trade.quantity * trade.price
        if trade.item.startswith(SHARE_ITEM):
            _move_share(record, trade)
        elif trade.item.startswith(LOAN_ITEM):
            _move_loan(record, loans_by_id[trade.item[len(LOAN_ITEM):]], trade)
    record.book.transfer_many(payments)
    return spent


def _move_share(record, trade: Trade) -> None:
    held = record.shares[trade.item[len(SHARE_ITEM):]]
    held[trade.seller] = held.get(trade.seller, 0.0) - trade.quantity
    if held[trade.seller] <= EPSILON:
        del held[trade.seller]
    held[trade.buyer] = held.get(trade.buyer, 0.0) + trade.quantity


def _move_loan(record, loan: Loan, trade: Trade) -> None:
    """The buyer takes `quantity` of the loan's principal, with its part of the arrears, as a contract of its own."""
    part = min(1.0, trade.quantity / loan.principal) if loan.principal > 0.0 else 1.0
    if part >= 1.0 - EPSILON:
        loan.lender = trade.buyer
        return
    bought = dataclasses.replace(loan, contract_id="%s|%s" % (loan.loan_id, trade.buyer), lender=trade.buyer,
                                 principal=loan.principal * part, arrears=loan.arrears * part,
                                 arrears_interest=loan.arrears_interest * part,
                                 collateral_value=loan.collateral_value * part, collateral_share=loan.collateral_share * part)
    loan.principal -= bought.principal
    loan.arrears -= bought.arrears
    loan.arrears_interest -= bought.arrears_interest
    loan.collateral_value -= bought.collateral_value
    loan.collateral_share -= bought.collateral_share
    record.loans.append(bought)


def run(setup, record, offers: Sequence[FundsOffer], short: Mapping[AgentId, Shortfall], market_rate: float,
        institutions: Sequence[str], sellers: Optional[Sequence[AgentId]] = None) -> Tuple[List[FundsOffer], List[Trade]]:
    """The year's secondary trading. Returns the offers with what each buyer spent taken off, and the trades. With
    `sellers`, only those holders sell (a bank that must raise cash)."""
    if SHARE_TRADING not in institutions and BOND_MARKET not in institutions:
        return list(offers), []
    asks, bids = asks_and_bids(setup, record, offers, short, market_rate, capital_market.RATE_FLOOR_SHARE * setup.opening_rate,
                               institutions, sellers)
    trades = secondary_market.clear(asks, bids)
    if not trades:
        return list(offers), []
    spent = apply(record, trades, setup.currency_id)
    return [dataclasses.replace(offer, amount=offer.amount - spent.get(offer.lender, 0.0)) if offer.lender in spent else offer
            for offer in offers], trades
