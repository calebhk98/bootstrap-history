"""The hours a market's offers sell at a wage, over arrays (the kernel behind `labour_supply.HourSupply.hours_at`).

Per offer, the hours sold are its hours less the share of the hours its worker keeps at home that falls to it; what the
worker keeps is the larger of its plan and its plot's hours at the wage, plus its household work, no more than its year
(`labour_supply.hours_kept_at_home`). The plot's hours are `households_hours_offered.plot_hours_kept` times the cohort's
workers, written out here for the parametric plot schedules `household_hours_year.plot_schedule` builds.

The offers sit in the columns of one matrix (one call argument is cheaper than ten)."""
import numpy as np

from sim.jit import njit

HOURS, WHOLE, SHARE, PLAN, WORK, HAS_PLOT, PER_WORKER, MARGINAL, USABLE, WORKERS = range(10)


@njit
def sold_hours(wage, offers, exponent):
    total = 0.0
    for index in range(offers.shape[1]):
        plot = 0.0
        if offers[HAS_PLOT, index] != 0.0:
            available = offers[PER_WORKER, index]
            marginal = offers[MARGINAL, index]
            usable = offers[USABLE, index]
            if available > 0.0 and usable > 0.0 and marginal > 0.0:
                allowed = available if available < usable else usable
                if wage <= 0.0:
                    plot = allowed
                else:
                    wanted = available * (marginal / wage) ** exponent
                    plot = allowed if allowed < wanted else wanted
            plot *= offers[WORKERS, index]
        kept = (offers[PLAN, index] if offers[PLAN, index] > plot else plot) + offers[WORK, index]
        if kept > offers[WHOLE, index]:
            kept = offers[WHOLE, index]
        total += offers[HOURS, index] - kept * offers[SHARE, index]
    return total


def pack_offers(rows):
    """The matrix `sold_hours` reads, from rows of (hours, whole, plan, work, plot parameters or None)."""
    offers = np.zeros((10, len(rows)))
    for index, (hours, whole, plan, work, parameters) in enumerate(rows):
        offers[HOURS, index], offers[WHOLE, index], offers[PLAN, index], offers[WORK, index] = hours, whole, plan, work
        offers[SHARE, index] = hours / whole
        if parameters is not None:
            offers[HAS_PLOT, index] = 1.0
            offers[PER_WORKER:WORKERS + 1, index] = parameters
    return offers
