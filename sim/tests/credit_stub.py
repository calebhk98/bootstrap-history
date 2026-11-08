"""A real credit record for the tests that stand a record up by hand: the loans go into the loan table as they would in a game."""
from sim.economy.credit_record import CreditRecord


def credit_of(loans=(), **fields) -> CreditRecord:
    """A `CreditRecord` holding copies of `loans` (Contracts), with the other record fields given as keywords."""
    credit = CreditRecord(**fields)
    credit.add_loans(list(loans))
    return credit
