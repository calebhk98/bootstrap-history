"""Real output: the quantity of goods the economy sells, valued at fixed opening prices.

No technology count and no index stand in for it. The opening basket is the economy's own: the quantity of each
good households bought when it opened (`economy.api.opening_quantities`), valued at the economy's opening prices in
hours of the unskilled trade's opening wage. Each good's volume then moves with what the economy trades of it
(`economy.api.traded_volumes`) against the first year it traded any, recorded in `stored["volume_baseline"]`, so the
ratio is one at the baseline by construction. Real output is

    sum over goods of (opening quantity * the good's traded volume over its baseline) * opening price in hours

A technique raises it only by lowering the cost of a good, which raises what the economy's households buy and its
markets clear. Population does not enter: a smaller society trades less and has fewer heads.

A good the opening basket did not hold but households want once a technique offers it has no opening price. Once the
economy trades it, it counts at the price it was first offered at (`economy.introduction_prices`), in the units the
economy trades of it.

TEMPORARY HEURISTIC (CLAUDE.md 4.4): a new good counts at its introduction price, standing for a chained basket
(re-based each year, quantity index linked), which would also credit what it saves.
"""


class RealOutputMixin:

    def base_basket(self):
        """{"prices": {good: opening price in labour hours}, "units": {good: units a year households bought at the
        opening}}: the agent economy's own opening basket. Empty while the economy opens."""
        cached = getattr(self.household, "_base_basket_cache", None)
        if cached is not None:
            return cached
        opened = self.economy.agent_opening_basket()
        if opened is None:
            return {"prices": {}, "units": {}}
        units, prices = opened
        units = {good: wanted for good, wanted in sorted(units.items()) if wanted > 0.0 and prices.get(good, 0.0) > 0.0}
        basket = {"prices": prices, "units": units}
        self.household._base_basket_cache = basket
        return basket

    def volume_ratios(self):
        """{good: units the economy traded last year over its first year's}, for the goods whose baseline is set."""
        return self.economy.agent_cleared_ratios() or {}

    def real_output_lines(self, ratios=None):
        """[(material, units a year sold now, opening price in labour hours)] for every good in the opening basket the
        economy has traded. `ratios` is a {good: volume ratio} the caller shares between its reads within one moment."""
        basket = self.base_basket()
        ratios = self.volume_ratios() if ratios is None else ratios
        lines = [(material, units * ratios[material], basket["prices"][material])
                 for material, units in basket["units"].items() if material in ratios]
        introduced = self.state.economy.introduction_prices
        volumes = self.economy.agent_traded_volumes() or {}
        for material in self.household_new_goods_units():
            if material in introduced and volumes.get(material, 0.0) > 0.0:
                lines.append((material, volumes[material], introduced[material]))
        return lines

    def real_output_hours(self, ratios=None):
        """Quantities sold this year at the opening prices, in labour hours."""
        return sum(quantity * price for _material, quantity, price in self.real_output_lines(ratios))

    def opening_output_hours(self, ratios=None):
        """The same sum at the opening's own quantities, over the goods that have a ratio."""
        basket = self.base_basket()
        ratios = self.volume_ratios() if ratios is None else ratios
        return sum(units * basket["prices"][material]
                   for material, units in basket["units"].items() if material in ratios)

    def real_output_per_head(self):
        """Real output per person over the opening's, as last year's market closed it; one at the baseline."""
        return self.state.economy.output_per_head

    def _close_real_output(self):
        """Measure the year's real output per head once the market has closed."""
        per_hour = self.labour.money_per_labour_hour()
        prices = self.goods_market.household_prices()
        for material in self.household_new_goods_units():
            self.state.economy.introduction_prices.setdefault(material, prices[material] / per_hour)
        ratios = self.volume_ratios()
        opening = self.opening_output_hours(ratios)
        people = float(self.population.total) / self._opening_population()
        if opening > 0.0 and people > 0.0:
            self.state.economy.output_per_head = self.real_output_hours(ratios) / opening / people
