"""A producer that leaves for good: its cash repays its lenders first, the rest and its goods go to its owner,
and what the cash could not repay becomes the lenders' loss."""
import math
from typing import Dict, List, Optional, Tuple


from . import producer_table
from . import bondage_hours, credit_claims, ownership
from sim.book import ROUNDING_SHARE
from .credit import Default
from .posting_sequence import post_in_order
from .types import GoodsMove, Transfer


class ExitBatch:
    """Several exits in one pass over the loans: the loan table's rows are grouped by borrower once and the exiting producers' term loans
    leave the table together at `finish()`. Each exit reads only its own loans (copies of them, `Contract`s), so none sees the others'
    pending removal."""

    def __init__(self, record) -> None:
        self.record = record
        self.exited: List[str] = []
        self._owed = None
        self._held: Dict[str, dict] = {}   # the goods the exits about to come hold, read together by `hold`
        self._steps: List[tuple] = []      # the postings of the exits so far, one batch each, made together at `finish()`

    def hold(self, producer_ids: List[str]) -> None:
        """Read the goods of the producers that will exit in one block (nothing is posted before `finish`, so the read stays true)."""
        self._held = dict(zip(producer_ids, self.record.book.goods_held_many(producer_ids)))

    def exit(self, producer_id: str, payout: List[Transfer]) -> List[Transfer]:
        store = self.record.credit.contracts.loan_store
        if self._owed is None:
            self._owed = store.group_rows()
        self.exited.append(producer_id)
        return exit_producer(self.record, producer_id, payout, store.snapshots(self._owed.get(producer_id, ())), deferred=True,
                             steps=self._steps, held=self._held[producer_id] if producer_id in self._held else None)

    def finish(self) -> None:
        post_in_order(self.record.book, self._steps)
        self._steps = []
        if self.exited:
            self.record.credit.default_term_loans_of(self.exited)
            bondage_hours.release_many(self.record.unfree.bonded_held, self.exited)       # one pass over the held rows for every exit
            self.exited = []


def exit_producer(record, producer_id: str, payout: List[Transfer], owed: Optional[List] = None, deferred: bool = False,
                  steps: Optional[List[tuple]] = None, held: Optional[dict] = None) -> List[Transfer]:
    """Repay the loans from the cash, in loan order; pay out what is left of the close's dividend (shared
    as ownership shares dividends); move the goods held to the owner; write off the unpaid debt as
    defaults and remove the producer. Returns the dividend payments made. `owed` is the producer's loans when the caller has them;
    `deferred` leaves its term loans in the contracts and the bonded people it holds in `bonded_held` for the caller to end (`ExitBatch`); `steps`, when given, takes the postings
    (repayments, dividend, goods) as three batches instead of posting them: only this producer's own cash and goods are read, so
    the postings of several exits can wait and be made together in order. `held` is the producer's goods (`Book.goods_held`) when the
    caller read them for several exits at once."""
    owner = record.producers.owner_at(record.producers.row_of[producer_id])
    if owed is None:
        store = record.credit.contracts.loan_store
        owed = store.snapshots(store.rows_of(borrower=producer_id))
    repayments, unpaid = _repay(record, producer_id, owed)
    repaid = math.fsum(transfer.amount for transfer in repayments)
    payout = _less(payout, repaid)
    paid = ownership.spread(record, payout)
    held = record.book.goods_held(producer_id) if held is None else held
    moves = [GoodsMove(producer_id, owner, good, tile, quantity, "an exited producer's stock")
             for good, tiles in held.items() for tile, quantity in tiles.items() if quantity > 0.0]
    if steps is not None:
        steps.extend([(repayments, ()), (paid, ()), ((), moves)])
    else:
        record.book.transfer_many(repayments)
        record.book.transfer_many(paid)
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
    if not deferred:
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
