"""When a lost trade is taught again: which trades are gone, which are past their cooldown, and what the household
can spend on teaching one."""

from .constants import (CAPITAL_SHARE_FOR_PROJECT_IN_HAND, PROJECT_IN_HAND_SCORE,
                        SPARE_SHARE_FOR_SPECULATIVE_TRADE)


def trade_is_gone(available, market_supply, headcount_pending):
    """A trade that no longer exists here, or exists but has nobody left on the market and nobody being taught."""
    return (not available) or (market_supply <= 0.0 and headcount_pending <= 0.0)


def past_cooldown(want, last_taught, year, reteach_every):
    """The wanted trades not taught within `reteach_every` years (a trade never taught is always past it)."""
    return {trade_id: value for trade_id, value in want.items()
            if year - last_taught.get(trade_id, -999) >= reteach_every}


def teaching_budget(score, spare_income, capital):
    """What the household may spend on keeping the people it would teach: a trade a project in hand waits on
    may borrow against capital, any other must come out of the spare income."""
    if score >= PROJECT_IN_HAND_SCORE:
        return max(0.0, spare_income) + max(0.0, capital) * CAPITAL_SHARE_FOR_PROJECT_IN_HAND
    return max(0.0, spare_income) * SPARE_SHARE_FOR_SPECULATIVE_TRADE
