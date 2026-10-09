"""Price ratios in real terms, all read from one economy so no money scale enters.

On the agent economy the price over the incumbents' cost is a ratio across scales: the cost follows the money
per labour hour, which follows the coin's revaluation, so a revaluation measured that way moves itself (a
loop). Here a good's price is set against the other goods' prices (a basket fixed at the baseline, the first
close that read it), both in the agent economy's own coin. That economy's goods prices do not read the
engine's money per labour hour, so the measure cannot be moved by what it drives. On the engine path the
market's ratio over cost is already real (price and cost share a money) and is used as it is.
"""
import math


class RealPriceRatiosMixin:

    def _agent_basket(self, excluded):
        """(prices now, baseline prices, the geometric mean of the basket's price change excluding the named
        goods), or None while the economy opens."""
        prices = self.economy.agent_prices()
        if prices is None:
            return None
        baseline = self.state.economy.agent_baseline_prices
        if not baseline:
            baseline.update({good: price for good, price in prices.items() if price > 0.0})
        logs = [math.log(prices[good] / base) for good, base in sorted(baseline.items())
                if good not in excluded and prices.get(good, 0.0) > 0.0]
        return prices, baseline, math.exp(sum(logs) / len(logs)) if logs else 1.0

    def real_price_ratio(self, material):
        """The material's price against the other goods' now, over the same at the baseline; the engine's
        market ratio while the economy opens."""
        basket = self._agent_basket({material})
        if basket is None:
            return self.market_price_ratio(material)
        prices, baseline, level = basket
        own_base, own_now = baseline.get(material), prices.get(material)
        if not own_base or not own_now or own_now <= 0.0:
            return 1.0
        return (own_now / own_base) / level

    def coin_value_ratio(self, metal):
        """What the coin of this metal buys now over what it bought at the baseline. The engine path: the
        metal's market ratio. The agent economy: the home coin is that economy's money, worth what the goods
        basket costs in it (the metal's own price left out, so a spike in the metal's market does not move
        it); a partner's coin is not priced there, so it keeps its baseline value."""
        basket = self._agent_basket({metal})
        if basket is None:
            return self.market_price_ratio(metal)
        return 1.0 / basket[2] if metal == self.home_coin_metal() else 1.0
