"""A queue of keen borrowers (a merchant's cap is the interest rate plus its trade return) can clear the agent
credit market at several times the civilisation's starting rate. The rate a household pays on arrears must
stay inside the loanable-funds ceiling, or debt compounds past any credit limit."""
from .harness import *  # noqa: F401,F403
from sim.world import capital_market

game = sim()
starting = float(game.civ["starting_interest_rate"])
ceiling = starting * capital_market.RATE_CEILING_SHARE
game.economy.agent_rate = lambda: 5.0
check("the market rate answered by the agent economy stops at the ceiling",
      game.market_rate() <= ceiling + 1e-12, game.market_rate())
game.state.household.capital = -1.0e6
widest = capital_market.borrower_rate(ceiling, 0.0, 1.0)
check("a borrower's rate on arrears is bounded however keen the other borrowers are",
      game.debt_interest_rate() <= widest + 1e-12, game.debt_interest_rate())
game.economy.agent_rate = lambda: starting * 0.5
check("a rate inside the ceiling passes through unchanged",
      abs(game.market_rate() - starting * 0.5) < 1e-12, game.market_rate())
