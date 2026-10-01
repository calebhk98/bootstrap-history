"""A loanable-funds market: what is saved against what is borrowed, and the rate that balance implies.

Nothing here knows about a civilisation, the founder or a state. The balance is a ratio of funds
demanded to funds held; the rate is the civilisation's starting rate (an initial condition) scaled by
how far that ratio has moved from its starting value; a borrower pays that rate plus a premium for its
own arrears, less a discount for its own standing.
"""
from sim.constants import declare

FOUNDER_LOAN = "founder"  # the founder's id among the market's borrowers

RATE_ELASTICITY = declare(
    "RATE_ELASTICITY", 0.5, kind="temporary_heuristic",
    unit="proportional change of the rate per proportional change of the balance", source=None,
    confidence="D",
    why="How strongly the yearly rate answers a shift in funds demanded against funds held. Stands in for "
        "lenders' and borrowers' bargaining over a scarce pool, which is not modelled.")
RATE_FLOOR_SHARE = declare(
    "RATE_FLOOR_SHARE", 0.25, kind="temporary_heuristic",
    unit="share of the starting rate", source=None, confidence="D",
    why="The lowest the market rate falls however plentiful funds are; lenders always have the option of "
        "holding grain or coin, whose return is not modelled.")
RATE_CEILING_SHARE = declare(
    "RATE_CEILING_SHARE", 4.0, kind="temporary_heuristic",
    unit="multiple of the starting rate", source=None, confidence="D",
    why="The highest the market rate rises however scarce funds are; beyond it borrowers stop borrowing "
        "and lenders turn to the risks of lending to desperate borrowers, which are not modelled.")
ARREARS_PREMIUM_AT_CEILING = declare(
    "ARREARS_PREMIUM_AT_CEILING", 0.5, kind="temporary_heuristic",
    unit="share of the market rate added at the credit ceiling", source=None, confidence="D",
    why="What a borrower at the limit of what lenders will advance pays over the market rate, rising "
        "in proportion to the share of the ceiling used. Stands in for a default-probability model.")
LENDER_RESERVE_SHARE = declare(
    "LENDER_RESERVE_SHARE", 0.2, kind="temporary_heuristic",
    unit="share of the funds lenders hold", source=None, confidence="D",
    why="The part of what lenders hold that they keep back and never lend out; stands in for liquidity "
        "needs and for the risks of lending out everything.")


def utilisation(demand: float, supply: float) -> float:
    """Funds demanded per unit of funds held."""
    return demand / supply if supply > 0.0 else float("inf")


def rate_for_balance(starting_rate: float, current_utilisation: float, reference_utilisation: float) -> float:
    """The market rate: the starting rate scaled by how the balance has moved from its starting value."""
    if reference_utilisation <= 0.0 or current_utilisation <= 0.0:
        return starting_rate * RATE_FLOOR_SHARE
    if current_utilisation == float("inf"):
        return starting_rate * RATE_CEILING_SHARE
    scaled = (current_utilisation / reference_utilisation) ** RATE_ELASTICITY
    return starting_rate * max(RATE_FLOOR_SHARE, min(RATE_CEILING_SHARE, scaled))


def borrower_rate(market_rate: float, standing_discount: float, share_of_ceiling_used: float) -> float:
    """What one borrower pays: never less than the market rate (what the market itself pays savers), plus
    the part of the arrears premium that its standing does not remove. A discount only removes premium."""
    used = max(0.0, min(1.0, share_of_ceiling_used))
    premium = market_rate * ARREARS_PREMIUM_AT_CEILING * used
    return market_rate + max(0.0, premium - max(0.0, standing_discount))


def headroom(capacity: float, lent: float) -> float:
    """What lenders can still advance: what they will lend less what is lent."""
    return max(0.0, capacity - lent)


def serviceable_debt(earning: float, rate: float, service_share: float) -> float:
    """The debt whose yearly interest stays within `service_share` of the standing earning."""
    if rate <= 0.0:
        return 0.0
    return max(0.0, earning) * service_share / rate


def lendable_capacity(supply: float) -> float:
    """What lenders will lend out of the funds they hold."""
    return supply * (1.0 - LENDER_RESERVE_SHARE)


