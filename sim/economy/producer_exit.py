"""A producer that leaves for good: its cash repays its lenders first, the rest and its goods go to its owner,
and what the cash could not repay becomes the lenders' loss."""
import math
from typing import Dict, List, Optional, Tuple


from . import producer_table
from . import bondage_hours, credit_claims, ownership
from sim.book import ROUNDING_SHARE
from .credit import Default
from .types import GoodsMove, Transfer


class ExitBatch:
    """Several exits in one pass over the loans: the exiting producers' loans are indexed once and their term loans leave the contracts
    together at `finish()`. Each exit reads only its own loans, so none sees the others' pending removal."""

    def __init__(self, record) -> None:
        self.record = record
        self.exited: List[str] = []
        self._owed = None

    def exit(self, producer_id: str, payout: List[Transfer]) -> List[Transfer]:
        if self._owed is None:
            self._owed = {}
            for loan in self.record.credit.loans:
                self._owed.setdefault(loan.borrower, []).append(loan)
        self.exited.append(producer_id)
        return exit_producer(self.record, producer_id, payout, self._owed.get(producer_id, []), deferred=True)

    def finish(self) -> None:
        if self.exited:
            self.record.credit.default_term_loans_of(self.exited)
            self.exited = []


def exit_producer(record, producer_id: str, payout: List[Transfer], owed: Optional[List] = None, deferred: bool = False) -> List[Transfer]:
    """Repay the loans from the cash, in loan order; pay out what is left of the close's dividend (shared
    as ownership shares dividends); move the goods held to the owner; write off the unpaid debt as
    defaults and remove the producer. Returns the dividend payments made. `owed` is the producer's loans when the caller has them;
    `deferred` leaves its term loans in the contracts for the caller to end (`ExitBatch`)."""
    producer = record.producers[producer_id]
    if owed is None:
        owed = [loan for loan in record.credit.loans if loan.borrower == producer_id]
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
        record.credit.add_loss(lender, lost)
    record.credit.remember(defaults)
    if not deferred:
        record.credit.default_term_loans(producer_id)
    record.credit.forget_producer(producer_id)
    record.capital_markets.forget_producer(producer_id)
    bondage_hours.release(record.unfree.bonded_held, producer_id)
    producer_table.remove_producer(record.producers, producer_id)
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
    """The dividend left once `repaid` has gone to lenders, taken from the payments in order; a remainder
    that is only rounding residue is dropped."""
    left = []
    for transfer in payout:
        amount = transfer.amount - min(transfer.amount, repaid)
        repaid -= transfer.amount - amount
        if amount > ROUNDING_SHARE * transfer.amount:
            left.append(Transfer(transfer.payer, transfer.payee, transfer.currency, amount, transfer.purpose))
    return left
