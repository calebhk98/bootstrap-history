"""Real output: the quantity of goods the economy sells, valued at fixed opening prices.

No technology count and no index stand in for it. The opening basket is the economy's own: the quantity of each
good households bought when it opened (`economy.api.opening_quantities`), valued at the economy's opening prices in
hours of the unskilled trade's opening wage. The economy's volumes (`economy.api.traded_volumes`) do not start at
those quantities, so they are measured against the first year each good cleared any, recorded in
`stored["volume_baseline"]`, and a single scale carries that year onto the opening basket's value. With the traded
units of a good, its baseline, its opening price and the scale,

    real output = scale * sum over goods of (traded units * opening price in hours)

and it equals the opening basket's value in the baseline year, whatever the economy traded then. A good's weight is
what the economy actually trades of it, so a good it barely trades cannot swing the total. A technique raises output
only by lowering the cost of a good, which raises what the economy's households buy and its markets clear.
Population does not enter: a smaller society trades less and has fewer heads.

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

    def traded_measure(self):
        """({good: units the economy traded last year}, scale) over the opening basket's goods that have a baseline;
        the scale carries the baseline year onto the opening basket's value, so real output starts at it."""
        basket = self.base_basket()
        baseline = self.economy.agent_volume_baseline() or {}
        volumes = self.economy.agent_traded_volumes() or {}
        if not baseline:        # no year has closed: the economy has traded nothing yet, and the opening basket stands
            return dict(basket["units"]), 1.0
        goods = [good for good in basket["units"] if baseline.get(good, 0.0) > 0.0]
        then = sum(baseline[good] * basket["prices"][good] for good in goods)
        opening = sum(basket["units"][good] * basket["prices"][good] for good in goods)
        return {good: volumes.get(good, 0.0) for good in goods}, (opening / then if then > 0.0 else 0.0)

    def real_output_lines(self, measure=None):
        """[(material, units a year sold now, opening price in labour hours)] for every good in the opening basket the
        economy has traded. `measure` is `traded_measure()`, which a caller shares between its reads within one moment."""
        basket = self.base_basket()
        traded, scale = self.traded_measure() if measure is None else measure
        lines = [(good, units * scale, basket["prices"][good]) for good, units in traded.items()]
        introduced = self.state.economy.introduction_prices
        volumes = self.economy.agent_traded_volumes() or {}
        for material in self.household_new_goods_units():
            if material in introduced and volumes.get(material, 0.0) > 0.0:
                lines.append((material, volumes[material], introduced[material]))
        return lines

    def real_output_hours(self, measure=None):
        """Quantities sold this year at the opening prices, in labour hours."""
        return sum(quantity * price for _material, quantity, price in self.real_output_lines(measure))

    def opening_output_hours(self, measure=None):
        """The opening basket's value over the goods the measure holds."""
        basket = self.base_basket()
        traded, _scale = self.traded_measure() if measure is None else measure
        return sum(basket["units"][good] * basket["prices"][good] for good in traded)

    def real_output_per_head(self):
        """Real output per person over the opening's, as last year's market closed it; one at the baseline."""
        return self.state.economy.output_per_head

    def _close_real_output(self):
        """Measure the year's real output per head once the market has closed."""
        per_hour = self.labour.money_per_labour_hour()
        prices = self.goods_market.household_prices()
        for material in self.household_new_goods_units():
            self.state.economy.introduction_prices.setdefault(material, prices[material] / per_hour)
        measure = self.traded_measure()
        opening = self.opening_output_hours(measure)
        people = float(self.population.total) / self._opening_population()
        if opening > 0.0 and people > 0.0:
            self.state.economy.output_per_head = self.real_output_hours(measure) / opening / people
