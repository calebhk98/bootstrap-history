"""Complaints/507 stage 5: a concern's market factor is its baskets at the economy's prices over the same baskets
at the long-run cost of making, one function of the baskets and the two price lists (not of a node)."""
from .harness import *  # noqa: F401,F403

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

# --- a game: the factor of a running concern is its baskets at the economy's price over its baskets at cost.
game = sim(civ="rome_100ad", capital=5_000_000.0)
economy_price, long_run = game.goods_market.home_unit_price, game._material_prices()


def node_with_market():
    """A concern whose goods the economy prices, and which earns at long-run cost."""
    for candidate in sorted(game.nodes):
        baskets = game.concern_baskets_now(candidate) if game.nodes[candidate].get("_revenue_basis") == "output" else None
        if baskets is not None and baskets.outputs and game.concern_goods_have_market(candidate) \
                and any(economy_price(material) not in (None, long_run.get(material)) for material in baskets.outputs) \
                and sum(units * long_run.get(material, 0.0) for material, units in baskets.outputs.items()) > \
                sum(units * long_run.get(material, 0.0) for material, units in baskets.purchases.items()):
            return candidate, baskets
    return None, None


node_id, baskets = node_with_market()
check("some concern sells goods the economy prices", node_id is not None)


def net(price_of):
    return (sum(units * price_of(material) for material, units in baskets.outputs.items())
            - sum(units * price_of(material) for material, units in baskets.purchases.items()))


def shown(material):
    price = economy_price(material)
    return long_run[material] if price is None else price


expected = net(shown) / net(lambda material: long_run[material])
factor = game.node_output_market_factor(game.nodes[node_id])
check("the node's factor is the economy's price over the cost of making, over its baskets",
      abs(factor - expected) < 1e-9 * max(1.0, abs(expected)), (factor, expected))
game.goods_market.home_unit_price = lambda material: 2.0 * shown(material)
check("a market twice as dear for everything the concern trades doubles its factor",
      abs(game.node_output_market_factor(game.nodes[node_id]) - 2.0 * expected) < 1e-9 * max(1.0, abs(expected)),
      (game.node_output_market_factor(game.nodes[node_id]), expected))
