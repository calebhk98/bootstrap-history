"""The hours a market's offers sell at a wage, over arrays (the kernel behind `labour_supply.HourSupply.hours_at` in the
economy, and the schedule the clearing kernels read every market's hours from).

Per offer, the hours sold are its hours less the share of the hours its worker keeps at home that falls to it; what the
worker keeps is the larger of its plan and its plot's hours at the wage, plus its household work, no more than its year.
The plot's hours are the cohort's workers times the parametric plot schedule written out here.

The offers sit in the columns of one matrix (one call argument is cheaper than ten); a market is a range of columns."""
from sim.jit import njit

OFFER_HOURS, OFFER_WHOLE, OFFER_SHARE, OFFER_PLAN, OFFER_WORK, OFFER_HAS_PLOT, OFFER_PER_WORKER, OFFER_MARGINAL, \
    OFFER_USABLE, OFFER_WORKERS = range(10)
OFFER_ROWS = 10


@njit
def sold_hours_range(wage, offers, exponent, first, last):
    """The hours sold at a wage by the offers in columns `first` up to `last`."""
    total = 0.0
    for index in range(first, last):
        plot = 0.0
        if offers[OFFER_HAS_PLOT, index] != 0.0:
            available = offers[OFFER_PER_WORKER, index]
            marginal = offers[OFFER_MARGINAL, index]
            usable = offers[OFFER_USABLE, index]
            if available > 0.0 and usable > 0.0 and marginal > 0.0:
                allowed = available if available < usable else usable
                if wage <= 0.0:
                    plot = allowed
                else:
                    wanted = available * (marginal / wage) ** exponent
                    plot = allowed if allowed < wanted else wanted
            plot *= offers[OFFER_WORKERS, index]
        kept = (offers[OFFER_PLAN, index] if offers[OFFER_PLAN, index] > plot else plot) + offers[OFFER_WORK, index]
        if kept > offers[OFFER_WHOLE, index]:
            kept = offers[OFFER_WHOLE, index]
        total += offers[OFFER_HOURS, index] - kept * offers[OFFER_SHARE, index]
    return total


@njit
def sold_hours(wage, offers, exponent):
    return sold_hours_range(wage, offers, exponent, 0, offers.shape[1])
