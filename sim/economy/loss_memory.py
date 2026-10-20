"""What a lender expects to lose: a rate per year of exposure that ages, kept apart from the lifetime loss stock.

`record.credit_losses` only grows (the money audit and the accounts read it as a stock). The ask reads
`record.loss_rates` instead: each year a lender's losses over its exposure that year (what it lost plus what it is
still owed) are blended into the rate it carried, so a loss long ago fades and a lender losing every year keeps a
high rate. Works on an agent id, so a household, a bank or a state lends by the same rule.
"""
from typing import Dict, Mapping

from sim.constants import declare

from .credit_claims import claims_by_lender

LOSS_RATE_SMOOTHING_SHARE = declare(
    "LOSS_RATE_SMOOTHING_SHARE", 0.3, kind="temporary_heuristic",
    unit="share of the year's loss rate blended into the lender's remembered rate each year", source=None, confidence="D",
    retire="Complaints/655: a lender's expectation follows from the default process it faces, not a fixed memory share",
    why="How fast a lender's expected loss follows its latest year. Larger forgets sooner; the size is not derived.")


def age(record, money: str, share: float = None) -> None:
    """Close the year for every lender: blend this year's loss rate into its remembered rate."""
    share = LOSS_RATE_SMOOTHING_SHARE if share is None else share
    lost = {agent: max(0.0, total - record.losses_seen.get(agent, 0.0)) for agent, total in record.credit_losses.items()}
    record.loss_rates = blend(record.loss_rates, lost, claims_by_lender(record.loans, money), share)
    record.losses_seen = dict(record.credit_losses)


def blend(remembered: Mapping[str, float], lost: Mapping[str, float], claims: Mapping[str, float],
          share: float) -> Dict[str, float]:
    """Each lender's remembered rate moved `share` of the way to this year's losses over its exposure."""
    rates: Dict[str, float] = {}
    for agent in set(remembered) | {agent for agent, amount in lost.items() if amount > 0.0}:
        year_lost = lost.get(agent, 0.0)
        exposure = year_lost + max(0.0, claims.get(agent, 0.0))
        year_rate = year_lost / exposure if exposure > 0.0 else 0.0
        rate = (1.0 - share) * remembered.get(agent, 0.0) + share * year_rate
        if rate > 1e-9:
            rates[agent] = rate
    return rates
