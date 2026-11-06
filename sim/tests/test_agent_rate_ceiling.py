"""A queue of keen borrowers (a merchant's cap is the interest rate plus its trade return) can clear the agent
credit market at several times the civilisation's starting rate. The rate the market answers must stay inside the
loanable-funds ceiling, or debt compounds past any credit limit. Pure rate functions: the numbers are built here."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.world import capital_market

starting = 0.08
ceiling = starting * capital_market.RATE_CEILING_SHARE
check("the market rate answered by the agent economy stops at the ceiling",
      capital_market.market_rate_answered(starting, 5.0) == ceiling, capital_market.market_rate_answered(starting, 5.0))
check("a rate inside the ceiling passes through unchanged",
      capital_market.market_rate_answered(starting, starting * 0.5) == starting * 0.5)
check("before the agent market has answered, the market rate is the starting rate",
      capital_market.market_rate_answered(starting, None) == starting)
