"""A price ratio in real terms: a material's price against a fixed basket of the other goods, over the same
at the baseline, all read from one economy.

On the agent economy the price over the incumbents' cost is a ratio across scales: the cost follows the money
per labour hour, which follows the coin metal's revaluation, so a revaluation measured that way moves itself
(a loop). The relative price has no money in it. On the engine path the market's ratio over cost is already
real (price and cost share a money), and is used as it is.
"""
import math


class RealPriceRatiosMixin:

    def real_price_ratio(self, material):
        """The material's price against the other goods' now, over the same at the baseline (the first close
        that read it); the engine's market ratio when the agent economy is off."""
        prices = self.economy.agent_prices()
        if prices is None:
            return self.market_price_ratio(material)
        baseline = self.state.economy.agent_baseline_prices
        if not baseline:
            baseline.update({good: price for good, price in prices.items() if price > 0.0})
        own_base, own_now = baseline.get(material), prices.get(material)
        if not own_base or not own_now or own_now <= 0.0:
            return 1.0
        logs = [math.log(prices[good] / base) for good, base in sorted(baseline.items())
                if good != material and prices.get(good, 0.0) > 0.0]
        basket = math.exp(sum(logs) / len(logs)) if logs else 1.0
        return (own_now / own_base) / basket
