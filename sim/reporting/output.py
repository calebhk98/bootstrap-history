"""Real output: the quantity of goods the economy sells, valued at fixed opening prices.

No technology count and no index stand in for it. The opening basket is the economy's own: the quantity of each
good households bought when it opened, valued at the economy's opening prices in hours of the unskilled trade's
opening wage. The economy's volumes (over the markets of the country measured, so a partner country's trade does
not stand in a home population's output) do not start at those quantities, so they are measured against the first
year each good cleared any, and a single scale carries that year onto the opening basket's value. With the traded
units of a good, its baseline, its opening price and the scale,

    real output = scale * sum over goods of (traded units * opening price in hours)

and it equals the opening basket's value in the baseline year, whatever the economy traded then. A good's weight is
what the economy actually trades of it, so a good it barely trades cannot swing the total. A technique raises output
only by lowering the cost of a good, which raises what the economy's households buy and its markets clear.
Population does not enter: a smaller society trades less and has fewer heads.

A good the opening basket did not hold but households want once a technique offers it has no opening price. Once the
economy trades it, it counts at the price it was first offered at, in the units the economy trades of it.

TEMPORARY HEURISTIC (CLAUDE.md 4.4): a new good counts at its introduction price, standing for a chained basket
(re-based each year, quantity index linked), which would also credit what it saves.
Needs: agent_opening_basket, agent_volume_baseline, agent_traded_volumes, new_goods_units, household_prices,
money_per_labour_hour, population_total, opening_population."""
from typing import Any, Dict, List, Optional, Tuple

from . import output_rules

INDICATORS = "indicators"


class Output:
    _basket: Optional[Tuple[Any, Dict[str, Dict[str, float]]]] = None   # (world it was read for, the basket); never saved

    def base_basket(self) -> Dict[str, Dict[str, float]]:
        """{"prices": {good: opening price in labour hours}, "units": {good: units a year households bought at the
        opening}}: the agent economy's own opening basket. Empty while the economy opens."""
        if self._basket is not None and self._basket[0] is self.world:
            return self._basket[1]
        opened = self.needs.agent_opening_basket()
        if opened is None:
            return {"prices": {}, "units": {}}
        units, prices = opened
        units = {good: wanted for good, wanted in sorted(units.items()) if wanted > 0.0 and prices.get(good, 0.0) > 0.0}
        basket = {"prices": prices, "units": units}
        self._basket = (self.world, basket)
        return basket

    def traded_measure(self) -> Tuple[Dict[str, float], float]:
        """({good: units the economy traded last year}, scale) over the opening basket's goods that have a baseline;
        the scale carries the baseline year onto the opening basket's value, so real output starts at it."""
        return output_rules.traded_measure(
            self.base_basket(), self.needs.agent_volume_baseline() or {}, self.needs.agent_traded_volumes() or {})

    def real_output_lines(self, measure: Any = None) -> List[Tuple[str, float, float]]:
        """[(material, units a year sold now, opening price in labour hours)] for every good in the opening basket the
        economy has traded. `measure` is `traded_measure()`, which a caller shares between its reads within one moment."""
        traded, scale = self.traded_measure() if measure is None else measure
        return output_rules.output_lines(
            self.base_basket(), traded, scale, self.world.introduction_prices,
            self.needs.new_goods_units(), self.needs.agent_traded_volumes() or {})

    def real_output_hours(self, measure: Any = None) -> float:
        """Quantities sold this year at the opening prices, in labour hours."""
        return sum(quantity * price for _material, quantity, price in self.real_output_lines(measure))

    def opening_output_hours(self, measure: Any = None) -> float:
        """The opening basket's value over the goods the measure holds."""
        basket = self.base_basket()
        traded, _scale = self.traded_measure() if measure is None else measure
        return sum(basket["units"][good] * basket["prices"][good] for good in traded)

    def real_output_per_head(self) -> float:
        """Real output per person over the opening's, as last year's market closed it; one at the baseline."""
        return self.world.output_per_head

    def money_real(self) -> float:
        return self.world.money_real

    def close_real_output(self, command: Any = None) -> None:
        """Measure the year's real output per head once the market has closed."""
        per_hour = self.needs.money_per_labour_hour()
        prices = self.needs.household_prices()
        for material in self.needs.new_goods_units():
            self.world.introduction_prices.setdefault(material, prices[material] / per_hour)
        measure = self.traded_measure()
        opening = self.opening_output_hours(measure)
        people = float(self.needs.population_total()) / self.needs.opening_population()
        if opening > 0.0 and people > 0.0:
            self.world.output_per_head = self.real_output_hours(measure) / opening / people
        self.bump(INDICATORS)

    def erode_money(self, command: Any) -> None:
        self.world.money_real *= (1 - command.share)
        self.bump(INDICATORS)
