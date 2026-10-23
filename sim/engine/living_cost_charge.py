"""What a seat's money phase charges as living costs in a year."""


def living_cost_charged(living_cost, dependants_beyond_means, wages_prepaid):
    """The living cost to pay this year: the whole cost less the dependants the income cannot carry, less the wages already
    paid in advance (never below zero for the advance: an advance larger than the cost nets it to zero)."""
    carried = living_cost - dependants_beyond_means
    return carried - min(carried, wages_prepaid)
