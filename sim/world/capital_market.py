"""A loanable-funds market: what is saved against what is borrowed, and the rate that balance implies.

Nothing here knows about a civilisation, the founder or a state. The balance is a ratio of funds
demanded to funds held; the rate is the civilisation's starting rate (an initial condition) scaled by
how far that ratio has moved from its starting value; a borrower pays that rate plus a premium for its
own arrears, less a discount for its own standing.
"""
from typing import Optional

from sim.constants import declare

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



def bounded_rate(starting_rate: float, rate: float) -> float:
    """A market rate held under the ceiling: however keen the queue of borrowers, lenders' own risk and the
    borrowers' turn to other means stop the rate there."""
    return min(rate, starting_rate * RATE_CEILING_SHARE)


def market_rate_answered(starting_rate: float, agent_rate: Optional[float]) -> float:
    """The market rate: the agent credit market's answer held under the ceiling, or the starting rate while
    that market has not yet answered."""
    return starting_rate if agent_rate is None else bounded_rate(starting_rate, agent_rate)


def capital_recovery_factor(rate: float, life_years: float) -> float:
    """The yearly share of a plant's cost that repays it over its life with interest at `rate` on what is
    still unpaid: one over the life when the rate is nil, the rate when the life is endless."""
    if life_years <= 0.0:
        raise ValueError("a plant needs a positive life")
    if rate <= 0.0:
        return 1.0 / life_years
    return rate / (1.0 - (1.0 + rate) ** -life_years)


def establishment_carry_factor(rate: float, establishment_years: float) -> float:
    """What a build bill spent evenly over `establishment_years` has grown to by the first bearing year, per unit
    of the bill: each year's outlay earns interest only from the year it is spent. One at a nil rate or no wait."""
    if establishment_years < 0.0:
        raise ValueError("establishment years cannot be negative")
    if rate <= 0.0 or establishment_years == 0.0:
        return 1.0
    return ((1.0 + rate) ** establishment_years - 1.0) / (rate * establishment_years)


def bearing_years(life_years: float, establishment_years: float) -> float:
    """Years a stand yields in: its life from planting less the years before it first bears (none are yielded in)."""
    if establishment_years >= life_years:
        raise ValueError("a stand must outlive the years before it bears")
    return life_years - establishment_years


def stand_yearly_share(rate: float, life_years: float, establishment_years: float = 0.0) -> float:
    """The yearly share of a stand's build bill that its bearing years repay: the bill carried to first bearing
    (`establishment_carry_factor`), then recovered over the bearing years. As `capital_recovery_factor` when
    there is no wait."""
    return (establishment_carry_factor(rate, establishment_years)
            * capital_recovery_factor(rate, bearing_years(life_years, establishment_years)))


def borrower_rate(market_rate: float, standing_discount: float, share_of_ceiling_used: float) -> float:
    """What one borrower pays: never less than the market rate (what the market itself pays savers), plus
    the part of the arrears premium that its standing does not remove. A discount only removes premium."""
    used = max(0.0, min(1.0, share_of_ceiling_used))
    premium = market_rate * ARREARS_PREMIUM_AT_CEILING * used
    return market_rate + max(0.0, premium - max(0.0, standing_discount))


def perpetuity_value(yearly_income: float, rate: float, rate_floor: float = 1e-9) -> float:
    """What an income of `yearly_income` a year for good is worth now at `rate`: its present value. The rate is held
    at `rate_floor` so a nil rate does not make the income worth infinity."""
    return max(0.0, yearly_income) / max(rate, rate_floor)


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


