"""The example table every converter copies: loans, their columns documented, and the small kernels that use them.

A loan is a sum a borrower owes a lender and pays interest on. The table is the whole state: nothing about loans lives in a
Python object while a kernel runs. Borrower and lender are numbers in the `agents` IdTable."""
import numpy

from sim.compiled_tables.causes import Causes
from sim.compiled_tables.growth import NO_ROOM, claim_row
from sim.compiled_tables.spec import Column, TableSpec
from sim.compiled_tables.sums import ordered_total
from sim.jit import njit

LOANS = TableSpec("Loans", (
    Column("borrower", numpy.int64, "the agent that owes the loan", "agent id", ids="agents"),
    Column("lender", numpy.int64, "the agent that is owed", "agent id", ids="agents"),
    Column("principal", numpy.float64, "what is still owed, interest included", "currency units"),
    Column("rate", numpy.float64, "interest added to the principal each year", "fraction per year"),
))
Loans = LOANS.make_type(__name__)

CAUSES = Causes(("table_full", "negative_principal"))
TABLE_FULL = CAUSES.code("table_full")
NEGATIVE_PRINCIPAL = CAUSES.code("negative_principal")


@njit
def lend(loans, borrower, lender, principal, rate):
    """Add a loan. Returns its row, or minus the problem code (TABLE_FULL, NEGATIVE_PRINCIPAL) when it is refused."""
    if principal < 0.0:
        return -NEGATIVE_PRINCIPAL
    row = claim_row(loans)
    if row == NO_ROOM:
        return -TABLE_FULL
    loans.borrower[row] = borrower
    loans.lender[row] = lender
    loans.principal[row] = principal
    loans.rate[row] = rate
    return row


@njit
def interest_due(loans, row):
    """The interest the loan adds this year."""
    return loans.principal[row] * loans.rate[row]


@njit
def accrue_interest(loans):
    """Add each loan's year of interest to its principal; returns the total interest added, summed in row order."""
    added = numpy.zeros(loans.row_count[0])
    for row in range(loans.row_count[0]):
        added[row] = interest_due(loans, row)
        loans.principal[row] += added[row]
    return ordered_total(added, loans.row_count[0])


@njit
def owed_by_agent(loans, agent_count):
    """Per agent number: the sum of the principal it owes, each added in row order."""
    owed = numpy.zeros(agent_count)
    for row in range(loans.row_count[0]):
        owed[loans.borrower[row]] += loans.principal[row]
    return owed
