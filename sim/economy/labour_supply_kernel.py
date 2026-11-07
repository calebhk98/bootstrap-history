"""Packs a market's offers into the matrix the labour core's `sold_hours` kernel reads (the hours a market's offers sell at a
wage: `labour_supply.HourSupply.hours_at`). The rule, and the matrix layout, live in the core
(`sim/labour/market/sold_hours_kernel.py`) so its clearing kernels can read every market's offers directly.

Per offer, the hours sold are its hours less the share of the hours its worker keeps at home that falls to it
(`labour_supply.hours_kept_at_home`); the plot's hours are `households_hours_offered.plot_hours_kept` times the cohort's
workers, written out in the kernel for the parametric plot schedules `household_hours_year.plot_schedule` builds."""
import numpy as np

from sim.labour.api import (OFFER_HAS_PLOT as HAS_PLOT, OFFER_HOURS as HOURS, OFFER_PER_WORKER as PER_WORKER, OFFER_PLAN as PLAN,
                            OFFER_ROWS, OFFER_SHARE as SHARE, OFFER_WHOLE as WHOLE, OFFER_WORK as WORK, OFFER_WORKERS as WORKERS,
                            sold_hours)

__all__ = ["pack_offers", "sold_hours"]


def pack_offers(rows):
    """The matrix `sold_hours` reads, from rows of (hours, whole, plan, work, plot parameters or None)."""
    offers = np.zeros((OFFER_ROWS, len(rows)))
    for index, (hours, whole, plan, work, parameters) in enumerate(rows):
        offers[HOURS, index], offers[WHOLE, index], offers[PLAN, index], offers[WORK, index] = hours, whole, plan, work
        offers[SHARE, index] = hours / whole
        if parameters is not None:
            offers[HAS_PLOT, index] = 1.0
            offers[PER_WORKER:WORKERS + 1, index] = parameters
    return offers
