"""Complaints/507 stage 5: a concern's market factor is its baskets at the economy's prices over the same baskets
at the long-run cost of making, one function of the baskets and the two price lists (not of a node)."""
from .harness import *  # noqa: F401,F403

QUICK_TOPIC = True

from sim.engine import node_revenue_market

# --- the function: net sales at the prices shown over net sales at long-run cost.
sold, bought, cost = {"a": 10.0}, {"b": 5.0}, {"a": 2.0, "b": 2.0}
check("net sales at the economy's prices over net sales at cost",
      abs(node_revenue_market.basket_market_factor(sold, bought, cost, {"a": 4.0, "b": 2.0}.get) - 3.0) < 1e-12)
check("a market that shows exactly the cost of making leaves the factor at one",
      abs(node_revenue_market.basket_market_factor(sold, bought, cost, cost.get) - 1.0) < 1e-12)
check("doubling every price the economy shows doubles the factor",
      abs(node_revenue_market.basket_market_factor(sold, bought, cost, {"a": 4.0, "b": 4.0}.get) - 2.0) < 1e-12)
check("nothing sold is a factor of one", node_revenue_market.basket_market_factor({}, bought, cost, cost.get) == 1.0)

# --- the concern's factor: the market's factor only while the economy prices what the concern sells.
from sim.engine import concern_earnings

check("a concern whose goods the economy prices takes the market's factor",
      concern_earnings.output_market_factor(True, lambda: 2.5) == 2.5)
check("a concern whose goods nobody has sold yet stays at long-run takings, a factor of one",
      concern_earnings.output_market_factor(False, lambda: 2.5) == 1.0)
check("the factor is not worked out at all while the goods have no market",
      concern_earnings.output_market_factor(False, lambda: 1 / 0) == 1.0)
check("a material the economy does not show is valued at its cost of making",
      abs(node_revenue_market.basket_market_factor(sold, bought, cost, {"a": 4.0}.get) - 3.0) < 1e-12)
