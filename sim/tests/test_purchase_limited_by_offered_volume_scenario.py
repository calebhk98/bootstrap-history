"""Scenario (Complaint 507, stage 4): in a running Rome game the quote's market figure is what the agent economy offers on the
founder's tile, and an order is cut to it. The cut and the quote's sources are in test_purchase_limited_by_offered_volume."""
from .harness import *  # noqa: F401,F403

game = sim(civ="rome_100ad", capital=1e12)
market = game.goods_market
WHEAT = game.civ.get("staple") or "wheat_kg"
game._step_market()
offered = game.economy.agent_offered_tonnes(WHEAT)
check("the economy offers the staple on the founder's tile", offered is not None and offered > 0.0, offered)
quote = market.quote(WHEAT)
check("the quote's market figure is the economy's offered quantity",
      abs(quote["market_available_tonnes_per_year"] - offered) <= 1e-9 * offered, (quote["market_available_tonnes_per_year"], offered))
bought = market.buy(market.acting, WHEAT, 10.0 * offered)
check("an order of ten times the offer is cut to the offer", abs(bought - offered) <= 1e-9 * offered, (bought, offered))
