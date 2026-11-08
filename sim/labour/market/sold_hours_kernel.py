"""The hours a market's offers sell at a wage, over arrays (the kernel behind `labour_supply.HourSupply.hours_at` in the
economy, and the schedule the clearing kernels read every market's hours from).

Per offer, the hours sold are its hours less the share of the hours its worker keeps at home that falls to it; what the
worker keeps is the larger of its plan and its plot's hours at the wage, plus its household work, no more than its year.
The plot's hours are the cohort's workers times the parametric plot schedule written out here.

The offers sit in the columns of one matrix (one call argument is cheaper than ten); a market is a range of columns. The
matrix is written from the economy's `LabourOffers` table (`economy.labour_offers_kernels.offer_matrix`) or packed from rows
by a caller with its own schedules. The two helpers that hold the rule are shared with the economy's settlement kernel."""
from sim.jit import njit

OFFER_HOURS, OFFER_WHOLE, OFFER_SHARE, OFFER_PLAN, OFFER_WORK, OFFER_HAS_PLOT, OFFER_PER_WORKER, OFFER_MARGINAL, \
    OFFER_USABLE, OFFER_WORKERS = range(10)
OFFER_ROWS = 10


@njit
def plot_hours_at_wage(wage, has_plot, available, marginal, usable, workers, exponent):
    """The hours a cohort's plot keeps at a wage: `households_hours_offered.plot_hours_kept` times its workers; none where
    it has no plot. `available`, `usable` are per worker; `marginal` is what the next plot hour adds (money per hour)."""
    plot = 0.0
    if has_plot != 0.0:
        if available > 0.0 and usable > 0.0 and marginal > 0.0:
            allowed = available if available < usable else usable
            if wage <= 0.0:
                plot = allowed
            else:
                wanted = available * (marginal / wage) ** exponent
                plot = allowed if allowed < wanted else wanted
        plot *= workers
    return plot


@njit
def hours_kept_at_home(whole, plan, plot, work):
    """The hours of a cohort's `whole` year that go home: what its plan or its plot asks (the greater) and the household work
    beside it, no more than the year (`economy.labour_supply.hours_kept_at_home`)."""
    kept = (plan if plan > plot else plot) + work
    return whole if kept > whole else kept


@njit
def sold_hours_range(wage, offers, exponent, first, last):
    """The hours sold at a wage by the offers in columns `first` up to `last`, added left to right."""
    total = 0.0
    for index in range(first, last):
        plot = plot_hours_at_wage(wage, offers[OFFER_HAS_PLOT, index], offers[OFFER_PER_WORKER, index], offers[OFFER_MARGINAL, index],
                                  offers[OFFER_USABLE, index], offers[OFFER_WORKERS, index], exponent)
        kept = hours_kept_at_home(offers[OFFER_WHOLE, index], offers[OFFER_PLAN, index], plot, offers[OFFER_WORK, index])
        total += offers[OFFER_HOURS, index] - kept * offers[OFFER_SHARE, index]
    return total


@njit
def sold_hours(wage, offers, exponent):
    return sold_hours_range(wage, offers, exponent, 0, offers.shape[1])
