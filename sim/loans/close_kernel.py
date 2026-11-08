"""The close's loan loop: what each producer owes on its loans, added loan by loan in table order."""
from sim.jit import njit

from .service_kernel import installment_of


@njit
def producer_loans(loans, count, producer_row, interest, commitments, arrears, debt):
    """For each loan whose borrower is a producer (`producer_row[agent number]`, -1 for any other agent) add to that producer's row of
    `interest` the year's interest, to `commitments` interest plus the installment, to `arrears` its arrears, to `debt` principal plus
    arrears; the loans in table order, plain additions."""
    for row in range(count):
        producer = producer_row[loans.borrower[row]]
        if producer < 0:
            continue
        year_interest = loans.principal[row] * loans.rate[row]
        interest[producer] += year_interest
        commitments[producer] += year_interest + installment_of(loans.principal[row], loans.years_left[row])
        arrears[producer] += loans.arrears[row]
        debt[producer] += loans.principal[row] + loans.arrears[row]
