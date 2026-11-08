"""The tables that hold the labour core's state between years (docs/architecture/COMPILED_YEAR.md, "The tables and their owners").

Four of them. Three sit on the grid of every (area, trade) pair the state knows, a pair being the row `area * trade_count +
trade` (areas and trades are numbered in sorted name order, `state_ids.SortedIds`, so rows run in sorted (area, trade) order):

    WORKERS   who works in each pair, per ability band
    MARKETS   what each pair's labour market remembers: wage, ask, and where its hired-hours rows are
    AREAS     one row per area: which of the state's fields name it (an area can be named with nothing in it)

and two grow as the year adds rows:

    HIRED     hours each employer was hired for in a market last year, rows grouped by market
    TRAINEES  cohorts of people learning a trade, one row each, grouped by market, in the order they enrolled

`MarketState` (records.py) owns them; other modules read them through its dict-shaped views (state_views.py) or the kernels
of this package. A missing wage or ask is NaN: kernels read it as "none" (CLAUDE.md: no in-band zero).
"""
import numpy

from sim.compiled_tables.spec import Column, TableSpec

WORKERS = TableSpec("Workers", (
    Column("present", numpy.bool_, "the pair has an entry in the workers view (a pair can be present with nobody in it)", "flag"),
    Column("order", numpy.int64, "when the pair got its entry, counted across the state: dict views list pairs in this order", "sequence number"),
    Column("length", numpy.int64, "how many bands the pair's list has (the state's band count, unless a caller stored a shorter list)", "bands"),
    Column("people", numpy.float64, "people of the trade in the area, per ability band; bands past `length` are zero", "people", width=0),
))
Workers = WORKERS.make_type(__name__)

MARKETS = TableSpec("Markets", (
    Column("wage", numpy.float64, "the wage every hour hired was paid at the last clearing; NaN: none yet", "currency per hour"),
    Column("ask", numpy.float64, "the workers' ask over the reservation wage (asks.py); NaN: none yet, read as one", "multiple of the reservation wage"),
    Column("wage_order", numpy.int64, "when the pair got its wage (the wages view lists pairs in this order)", "sequence number"),
    Column("ask_order", numpy.int64, "when the pair got its ask (the asks view lists pairs in this order)", "sequence number"),
    Column("hired_order", numpy.int64, "when the pair got its hired-hours entry (the hired view lists pairs in this order)", "sequence number"),
    Column("cohort_order", numpy.int64, "when the pair got its first cohort (the trainees view lists pairs in this order)", "sequence number"),
    Column("hired_present", numpy.bool_, "the pair has an entry in the hired-hours view (an entry can hold no employer)", "flag"),
    Column("hired_first", numpy.int64, "first HIRED row of this market's employers", "row"),
    Column("hired_count", numpy.int64, "how many HIRED rows the market has", "rows"),
    Column("cohort_first", numpy.int64, "first TRAINEES row of the cohorts learning this pair's trade here", "row"),
    Column("cohort_count", numpy.int64, "how many TRAINEES rows (cohorts) the pair has", "rows"),
))
Markets = MARKETS.make_type(__name__)

AREAS = TableSpec("Areas", tuple(
    column for field in ("workers", "trainees", "wages", "asks", "hired") for column in (
        Column(field + "_named", numpy.bool_, "the area has an entry in the %s view (it can have nothing in it)" % field, "flag"),
        Column(field + "_order", numpy.int64, "when the area got its entry in the %s view (the view lists areas in this order)" % field,
               "sequence number"))))
Areas = AREAS.make_type(__name__)

HIRED = TableSpec("Hired", (
    Column("employer", numpy.int64, "the employer the hours were hired by", "employer id", ids="employers"),
    Column("hours", numpy.float64, "hours the employer held in the market at the last clearing", "hours per year"),
))
Hired = HIRED.make_type(__name__)

TRAINEES = TableSpec("Trainees", (
    Column("market", numpy.int64, "grid row (area * trade_count + trade) of the trade being learnt and the area learning it", "row"),
    Column("years_left", numpy.float64, "years of training still to go; the cohort finishes when it reaches zero", "years"),
    Column("bonus", numpy.float64, "teaching that adds to every band's chance of finishing", "ability standard deviations"),
    Column("length", numpy.int64, "how many bands the cohort's list has", "bands"),
    Column("people", numpy.float64, "people in training, per ability band; bands past `length` are zero", "people", width=0),
))
Trainees = TRAINEES.make_type(__name__)
