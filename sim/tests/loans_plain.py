"""The loan rules as they were written over lists of `Contract` objects, kept as the reference the table kernels are tested against
(`test_loans_*`). Each function here is the Python the named kernel replaced; do not use them in the game."""
from typing import Dict, List, Mapping, Tuple

from sim.contract_record import Contract
from sim.economy.credit import DEFAULT_ARREARS_SHARE, Default, Receipt
from sim.economy.replaced import replaced
from sim.economy.types import Transfer


def installment_of(loan: Contract) -> float:
    return loan.principal if loan.years_left <= 1.0 else loan.principal / loan.years_left


def service_split(loans, cash_by_borrower: Mapping[str, float], year: int,
                  ) -> Tuple[List[Transfer], List[Contract], List[Default], Dict[str, Receipt]]:
    """`credit.service_split` before it ran over the loan table."""
    cash = dict(cash_by_borrower)
    transfers: List[Transfer] = []
    updated: List[Contract] = []
    defaults: List[Default] = []
    receipts: Dict[str, Receipt] = {}
    for loan in sorted(loans, key=lambda l: l.loan_id):
        installment = installment_of(loan)
        interest = loan.principal * loan.rate
        arrears_interest = min(loan.arrears, loan.arrears_interest)
        arrears_principal = loan.arrears - arrears_interest
        due = loan.arrears + interest + installment
        paid = min(max(0.0, cash.get(loan.borrower, 0.0)), due)
        if paid > 0:
            cash[loan.borrower] = cash.get(loan.borrower, 0.0) - paid
            transfers.append(Transfer(loan.borrower, loan.lender, loan.currency, paid,
                                      "loan_service:%s:%d" % (loan.loan_id, year)))
        left = paid
        paid_parts = []
        for part in (arrears_interest, arrears_principal, interest, installment):
            take = min(left, part)
            paid_parts.append(take)
            left -= take
        receipt = receipts.setdefault(loan.lender, Receipt())
        receipt.interest += paid_parts[0] + paid_parts[2]
        receipt.arrears += paid_parts[1]
        receipt.principal += paid_parts[3]
        arrears = due - paid
        principal = loan.principal - installment
        if arrears > DEFAULT_ARREARS_SHARE * loan.principal + 1e-12:
            defaults.append(Default(loan.loan_id, loan.lender, loan.borrower, loan.currency, loss=principal + arrears))
            continue
        if principal <= 1e-12 and arrears <= 1e-12:
            continue
        updated.append(replaced(loan, principal=principal, arrears=arrears,
                                arrears_interest=(arrears_interest - paid_parts[0]) + (interest - paid_parts[2]),
                                years_left=max(0.0, loan.years_left - 1.0)))
    return transfers, updated, defaults, receipts


def written_down(loan: Contract, ratio: float):
    """`firm_finance.written_down`: (the loan after a write-off of `ratio`, the loss to its lender)."""
    keep = 1.0 - ratio
    lost = ratio * (loan.principal + loan.arrears)
    return replaced(loan, principal=keep * loan.principal, arrears=keep * loan.arrears, arrears_interest=keep * loan.arrears_interest), lost


def producer_loans(loans, producer_row: Mapping[str, int], count: int):
    """The close's loan loop (`close_pack._loans`): (interest, commitments, arrears, debt) per producer row."""
    import numpy
    interest, commitments, arrears, debt = (numpy.zeros(count) for _name in range(4))
    for loan in loans:
        row = producer_row.get(loan.borrower)
        if row is None:
            continue
        interest[row] += loan.principal * loan.rate
        commitments[row] += loan.principal * loan.rate + installment_of(loan)
        arrears[row] += loan.arrears
        debt[row] += loan.principal + loan.arrears
    return interest, commitments, arrears, debt
