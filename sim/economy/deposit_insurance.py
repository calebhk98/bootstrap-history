"""Deposit insurance: an actor (a state, or anyone with a purse) promises depositors their deposits, funded by premiums.

The insurer's reserve is its balance in the book. Each bank pays a premium equal to the payout the insurer expects
to make on it: the share of its deposits that its loss record puts beyond its capital (bank_runs.expected_loss_share),
times the deposits. A bank whose capital covers its expected losses pays nothing. When a bank fails (banks.fail) the
insurer pays each depositor what the bank cannot, from its reserve; where the reserve is short it pays every
depositor the same share. What it pays it takes over as a claim on the bank, so the bank's remaining assets repay
the insurer through the one default rule. Depositors trust the promise to the extent the reserve covers the payout
expected (`cover`), so a reserve that falls behind the risk brings the runs back.
"""
from typing import Optional

from .types import AgentId, Transfer

EPSILON = 1e-9
PREMIUM_PURPOSE = "deposit insurance premium"
PAYOUT_PURPOSE = "deposit insurance payout"


def insurer_of(record) -> Optional[AgentId]:
    return record.capital_markets.deposit_insurer


def premium(expected_loss_share: float, deposits_owed: float) -> float:
    """The premium that equals the expected payout: the share of the deposits expected lost, times the deposits."""
    return max(0.0, expected_loss_share) * max(0.0, deposits_owed)


def cover(reserve: float, expected_payout: float) -> float:
    """The share of the promise depositors believe: the reserve over the payout expected, at most one. Full when no
    payout is expected."""
    if expected_payout <= EPSILON:
        return 1.0
    return min(1.0, max(0.0, reserve) / expected_payout)


def collect(record, bank_id: AgentId, due: float, money: str) -> float:
    """The bank pays the insurer its premium out of its cash, as far as the cash goes; the amount paid."""
    insurer = insurer_of(record)
    paid = min(max(0.0, due), max(0.0, record.book.balance(bank_id, money)))
    if insurer is None or paid <= EPSILON:
        return 0.0
    record.book.transfer(Transfer(bank_id, insurer, money, paid, PREMIUM_PURPOSE))
    return paid


def settle(record, bank_id: AgentId, money: str) -> float:
    """The bank has failed: the insurer pays each depositor its claim (principal and arrears), all of it while the
    reserve lasts, the same share of each otherwise, and takes over the part it paid as the lender of that deposit.
    The money paid."""
    insurer = insurer_of(record)
    if insurer is None:
        return 0.0
    deposits = [deposit for deposit in record.credit.loans.select(borrower=bank_id)
                if deposit.principal + deposit.arrears > EPSILON and deposit.lender not in (insurer, record.capital_markets.last_resort)]
    claims = [(deposit, deposit.principal + deposit.arrears) for deposit in deposits]
    owed = sum(claim for _deposit, claim in claims)
    if owed <= EPSILON:
        return 0.0
    share = min(1.0, max(0.0, record.book.balance(insurer, money)) / owed)
    if share <= EPSILON:
        return 0.0
    payments = [Transfer(insurer, deposit.lender, money, claim * share, PAYOUT_PURPOSE) for deposit, claim in claims]
    record.book.transfer_many(payments)
    for deposit, _claim in claims:
        record.credit.transfer_loan(deposit, insurer, share)
    return sum(payment.amount for payment in payments)
