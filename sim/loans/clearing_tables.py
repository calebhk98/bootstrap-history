"""The tables of one clearing of the credit market: the requests, the lenders' offers and the loans struck.

A request is one row, in the order the clearing sorts them (borrower name, purpose, amount, maximum rate); an offer is one row in the
order the lenders were listed. Names do not enter the kernel: where a rule breaks a tie by name the table holds the rank of the name
among the names of its own table (`borrower_rank`, `lender_rank`)."""
import numpy

from sim.compiled_tables.spec import Column, TableSpec

REQUESTS = TableSpec("ClearingRequests", (
    Column("borrower_rank", numpy.int64, "place of the borrower's name among the requesters' names sorted: breaks every tie by name", "rank"),
    Column("amount", numpy.float64, "what the request asks (the kernel cuts it to what its collateral bears)", "currency units"),
    Column("maximum_rate", numpy.float64, "the most the borrower pays a year, premium included", "fraction per year"),
    Column("years", numpy.float64, "the term asked", "years"),
    Column("collateral_value", numpy.float64, "worth of the land pledged for the whole amount asked", "currency units"),
    Column("collateral_share", numpy.float64, "the share of the tile's land pledged for the whole amount asked", "fraction of the tile"),
    Column("existing_debt", numpy.float64, "what the borrower owes on loans already struck", "currency units"),
    Column("arrears_history", numpy.float64, "what the market holds against the borrower: its arrears and the losses it caused", "currency units"),
    Column("funded_amount", numpy.float64, "output: the amount the clearing works with (the amount asked, or less when cut)", "currency units"),
    Column("premium", numpy.float64, "output: the rate added for the borrower's risk on the funded amount", "fraction per year"),
    Column("ceiling", numpy.float64, "output: the highest base rate the borrower can pay (maximum rate less premium)", "fraction per year"),
    Column("default_probability", numpy.float64, "output: the borrower's chance of default on the funded amount", "probability"),
    Column("granted", numpy.float64, "output: what the borrower was lent", "currency units"),
    Column("unmet", numpy.float64, "output: what it asked and did not get, or 0 when that is within rounding", "currency units"),
))
Requests = REQUESTS.make_type(__name__)

OFFERS = TableSpec("ClearingOffers", (
    Column("lender_rank", numpy.int64, "place of the lender's name among the lenders' names sorted: breaks every tie by name", "rank"),
    Column("amount", numpy.float64, "the funds on offer", "currency units"),
    Column("minimum_rate", numpy.float64, "the lowest base rate the lender takes", "fraction per year"),
    Column("risk_capacity", numpy.float64, "the value at risk the lender may still take on (read only where has_capacity)", "currency units"),
    Column("has_capacity", numpy.bool_, "whether the lender limits the value at risk it takes on (a bank does)", "flag"),
))
Offers = OFFERS.make_type(__name__)

NEW_LOANS = TableSpec("ClearingLoans", (
    Column("request", numpy.int64, "the row of the request the loan funds", "request row"),
    Column("offer", numpy.int64, "the row of the offer the loan is lent from", "offer row"),
    Column("principal", numpy.float64, "what is lent", "currency units"),
    Column("rate", numpy.float64, "the rate: the base rate plus the borrower's premium", "fraction per year"),
    Column("collateral_value", numpy.float64, "the share of the request's collateral value this loan carries", "currency units"),
    Column("collateral_share", numpy.float64, "the share of the request's pledged land this loan carries", "fraction of the tile"),
))
NewLoans = NEW_LOANS.make_type(__name__)

# the kernel's constants, in this order (the declared numbers of the rules it runs)
CONSTANT_NAMES = ("default_probability_sensitivity", "bank_lambda", "markup_reference_rate", "arrears_premium", "rate_adjustment_share",
                  "material_lender_share", "bisection_steps")

# the causes a clearing reports (0: it cleared)
CLEARED, NO_BORROWER_AT_ASK, NO_OFFER_AT_RATE = 0, 1, 2
