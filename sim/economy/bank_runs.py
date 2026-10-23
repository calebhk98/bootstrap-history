"""Depositors withdraw from a bank whose loss record threatens their deposit; an illiquid bank sells its loans or fails.

As the year opens each depositor weighs its deposit against what the bank is expected to lose. The bank's own loss
record (`record.loss_rates`, the share of what it has lent that it loses a year) times what it has lent is the loss it
expects; its capital absorbs that first, and what is left falls on the depositors, as a share of what the bank owes.
A depositor stays while the interest it asked as a lender covers that share, and withdraws its deposit when it does
not: those who ask least run first.

The bank pays the withdrawals from its cash. Short of cash it sells loans to savers at the secondary price (the price
that clears the savers' bids against what the bank asks, secondary_trade.py), which is below what the loans are
worth to it, so its capital falls by the discount. Where the society has no market for loans, or the savers cannot
pay for enough, the bank pays what it holds to the withdrawing depositors in proportion and fails (banks.fail): the
rest of its deposits fall due, the depositors bear what the bank cannot pay through the one default rule, and its
founder loses the capital the bank no longer holds.
"""
from typing import List, Sequence

from . import banks, secondary_trade
from .secondary_trade import BOND_MARKET, Shortfall
from .types import AgentId, FundsOffer, Loan, Transfer

EPSILON = 1e-9
WITHDRAWAL_PURPOSE = "deposit withdrawn"


def expected_loss_share(record, bank: banks.Bank, money: str) -> float:
    """The share of what the bank owes its depositors that they expect not to be paid: the loss its record puts on
    its loans, less its capital, over its deposits. Nothing while its capital covers the loss."""
    owed = banks.owed_to_depositors(record, bank.agent_id)
    if owed <= EPSILON:
        return 0.0
    expected = record.loss_rates.get(bank.agent_id, 0.0) * banks.loans_out(record, bank.agent_id)
    uncovered = max(0.0, expected - max(0.0, banks.capital_of(record, bank.agent_id, money)))
    return min(1.0, uncovered / owed)


def withdrawing(record, bank: banks.Bank, money: str) -> List[Loan]:
    """The deposits whose holders ask for them back: those whose interest does not cover the loss they expect."""
    share = expected_loss_share(record, bank, money)
    if share <= EPSILON:
        return []
    return [deposit for deposit in banks.deposits_of(record, bank.agent_id) if deposit.rate < share and deposit.principal > EPSILON]


def _pay(record, bank_id: AgentId, deposits: Sequence[Loan], part: float, money: str) -> float:
    """Pay each deposit `part` of its principal and shrink it; the money paid."""
    payments = [Transfer(bank_id, deposit.lender, money, deposit.principal * part, WITHDRAWAL_PURPOSE) for deposit in deposits]
    record.book.transfer_many(payments)
    for deposit in deposits:
        deposit.principal -= deposit.principal * part
    record.loans = [loan for loan in record.loans if loan.principal > EPSILON or loan.arrears > EPSILON or loan.borrower != bank_id]
    return sum(payment.amount for payment in payments)


def sell_for_cash(setup, record, bank: banks.Bank, need: float, offers: Sequence[FundsOffer], market_rate: float,
                  institutions: Sequence[str], money: str) -> List[FundsOffer]:
    """The bank sells loans to the savers for `need` of cash, at the price that clears; the offers less what savers spent."""
    if BOND_MARKET not in institutions or need <= EPSILON:
        return list(offers)
    # cash costs the bank what its depositors who run would need to stay: their interest and the loss they expect
    asking_rate = banks.ask_of(record, bank, money) + expected_loss_share(record, bank, money)
    remaining, _trades = secondary_trade.run(setup, record, offers, {bank.agent_id: Shortfall(need, asking_rate)},
                                             market_rate, institutions, sellers=[bank.agent_id])
    return remaining


def run(setup, record, offers: Sequence[FundsOffer], year: int, institutions: Sequence[str], market_rate: float,
        ) -> List[FundsOffer]:
    """The year's withdrawals from every standing bank. Returns the offers less what savers spent buying loans."""
    money = setup.currency_id
    offers = list(offers)
    for bank in banks.standing(record):
        leaving = withdrawing(record, bank, money)
        asked = sum(deposit.principal for deposit in leaving)
        if asked <= EPSILON:
            continue
        cash = record.book.balance(bank.agent_id, money)
        if cash < asked:
            offers = sell_for_cash(setup, record, bank, asked - cash, offers, market_rate, institutions, money)
            cash = record.book.balance(bank.agent_id, money)
        if cash >= asked - EPSILON:
            _pay(record, bank.agent_id, leaving, 1.0, money)
            continue
        _pay(record, bank.agent_id, leaving, max(0.0, cash) / asked, money)
        banks.fail(record, bank, year, money)
    return offers
