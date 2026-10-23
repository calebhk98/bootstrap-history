"""SCENARIO: the quote's volume and the throttle's market tonnes read one market figure. The routes (makeable,
unavailable, market) are rule tests in test_material_reach."""
from .harness import *  # noqa: F401,F403

game = unopened_sim(civ="rome_100ad", events=False, capital=1e9)
check("the quote's volume and the throttle's market tonnes agree",
      game.goods_market.quote("alum_kg")["market_available_tonnes_per_year"]
      == game._material_market_tonnes("alum_kg"))
