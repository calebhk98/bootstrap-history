"""Complaint 135 on a whole game (slow): a glut of the coin metal lowers its market price and so the coin's
value, which shows as a higher price level; the wage's food and tool terms read the same clearing."""
from .harness import *  # noqa: F401,F403
from functools import partial

sim = partial(sim, agent_economy=False)   # the engine's own yearly market

s = sim(civ="rome_100ad", capital=1e9)
metal = s.home_coin_metal()
level_before = s.home_price_level()
s.goods_market.add_stock(metal, s.market_state(metal)["capacity_tonnes"] * 5.0)
s.revalue_coin_metals()
check("a glut of the coin metal lowers its market ratio", s.coin_metal_ratio(metal) < 1.0, s.coin_metal_ratio(metal))
check("...and raises the price level: the coin buys less",
      s.home_price_level() > level_before, (level_before, s.home_price_level()))
check("the wage's food term is the staple's clearing",
      abs(s.labour.wage_cost_factors("smith")["food"]
          - s.market_price_ratio(s.civ.get("staple", "wheat_kg"))) < 1e-9, None)
