"""Price ratios in real terms, all read from one economy so no money scale enters (price_rules.py says why).

While the economy opens there are no prices to set against each other, and every ratio is one.
Needs: agent_prices, home_coin_metal, wage_materials."""
from typing import Any, Optional, Set, Tuple

from . import price_rules

INDICATORS = "indicators"


class PriceRatios:

    def agent_basket(self, excluded: Set[str]) -> Optional[Tuple[Any, Any, float]]:
        """(prices now, baseline prices, the geometric mean of the basket's price change excluding the named
        goods), or None while the economy opens. The first read that finds prices fixes the baseline."""
        prices = self.needs.agent_prices()
        if prices is None:
            return None
        baseline = self.world.agent_baseline_prices
        if not baseline:
            baseline.update(price_rules.opening_baseline(prices))
        return prices, baseline, price_rules.basket_level(prices, baseline, excluded)

    def real_price_ratio(self, material: str) -> float:
        """The material's price against the other goods' now, over the same at the baseline; one while the
        economy opens."""
        basket = self.agent_basket({material})
        if basket is None:
            return 1.0
        prices, baseline, level = basket
        return price_rules.price_ratio(baseline.get(material), prices.get(material), level)

    def coin_value_ratio(self, metal: str) -> float:
        """What the coin of this metal buys now over what it bought at the baseline. The home coin is the agent
        economy's money, worth what the goods basket costs in it (the metal's own price left out, so a spike in
        the metal's market does not move it); a partner's coin is not priced there, so it keeps its baseline
        value. One while the economy opens."""
        basket = self.agent_basket({metal})
        if basket is None:
            return 1.0
        return 1.0 / basket[2] if metal == self.needs.home_coin_metal() else 1.0

    def last_market_price_ratio(self, material: str) -> float:
        """The material's real price ratio at the last year's close; one before any close. A wage is set before
        the year's market clears (the clearing prices imports at a partner's landed price, which needs a wage
        quote), so wages read this recorded ratio, never the live clearing."""
        return self.world.wage_market_ratios.get(material, 1.0)

    def record_wage_market_ratios(self, seats: Any = None) -> None:
        """Record the real price ratio of the staple and of every trade's tool materials."""
        ratios = self.world.wage_market_ratios
        for material in self.needs.wage_materials():
            ratios[material] = price_rules.wage_ratio(self.real_price_ratio(material))
        self.bump(INDICATORS)
