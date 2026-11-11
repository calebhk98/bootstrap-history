"""What a lender expects to lose: a rate per year of exposure that ages, kept apart from the lifetime loss stock.

`record.credit.credit_losses` only grows (the money audit and the accounts read it as a stock). The ask reads
`record.credit.loss_rates` instead: each year a lender's losses over its exposure that year (what it lost plus what it is
still owed) are blended into the rate it carried, so a loss long ago fades and a lender losing every year keeps a
high rate. Works on an agent id, so a household, a bank or a state lends by the same rule.
"""
from typing import Dict, Mapping

from sim.constants import declare

from .credit_claims import claims_by_lender

LOSS_RATE_SMOOTHING_SHARE = declare(
    "LOSS_RATE_SMOOTHING_SHARE", 0.3, kind="temporary_heuristic",
    unit="share of the year's loss rate blended into the lender's remembered rate each year", source=None, confidence="D",
    retire="Complaints/641: a lender's expectation follows from the default process it faces, not a fixed memory share",
    why="How fast a lender's expected loss follows its latest year. Larger forgets sooner; the size is not derived.")
LOSS_CLAIM_LIFE_YEARS = declare(
    "LOSS_CLAIM_LIFE_YEARS", 3.0, kind="temporary_heuristic",
    unit="years a claim that was lost had been exposed", source=None, confidence="D",
    retire="Complaints/106: a defaulted claim carries the years it was held, read from the loan itself",
    why="A claim lost this year was exposed for its whole life, not for the one year it is written off in, so its loss is "
        "spread over that life. A single typical life stands in for the loan's own term, which the default record omits.")


def age(record, money: str, share: float = None) -> None:
    """Close the year for every lender: blend this year's loss rate into its remembered rate."""
    share = LOSS_RATE_SMOOTHING_SHARE if share is None else share
    lost = {agent: max(0.0, total - record.credit.losses_seen.get(agent, 0.0)) for agent, total in record.credit.credit_losses.items()}
    record.credit.loss_rates = blend(record.credit.loss_rates, lost, claims_by_lender(record.credit.loans, money), share)
    record.credit.losses_seen = dict(record.credit.credit_losses)


def blend(remembered: Mapping[str, float], lost: Mapping[str, float], claims: Mapping[str, float],
          share: float, claim_life_years: float = None) -> Dict[str, float]:
    """Each lender's remembered rate moved `share` of the way to this year's loss rate: what it lost over the years of
    exposure it had to it (the claims it still holds for the year, what it lost for the life that claim was held), so a
    lender that lost its only claim does not read the whole of it as one year's loss."""
    life = max(1.0, LOSS_CLAIM_LIFE_YEARS if claim_life_years is None else claim_life_years)
    rates: Dict[str, float] = {}
    for agent in sorted(set(remembered) | {agent for agent, amount in lost.items() if amount > 0.0}):    # name order: a save must not follow string hashing
        year_lost = lost.get(agent, 0.0)
        exposure = year_lost * life + max(0.0, claims.get(agent, 0.0))
        year_rate = year_lost / exposure if exposure > 0.0 else 0.0
        rate = (1.0 - share) * remembered.get(agent, 0.0) + share * year_rate
        if rate > 1e-9:
            rates[agent] = rate
    return rates
