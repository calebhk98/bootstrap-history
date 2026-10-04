"""A producer that leaves for good: what it held goes to its owner and its debts become the lenders' loss."""
from typing import List

from . import credit_claims, ownership
from .credit import Default
from .types import GoodsMove, Transfer


def exit_producer(record, producer_id: str, payout: List[Transfer]) -> List[Transfer]:
    """Pay out the cash (the close's dividend, shared as ownership shares dividends), move the goods held
    to the owner, write off the loans as defaults and remove the producer. Returns the payments made."""
    producer = record.producers[producer_id]
    paid = ownership.spread(record, payout)
    record.book.transfer_many(paid)
    moves = [GoodsMove(producer_id, producer.owner, good, tile, quantity, "an exited producer's stock")
             for good, tiles in sorted(record.book.holdings(producer_id)["goods"].items())
             for tile, quantity in sorted(tiles.items()) if quantity > 0.0]
    if moves:
        record.book.move_many(moves)
    owed = [loan for loan in record.loans if loan.borrower == producer_id]
    defaults = [Default(loan.loan_id, loan.lender, loan.borrower, loan.currency, loan.principal + loan.arrears)
                for loan in owed]
    for lender, lost in credit_claims.losses_by_lender(defaults).items():
        record.credit_losses[lender] = record.credit_losses.get(lender, 0.0) + lost
    record.remembered_defaults = credit_claims.remember_defaults(record.remembered_defaults, defaults)
    record.loans = [loan for loan in record.loans if loan.borrower != producer_id]
    record.worn_runs.pop(producer_id, None)
    record.expansion_runs.pop(producer_id, None)
    del record.producers[producer_id]
    return paid
