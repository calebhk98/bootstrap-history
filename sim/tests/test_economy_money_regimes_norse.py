"""Norse weighed silver on the agent economy: more metal mined raises the money stock, and the mint holds the metal of
the money in circulation (its own topic: see test_economy_money_regimes.py; prices: test_money_reaches_prices)."""
from .harness import *  # noqa: F401,F403
from .money_regimes_play import check_more_metal_raises_money, check_more_metal_raises_price_level

check_more_metal_raises_money("norse_900ad")
check_more_metal_raises_price_level("norse_900ad")
