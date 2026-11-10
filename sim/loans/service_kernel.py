"""One year's service of the loans: each borrower pays its due loans, one after another, until its cash runs out.

`service_loans` is the loop of `credit.service_split` over table rows. It reads the loan table and a cash figure per borrower and
writes only its own output arrays (`ServiceOutcome`), so a caller can use the answer (payments, receipts, defaults) before the table
is changed. Row `i` of the outcome is the `i`-th loan served, in the order the rows are given."""
from collections import namedtuple

import numpy

from sim.jit import njit

KEPT, DEFAULTED, REPAID = 0, 1, 2     # what became of a loan served: still owed, written off, or paid off

ServiceOutput = namedtuple("ServiceOutput", (
    "paid",                # currency units: what the borrower paid this loan (0 when it could pay nothing)
    "status",              # KEPT, DEFAULTED or REPAID
    "principal",           # currency units: the principal after the year's installment
    "arrears",             # currency units: what is still unpaid after the year's payment
    "arrears_interest",    # currency units: the part of those arrears that is unpaid interest
    "years_left",          # years: the term left after this year
    "loss",                # currency units: principal and arrears the lender will not collect (DEFAULTED only)
    "receipt_interest",    # per lender agent number: interest received (income)
    "receipt_principal",   # per lender agent number: principal installments received
    "receipt_arrears",     # per lender agent number: overdue principal received
    "lender_order"))       # per lender agent number: place among the lenders served (-1: none of its loans was served)


def new_output(served: int, agent_count: int) -> ServiceOutput:
    return ServiceOutput(numpy.zeros(served), numpy.zeros(served, dtype=numpy.int64), numpy.zeros(served), numpy.zeros(served),
                          numpy.zeros(served), numpy.zeros(served), numpy.zeros(served), numpy.zeros(agent_count),
                          numpy.zeros(agent_count), numpy.zeros(agent_count), numpy.full(agent_count, -1, dtype=numpy.int64))


@njit
def installment_of(principal, years_left):
    """The principal a loan returns at the year's end: an even share over the years left, all of it in the last year."""
    return principal if years_left <= 1.0 else principal / years_left


@njit
def serve_one(loans, row, cash, arrears_share, output, place):
    """Serve the loan in `row` from its borrower's `cash` (a figure per agent number, drawn down); write output row `place`."""
    principal, rate, arrears = loans.principal[row], loans.rate[row], loans.arrears[row]
    installment = installment_of(principal, loans.years_left[row])
    interest = principal * rate
    arrears_interest = min(arrears, loans.arrears_interest[row])
    arrears_principal = arrears - arrears_interest
    due = arrears + interest + installment
    borrower = loans.borrower[row]
    paid = min(max(0.0, cash[borrower]), due)
    if paid > 0:
        cash[borrower] = cash[borrower] - paid
    output.paid[place] = paid
    left = paid
    take_arrears_interest = min(left, arrears_interest)
    left -= take_arrears_interest
    take_arrears_principal = min(left, arrears_principal)
    left -= take_arrears_principal
    take_interest = min(left, interest)
    left -= take_interest
    take_installment = min(left, installment)
    lender = loans.lender[row]
    if output.lender_order[lender] < 0:
        output.lender_order[lender] = place
    output.receipt_interest[lender] += take_arrears_interest + take_interest
    output.receipt_arrears[lender] += take_arrears_principal
    output.receipt_principal[lender] += take_installment
    owed = due - paid
    remaining = principal - installment
    if owed > arrears_share * principal + 1e-12:
        output.status[place] = DEFAULTED
        output.loss[place] = remaining + owed
    elif remaining <= 1e-12 and owed <= 1e-12:
        output.status[place] = REPAID
    else:
        output.status[place] = KEPT
        output.principal[place] = remaining
        output.arrears[place] = owed
        output.arrears_interest[place] = (arrears_interest - take_arrears_interest) + (interest - take_interest)
        output.years_left[place] = max(0.0, loans.years_left[row] - 1.0)


@njit
def service_loans(loans, rows, cash, arrears_share, output):
    """Serve the loans in `rows` in that order (the caller sorts them by id), each from its borrower's `cash`, filling `output`."""
    for place in range(len(rows)):
        serve_one(loans, rows[place], cash, arrears_share, output, place)
