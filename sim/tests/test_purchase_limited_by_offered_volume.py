"""Complaint 507, stage 4: the founder cannot buy more of a material in a year than the sellers on his tile's market
offered at the last clearing; the quote's figure is the economy's own, not the engine's reference tonnes."""
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
check("...and nothing more can be bought that year", market.buy(market.acting, WHEAT, offered) == 0.0)
