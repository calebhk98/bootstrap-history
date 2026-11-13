"""What a household spends on its store of durable goods in a year (plain floats, so the kernels call the same code).

The store is held at a wanted value. What wears out of it each year is bought back at once, since a worn-out durable is a loss
the household replaces. A larger shortfall (prices fell, or the savings the store is a share of rose) is a reallocation: it is
bought only once it passes the rebalance band, and then over several years, so one year's swing in the target is not one year's
demand for the same few goods."""
from sim.constants import declare
from sim.jit import njit

STORE_GAP_CLOSING = declare(
    "STORE_GAP_CLOSING", 0.3, kind="temporary_heuristic", unit="share of the shortfall bought a year", source=None, confidence="D",
    retire="Complaints/473: the store target follows smoothed wealth and usual prices, so a shortfall is not a one-year event",
    why="A household whose store is short of its target beyond the band buys this share of the shortfall a year (and never less "
        "than a year's wear). The share is the one the household closes the gap to its expected spending by "
        "(EXPECTED_SPENDING_ADJUSTMENT); real households' pace in reallocating a portfolio is not modelled.")


@njit
def store_spend(wanted: float, held_value: float, replacement_share: float, pot: float, band: float) -> float:
    """Money to spend on the store: nothing at or above `wanted`; inside the band the shortfall up to a year's wear (`replacement_share`
    of `wanted`, the weighted wear share of the store's goods); past the band the larger of that and `STORE_GAP_CLOSING` of the
    shortfall; never above the shortfall or `pot`."""
    if held_value >= wanted:
        return 0.0
    shortfall = wanted - held_value
    wear = wanted * replacement_share
    if held_value < wanted * (1.0 - band):
        return min(pot, shortfall, max(wear, STORE_GAP_CLOSING * shortfall))
    return min(pot, shortfall, wear)
