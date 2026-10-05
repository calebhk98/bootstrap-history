"""A producer that leaves for good: its cash repays its lenders first, the rest and its goods go to its owner,
and what the cash could not repay becomes the lenders' loss."""
import math
from typing import Dict, List, Tuple

from . import credit_claims, ownership
from .credit import Default
from .types import GoodsMove, Transfer


def exit_producer(record, producer_id: str, payout: List[Transfer]) -> List[Transfer]:
    """Repay the loans from the cash, in loan order; pay out what is left of the close's dividend (shared
    as ownership shares dividends); move the goods held to the owner; write off the unpaid debt as
    defaults and remove the producer. Returns the dividend payments made."""
    producer = record.producers[producer_id]
    owed = [loan for loan in record.loans if loan.borrower == producer_id]
    repayments, unpaid = _repay(record, producer_id, owed)
    record.book.transfer_many(repayments)
    repaid = math.fsum(transfer.amount for transfer in repayments)
    payout = _less(payout, repaid)
    paid = ownership.spread(record, payout)
    record.book.transfer_many(paid)
    moves = [GoodsMove(producer_id, producer.owner, good, tile, quantity, "an exited producer's stock")
             for good, tiles in sorted(record.book.holdings(producer_id)["goods"].items())
             for tile, quantity in sorted(tiles.items()) if quantity > 0.0]
    if moves:
        record.book.move_many(moves)
    defaults = [Default(loan.loan_id, loan.lender, loan.borrower, loan.currency, unpaid[loan.loan_id])
                for loan in owed if unpaid[loan.loan_id] > 0.0]
    for lender, lost in credit_claims.losses_by_lender(defaults).items():
        record.credit_losses[lender] = record.credit_losses.get(lender, 0.0) + lost
    record.remembered_defaults = credit_claims.remember_defaults(record.remembered_defaults, defaults)
    record.loans = [loan for loan in record.loans if loan.borrower != producer_id]
    record.worn_runs.pop(producer_id, None)
    record.expansion_runs.pop(producer_id, None)
    del record.producers[producer_id]
    return paid


def _repay(record, producer_id, owed) -> Tuple[List[Transfer], Dict[str, float]]:
    """Lenders are paid before the owner: each loan's principal and arrears from the cash, in loan order."""
    repayments: List[Transfer] = []
    unpaid: Dict[str, float] = {}
    for loan in owed:
        cash = record.book.balance(producer_id, loan.currency) - math.fsum(
            transfer.amount for transfer in repayments if transfer.currency == loan.currency)
        due = loan.principal + loan.arrears
        paid = min(due, max(0.0, cash))
        if paid > 0.0:
            repayments.append(Transfer(producer_id, loan.lender, loan.currency, paid, "repaid on exit"))
        unpaid[loan.loan_id] = due - paid
    return repayments, unpaid


def _less(payout: List[Transfer], repaid: float) -> List[Transfer]:
    """The dividend left once `repaid` has gone to lenders, taken from the payments in order."""
    left = []
    for transfer in payout:
        amount = transfer.amount - min(transfer.amount, repaid)
        repaid -= transfer.amount - amount
        if amount > 0.0:
            left.append(Transfer(transfer.payer, transfer.payee, transfer.currency, amount, transfer.purpose))
    return left
