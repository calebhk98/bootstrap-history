"""What a lender expects to lose: a rate per year of exposure that ages, kept apart from the lifetime loss stock.

`record.credit.credit_losses` only grows (the money audit and the accounts read it as a stock). The ask reads
`record.credit.loss_rates` instead: each year a lender's losses over its exposure that year (what it lost plus what it is
still owed) are blended into the rate it carried, so a loss long ago fades and a lender losing every year keeps a
high rate. Works on an agent id, so a household, a bank or a state lends by the same rule.
"""
from typing import Dict, Mapping, Optional

from sim.constants import declare

from .claim_terms import mean_term_years
from .credit_claims import claims_by_lender

LOSS_RATE_SMOOTHING_SHARE = declare(
    "LOSS_RATE_SMOOTHING_SHARE", 0.3, kind="temporary_heuristic",
    unit="share of the year's loss rate blended into the lender's remembered rate each year", source=None, confidence="D",
    retire="Complaints/641: a lender's expectation follows from the default process it faces, not a fixed memory share",
    why="How fast a lender's expected loss follows its latest year. Larger forgets sooner; the size is not derived.")

ONE_YEAR = 1.0    # the span of a year's books: a loss written off in it was exposed at least this long


def age(record, money: str, year: int, share: float = None) -> None:
    """Close the year for every lender: blend this year's loss rate into its remembered rate."""
    share = LOSS_RATE_SMOOTHING_SHARE if share is None else share
    lost = {agent: max(0.0, total - record.credit.losses_seen.get(agent, 0.0)) for agent, total in record.credit.credit_losses.items()}
    lives, book_life = mean_term_years(record.credit.loans, year, money)
    # a claim lost this year had left the book by now: its life is read from the book as the last close left it
    kept_book_life = record.credit.book_claim_life if record.credit.book_claim_life is not None else book_life
    record.credit.loss_rates = blend(record.credit.loss_rates, lost, claims_by_lender(record.credit.loans, money), share,
                                     {**lives, **record.credit.claim_lives}, kept_book_life)
    record.credit.claim_lives, record.credit.book_claim_life = lives, book_life
    record.credit.losses_seen = dict(record.credit.credit_losses)


def blend(remembered: Mapping[str, float], lost: Mapping[str, float], claims: Mapping[str, float],
          share: float, claim_lives: Mapping[str, float] = None, book_life: Optional[float] = None) -> Dict[str, float]:
    """Each lender's remembered rate moved `share` of the way to this year's loss rate: what it lost over the years of
    exposure it had to it (the claims it still holds for the year, what it lost for the life that claim was held), so a
    lender that lost its only claim does not read the whole of it as one year's loss. A claim's life is the mean term of the
    claims the lender holds (`claim_lives`), else of every claim on the book (`book_life`), else one year: the year the loss
    is written off in, the least exposure it can have had."""
    claim_lives = claim_lives or {}
    rates: Dict[str, float] = {}
    for agent in sorted(set(remembered) | {agent for agent, amount in lost.items() if amount > 0.0}):    # name order: a save must not follow string hashing
        year_lost = lost.get(agent, 0.0)
        life = claim_lives.get(agent, book_life)
        life = ONE_YEAR if life is None else max(ONE_YEAR, life)
        exposure = year_lost * life + max(0.0, claims.get(agent, 0.0))
        year_rate = year_lost / exposure if exposure > 0.0 else 0.0
        rate = (1.0 - share) * remembered.get(agent, 0.0) + share * year_rate
        if rate > 1e-9:
            rates[agent] = rate
    return rates
