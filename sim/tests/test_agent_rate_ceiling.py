"""A queue of keen borrowers (a merchant's cap is the interest rate plus its trade return) can clear the agent
credit market at several times the civilisation's starting rate. The rate the economy reports must stay inside the
loanable-funds ceiling (real rate plus the inflation lenders expect), or debt compounds past any credit limit. Pure rate
functions: the numbers are built here."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.world import capital_market

from sim.economy import reported_rate

starting = 0.08
ceiling = starting * capital_market.RATE_CEILING_SHARE
check("the market rate reported stops at the ceiling",
      reported_rate.reported_rate(starting, 5.0, None, 0.0) == ceiling, reported_rate.reported_rate(starting, 5.0, None, 0.0))
check("the ceiling bounds the real rate: the inflation lenders expect lifts the nominal bound",
      abs(reported_rate.reported_rate(starting, 5.0, None, 0.1) - (ceiling + 0.1)) < 1e-12)
check("a rate inside the ceiling passes through unchanged",
      reported_rate.reported_rate(starting, starting * 0.5, None, 0.0) == starting * 0.5)
check("the year's loan-weighted average is the rate reported, not the last base rate",
      reported_rate.reported_rate(starting, 0.06, 0.09, 0.0) == 0.06)
check("with no clearing that lent, the remembered base rate is reported",
      reported_rate.reported_rate(starting, None, 0.09, 0.0) == 0.09)
check("the economy that holds no rate reports none", reported_rate.reported_rate(starting, None, None, 0.0) is None)
check("the engine-facing answer before the agent market has answered is the starting rate",
      capital_market.market_rate_answered(starting, None) == starting)
check("the engine-facing answer is the economy's reported rate unchanged",
      capital_market.market_rate_answered(starting, 0.3) == 0.3)
