"""The columns of the loan table: every term loan the economy has out, one row each, in the order they were struck (the
order the credit market's sums follow). Names (agents, currencies, tiles, kinds) are numbers of the store's `IdTable`s."""
import numpy

from sim.compiled_tables.spec import Column, TableSpec

NO_TILE = -1       # collateral_tile of a loan that pledges no land

LOAN_TABLE = TableSpec("Loans", (
    Column("number", numpy.int64, "the loan's number: its place in the store's id texts, never reused while a game runs", "loan number"),
    Column("lender", numpy.int64, "who is owed", "agent id", ids="agents"),
    Column("borrower", numpy.int64, "who owes", "agent id", ids="agents"),
    Column("currency", numpy.int64, "the currency the loan is in", "currency id", ids="currencies"),
    Column("principal", numpy.float64, "the part of the loan not yet repaid", "currency units"),
    Column("rate", numpy.float64, "interest charged on the principal each year", "fraction per year"),
    Column("years_left", numpy.float64, "years of term left; the last year repays all the principal", "years"),
    Column("collateral_value", numpy.float64, "worth of the land pledged to this loan", "currency units"),
    Column("arrears", numpy.float64, "what the borrower has not paid of earlier years, interest included", "currency units"),
    Column("issued_year", numpy.int64, "the year the loan was struck (its first payment falls due a year later)", "year"),
    Column("arrears_interest", numpy.float64, "the part of the arrears that is unpaid interest", "currency units"),
    Column("kind", numpy.int64, "the contract kind (the term loan is the only kind the store holds in a game)", "kind id", ids="kinds"),
    Column("collateral_tile", numpy.int64, "the tile whose land title the loan pledges, or NO_TILE", "tile id", ids="tiles"),
    Column("collateral_share", numpy.float64, "the share of that tile's land pledged", "fraction of the tile"),
    Column("unit_value", numpy.float64, "what one coin of principal is worth in the lender's own unit (1 unless the lender is abroad)",
           "lender units per coin"),
))
Loans = LOAN_TABLE.make_type(__name__)

FLOAT_FIELDS = ("principal", "rate", "years_left", "collateral_value", "arrears", "arrears_interest", "collateral_share", "unit_value")
NAME_FIELDS = {"lender": "agents", "borrower": "agents", "currency": "currencies", "kind": "kinds"}
RECORD_ORDER = ("contract_id", "lender", "borrower", "currency", "principal", "rate", "years_left", "collateral_value", "arrears",
                "issued_year", "arrears_interest", "kind", "collateral_tile", "collateral_share", "unit_value")
