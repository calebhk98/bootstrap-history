"""Real output: the quantity of goods the society's market sells, valued at fixed opening prices.

No technology count and no index stand in for it. The opening basket is what households bought at
the prices the society's own starting techniques solve to (units a year of each material, and
those prices in labour hours). Each commodity's market then says how much of it changes hands this
year relative to the opening (`traded_tonnes` over `reference_tonnes` in the market book, which
clear supply against household demand). Real output is

    sum over materials of (opening units * the commodity's traded ratio) * opening price in hours

A technique raises it only by lowering the price of a good its production entries make, which
raises what households buy of it (market_demand.py) and what the market clears.

A good households were not offered at the opening has no opening price. Once it is offered and the
market sells it, it counts at the price it was first offered at (`economy.introduction_prices`), in the
quantity households want of it times the share of that demand the market cleared.

TEMPORARY HEURISTIC (CLAUDE.md 4.4): a new good counts at its introduction price, standing for a chained
basket (re-based each year, quantity index linked), which would also credit what it saves.
"""
from sim.engine import market_demand


def opening_prices_in_hours(held, civ, opening_farmed_hectares):
    """{material: opening price in labour hours} the basket is valued at: the solved prices at the
    opening's banded farmed area, less goods with no calculated price or only a mature-market one."""
    from .data import calculated_goods_table
    from .prices import band_farmed_hectares
    in_hours, basis = calculated_goods_table(
        held, civilization_id=civ.get("id"), civilization=civ,
        farmed_hectares=band_farmed_hectares(opening_farmed_hectares))
    return {material: price for material, price in sorted(in_hours.items())
            if price > 0.0 and basis.get(material) != "mature"}


class RealOutputMixin:

    def base_basket(self):
        """{"prices": {material: opening price in labour hours}, "units": {material: units a year
        households bought at the opening}, "commodity": {material: its commodity}}. A function of
        the society's starting techniques and the civilisation only, so kept for the run."""
        cached = getattr(self.household, "_base_basket_cache", None)
        if cached is not None:
            return cached
        prices = opening_prices_in_hours(
            frozenset(self.state.projects.granted), self.civ, self._opening_farmed_hectares)
        units = market_demand.household_demand_by_material(
            prices, self._opening_population(), market_demand.MEAN_INCOME_HOURS_PER_CAPITA,
            self.civ, self.world_map)
        units = {material: wanted for material, wanted in sorted(units.items())
                 if wanted > 0.0 and material in prices}
        basket = {"prices": prices, "units": units,
                  "commodity": {material: self._material_tag(material)[0] for material in units}}
        self.household._base_basket_cache = basket
        return basket

    def traded_ratio(self, commodity):
        """Tonnes the market cleared of a commodity last year over the opening's; None where
        nothing produces it."""
        entry = self._market_entry(commodity)
        if entry is None or not entry["reference_tonnes"] > 0.0:
            return None
        return entry.get("traded_tonnes", entry["reference_tonnes"]) / entry["reference_tonnes"]

    def real_output_lines(self):
        """[(material, units a year sold now, opening price in labour hours)] for every good in the
        opening basket whose commodity has a market."""
        basket = self.base_basket()
        ratios = {}
        lines = []
        for material, units in basket["units"].items():
            commodity = basket["commodity"][material]
            if commodity not in ratios:
                ratios[commodity] = self.traded_ratio(commodity)
            if ratios[commodity] is not None:
                lines.append((material, units * ratios[commodity], basket["prices"][material]))
        introduced = self.state.economy.introduction_prices
        for material, units in self.household_new_goods_units().items():
            entry = self._market_entry(self._material_tag(material)[0])
            if entry is not None and material in introduced:
                lines.append((material, units * entry.get("cleared_share", 1.0), introduced[material]))
        return lines

    def real_output_hours(self):
        """Quantities sold this year at the opening prices, in labour hours."""
        return sum(quantity * price for _material, quantity, price in self.real_output_lines())

    def opening_output_hours(self):
        """The same sum at the opening's own quantities."""
        basket = self.base_basket()
        return sum(units * basket["prices"][material] for material, units in basket["units"].items()
                   if self.traded_ratio(basket["commodity"][material]) is not None)

    def real_output_per_head(self):
        """Real output per person over the opening's, as last year's market closed it; one at the opening."""
        return self.state.economy.output_per_head

    def _close_real_output(self):
        """Measure the year's real output per head once the market has closed."""
        per_hour = self.labour.money_per_labour_hour()
        prices = self.goods_market.household_prices()
        for material in self.household_new_goods_units():
            self.state.economy.introduction_prices.setdefault(material, prices[material] / per_hour)
        opening = self.opening_output_hours()
        people = float(self.population.total) / self._opening_population()
        if opening > 0.0 and people > 0.0:
            self.state.economy.output_per_head = self.real_output_hours() / opening / people
