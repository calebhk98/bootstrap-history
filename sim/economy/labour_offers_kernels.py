"""Kernels over the `LabourOffers` table (labour_offers_table.py): what the closures of `HourSupply` computed, from columns.

- `whole_hours_by_cohort`: each cohort's hours over its offers.
- `offer_matrix`: the offers with hours, grouped by market, as the matrix the labour core's clearing kernels read
  (`sim/labour/market/sold_hours_kernel.py`); the hours a market sells at a wage are `sold_hours_range` over its columns.
- `settle_offers`: for each offer, the hours sold and kept at the wage its market settled at.

The plot and home-share rule is the core's (`plot_hours_at_wage`, `hours_kept_at_home`). Sums are added in row order."""
import numpy

from sim.jit import njit
from sim.labour.api import (OFFER_HAS_PLOT, OFFER_HOURS, OFFER_MARGINAL, OFFER_PER_WORKER, OFFER_PLAN, OFFER_ROWS, OFFER_SHARE,
                            OFFER_USABLE, OFFER_WHOLE, OFFER_WORK, OFFER_WORKERS, hours_kept_at_home, plot_hours_at_wage)


@njit
def whole_hours_by_cohort(offers, cohort_count):
    """Per cohort number: the sum of the hours of its offers, added in row order (zero hours and all)."""
    whole = numpy.zeros(cohort_count)
    for row in range(offers.row_count[0]):
        whole[offers.cohort[row]] += offers.hours[row]
    return whole


@njit
def live_offer_counts(offers, market_count):
    """Per market number: how many of its offers hold hours (more than zero)."""
    counts = numpy.zeros(market_count, dtype=numpy.int64)
    for row in range(offers.row_count[0]):
        if offers.hours[row] > 0.0:
            counts[offers.market[row]] += 1
    return counts


@njit
def _write_column(matrix, column, offers, row):
    """Offer `row` as column `column` of the matrix. A cohort with no hours in all sells nothing (its column holds no hours)."""
    whole = offers.whole_hours[row]
    live = whole > 0.0
    matrix[OFFER_HOURS, column] = offers.hours[row] if live else 0.0
    matrix[OFFER_WHOLE, column] = whole
    matrix[OFFER_SHARE, column] = offers.hours[row] / whole if live else 0.0
    matrix[OFFER_PLAN, column] = offers.plan_hours[row]
    matrix[OFFER_WORK, column] = offers.work_hours[row]
    if offers.has_plot[row]:
        matrix[OFFER_HAS_PLOT, column] = 1.0
        matrix[OFFER_PER_WORKER, column] = offers.plot_hours_per_worker[row]
        matrix[OFFER_MARGINAL, column] = offers.marginal_return[row]
        matrix[OFFER_USABLE, column] = offers.usable_per_worker[row]
        matrix[OFFER_WORKERS, column] = offers.workers[row]


@njit
def offer_matrix(offers, market_count):
    """(matrix, first, last): the offers that hold hours as columns, market after market in market number order and in row
    order within a market; market m's columns are `first[m]` up to `last[m]`. Rows of the matrix are the core's OFFER_ fields."""
    counts = live_offer_counts(offers, market_count)
    first = numpy.zeros(market_count, dtype=numpy.int64)
    last = numpy.zeros(market_count, dtype=numpy.int64)
    taken = 0
    for market in range(market_count):
        first[market] = taken
        taken += counts[market]
        last[market] = taken
    matrix = numpy.zeros((OFFER_ROWS, taken))
    next_column = first.copy()
    for row in range(offers.row_count[0]):
        if offers.hours[row] > 0.0:
            market = offers.market[row]
            _write_column(matrix, next_column[market], offers, row)
            next_column[market] += 1
    return matrix, first, last


@njit
def hours_kept_by_offer(offers, row, wage, exponent):
    """Hours of offer `row` kept at home at this wage: the cohort's home hours (`hours_kept_at_home`) times the offer's share of
    the cohort's hours, taken as kept * hours / whole (the order `HourSupply.split` has). Zero where the offer or the cohort has no hours."""
    whole = offers.whole_hours[row]
    if whole <= 0.0 or offers.hours[row] <= 0.0:
        return 0.0
    plot = plot_hours_at_wage(wage, 1.0 if offers.has_plot[row] else 0.0, offers.plot_hours_per_worker[row], offers.marginal_return[row],
                              offers.usable_per_worker[row], offers.workers[row], exponent)
    return hours_kept_at_home(whole, offers.plan_hours[row], plot, offers.work_hours[row]) * offers.hours[row] / whole


@njit
def settle_offers(offers, market_wage, market_wage_known, exponent, cohort_count):
    """Fill `sold_hours` and `kept_hours` of every offer at the wage of its market (`market_wage[m]` where `market_wage_known[m]`,
    else the offer's reservation wage). Returns per cohort number the kept hours over its offers, added in row order."""
    kept_by_cohort = numpy.zeros(cohort_count)
    for row in range(offers.row_count[0]):
        market = offers.market[row]
        wage = market_wage[market] if market_wage_known[market] else offers.reservation_wage[row]
        sold = 0.0
        if offers.whole_hours[row] > 0.0 and offers.hours[row] > 0.0:
            sold = offers.hours[row] - hours_kept_by_offer(offers, row, wage, exponent)
        offers.sold_hours[row] = sold
        offers.kept_hours[row] = offers.hours[row] - sold
        kept_by_cohort[offers.cohort[row]] += offers.kept_hours[row]
    return kept_by_cohort
