"""Kernels of the merchants' credit requests over every merchant at once: what each holds by market slot, and what each would borrow."""
import numpy

from sim.jit import njit

from .merchants_book_kernel import commit_credit


@njit
def accumulate_by_slot(owner, slot, quantity, held):
    """Add each row's quantity to `held[owner, slot]` in row order (a slot of -1 is not a market the merchants trade: skipped)."""
    for row in range(len(owner)):
        if slot[row] >= 0:
            held[owner[row], slot[row]] += quantity[row]


@njit
def commit_credit_all(offsets, destinations, sources, ranks, outlays, cash, limit, volumes, held, own_share, group_share, source_share):
    """`commit_credit` for each merchant k over its rows `offsets[k]:offsets[k + 1]` (best first), with no commitments of rivals
    (credit is asked of each merchant alone): `cash[k]`, `limit[k]`, `volumes[k]` and `held[k]` (by slot) are its own.
    Returns (wanted, gain) per merchant."""
    merchants = len(cash)
    wanted = numpy.zeros(merchants)
    gain = numpy.zeros(merchants)
    slots = volumes.shape[1]
    for merchant in range(merchants):
        low, high = offsets[merchant], offsets[merchant + 1]
        wanted[merchant], gain[merchant] = commit_credit(
            destinations[low:high], sources[low:high], ranks[low:high], outlays[low:high], cash[merchant], limit[merchant],
            volumes[merchant], held[merchant], numpy.zeros(slots), numpy.zeros(slots), numpy.zeros(slots),
            own_share, group_share, source_share)
    return wanted, gain
