"""The trainee cohorts a kernel reads and adds to while a phase runs: the state's table (grouped by market) and a pending table.

The state's TRAINEES rows are grouped by market, so a cohort cannot be inserted without moving the rows after it. A phase that
enrols people (switching) instead appends its new cohorts to the PENDING table, linked market by market, and reads a market's
cohorts as the state's rows followed by its pending ones, the order they will have once `MarketState.merge_cohorts` puts them
in the state's table at the end of the phase. Rows are claimed with `sim.compiled_tables.growth.claim_row`; the phase reserves
room for the most it can add, and a kernel that finds none returns `NO_ROOM` as its answer.
"""
from typing import NamedTuple

import numpy

from sim.compiled_tables.growth import NO_ROOM, claim_row
from sim.compiled_tables.spec import Column, TableSpec
from sim.jit import njit

from .exact_sums import exact_sum, float_sumprod

PENDING = TableSpec("Pending", (
    Column("market", numpy.int64, "grid row (area * trade_count + trade) of the cohort's trade and area", "row"),
    Column("years_left", numpy.float64, "years of training still to go", "years"),
    Column("bonus", numpy.float64, "teaching that adds to every band's chance of finishing", "ability standard deviations"),
    Column("people", numpy.float64, "people in training, per ability band", "people", width=0),
    Column("next", numpy.int64, "the pending row of the same market that follows this one; -1 for the last", "row"),
))
Pending = PENDING.make_type(__name__)


class CohortBook(NamedTuple):
    """A market's cohorts: its rows of the state's table (`first`, `count`, per grid row) and its pending ones (a chain from
    `pending_first` to `pending_last`, `pending_count` long)."""
    first: numpy.ndarray
    count: numpy.ndarray
    years_left: numpy.ndarray
    bonus: numpy.ndarray
    people: numpy.ndarray
    pending: Pending
    pending_first: numpy.ndarray
    pending_last: numpy.ndarray
    pending_count: numpy.ndarray


def new_book(state, room: int) -> CohortBook:
    """The state's cohorts with an empty pending table that has room for `room` new cohorts."""
    rows = len(state.market_table.cohort_count)
    table = state.trainee_table
    return CohortBook(state.market_table.cohort_first, state.market_table.cohort_count, table.years_left, table.bonus, table.people,
                      PENDING.new_table(Pending, room, widths={"people": state.bands}), numpy.full(rows, -1, numpy.int64),
                      numpy.full(rows, -1, numpy.int64), numpy.zeros(rows, numpy.int64))


@njit
def cohorts_in(book, market):
    """How many cohorts the market has, in the state's table and pending."""
    return book.count[market] + book.pending_count[market]


@njit
def add_cohort(book, market, years_left, bonus, bands):
    """Append a cohort to the market. Returns its pending row, or NO_ROOM when the pending table is full (nothing changed)."""
    row = claim_row(book.pending)
    if row == NO_ROOM:
        return NO_ROOM
    book.pending.market[row] = market
    book.pending.years_left[row] = years_left
    book.pending.bonus[row] = bonus
    book.pending.next[row] = -1
    for band in range(bands.shape[0]):
        book.pending.people[row, band] = bands[band]
    if book.pending_last[market] >= 0:
        book.pending.next[book.pending_last[market]] = row
    else:
        book.pending_first[market] = row
    book.pending_last[market] = row
    book.pending_count[market] += 1
    return row


@njit
def last_cohort(book, market):
    """The market's newest cohort as (exists, years left, bonus)."""
    if book.pending_last[market] >= 0:
        row = book.pending_last[market]
        return True, book.pending.years_left[row], book.pending.bonus[row]
    if book.count[market] > 0:
        row = book.first[market] + book.count[market] - 1
        return True, book.years_left[row], book.bonus[row]
    return False, 0.0, 0.0


@njit
def add_to_last_cohort(book, market, bands):
    """Add people (per band) to the market's newest cohort."""
    if book.pending_last[market] >= 0:
        row = book.pending_last[market]
        for band in range(bands.shape[0]):
            book.pending.people[row, band] += bands[band]
    else:
        row = book.first[market] + book.count[market] - 1
        for band in range(bands.shape[0]):
            book.people[row, band] += bands[band]


@njit
def enrolled(book, market):
    """`training.enrolled`: the people in the market's cohorts, `math.fsum` of each cohort's `math.fsum`."""
    total_cohorts = cohorts_in(book, market)
    sums = numpy.zeros(total_cohorts)
    slot = 0
    for row in range(book.first[market], book.first[market] + book.count[market]):
        sums[slot] = exact_sum(book.people[row], book.people.shape[1])
        slot += 1
    row = book.pending_first[market]
    while row >= 0:
        sums[slot] = exact_sum(book.pending.people[row], book.people.shape[1])
        slot += 1
        row = book.pending.next[row]
    return exact_sum(sums, total_cohorts)


@njit
def graduates_coming(book, market, chances):
    """`expectations.graduates_coming`: the people in the market's cohorts expected to finish, `math.fsum` of each cohort's
    `math.sumprod` of its bands and the chances."""
    total_cohorts = cohorts_in(book, market)
    if total_cohorts == 0:
        return 0.0
    products = numpy.zeros(total_cohorts)
    slot = 0
    for row in range(book.first[market], book.first[market] + book.count[market]):
        products[slot] = float_sumprod(book.people[row], chances, chances.shape[0])
        slot += 1
    row = book.pending_first[market]
    while row >= 0:
        products[slot] = float_sumprod(book.pending.people[row], chances, chances.shape[0])
        slot += 1
        row = book.pending.next[row]
    return exact_sum(products, total_cohorts)
