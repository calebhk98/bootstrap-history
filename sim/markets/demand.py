"""How much more or less households want of each commodity than at the opening.

Households are priced only for goods something offers (`GoodsMarket.household_prices`): a good nothing offers has no price,
so the need it served draws no spending on it.

The household demand model (sim/world/need_demand.py, household_views.py) turns population
and income into units wanted per year, through needs, goods and the recipes that make them. Its absolute quantities do not
match the resource tables (it omits many uses), so the market uses only its change: demand now over demand at the opening,
at the same prices. The society's capacity at the opening is what built up to meet the opening demand, so that ratio is what
moves the year's price. A commodity the model never reaches follows the whole economy's size instead.
"""
from . import constants, new_goods
from .demand_key import demand_key, population_of_key
from .rules import HOME_SELLER


class Demand:

	def opening_population(self):
		return float(self.needs.civilisation().get("population", self.needs.default_population()))

	def household_income_hours_per_capita(self):
		"""Labour hours a person earns a year: the opening's income, carried by what an hour of the unskilled trade pays now
		against the opening (the labour market's scarcity of hands and the share of output gain it passes on). Prices here
		are the solver's own, so cost of living and the price level are left out of the wage. Returns to land and capital are
		not yet in it."""
		# TEMPORARY HEURISTIC: every household earns the mean; the spread and the returns are not modelled.
		return constants.MEAN_INCOME_HOURS_PER_CAPITA * self.needs.labour_market().household_wage_ratio()

	def household_real_income_ratio(self):
		"""What a person's income buys of the opening basket now over what it bought at the opening: income in hours over
		the opening's, over the basket's cost at today's prices against its cost then."""
		basket = self.static_book_basket()
		prices = self.goods_market.household_cost_prices()
		per_hour = self.needs.money_per_labour_hour()
		opening_cost = now_cost = 0.0
		for material, units in basket["units"].items():
			if prices.get(material, 0.0) > 0.0:
				opening_cost += units * basket["prices"][material]
				now_cost += units * prices[material] / per_hour
		if opening_cost <= 0.0 or now_cost <= 0.0:
			return 1.0
		return self.household_income_hours_per_capita() / constants.MEAN_INCOME_HOURS_PER_CAPITA * opening_cost / now_cost

	def household_demand_ratios(self):
		"""{commodity: demand now over demand at the opening}, from population, income and today's prices against the opening
		basket; recomputed when the population or the wage moves by a tenth of a percent or the price table changes."""
		return self.household_demand_now()[0]

	def new_goods_units(self):
		"""{material: units a year households want} of goods offered now that the opening did not offer."""
		return self.household_demand_now()[1]

	def household_demand_now(self):
		market_api = self.goods_market
		prices = market_api.household_cost_prices()
		opening_population = self.opening_population()
		key = demand_key(self.needs.population_total(), opening_population, self.household_income_hours_per_capita())
		cache = self._seat_cache("household_demand")
		if cache is not None and cache[0] == key and cache[1] is prices:
			return cache[2], cache[3]
		# computed from the rounded key, so the answer depends on the key and not on when it was last computed
		basket = self.static_book_basket()
		per_hour = self.needs.money_per_labour_hour()
		# the opening's goods and any the home society now makes, so a need a new good serves can turn to it; a good only a
		# partner offers is not the home market's
		prices_in_hours = new_goods.prices_in_hours(
			prices, per_hour, basket["prices"],
			{material: market_api.offered_by(material) == HOME_SELLER
			 for material, price in prices.items() if price > 0.0 and material not in basket["prices"]})
		now = self.household_demand_units(prices_in_hours, population_of_key(key, opening_population), key[1])
		opening_by_commodity, now_by_commodity = {}, {}
		for material, units in basket["units"].items():
			commodity = basket["commodity"][material]
			opening_by_commodity[commodity] = opening_by_commodity.get(commodity, 0.0) + units
			now_by_commodity[commodity] = now_by_commodity.get(commodity, 0.0) + now.get(material, 0.0)
		ratios = {commodity: now_by_commodity[commodity] / total
		          for commodity, total in sorted(opening_by_commodity.items()) if total > 0.0}
		new_units = new_goods.new_goods_units(now, basket["units"], prices_in_hours)
		self._set_seat_cache("household_demand", (key, prices, ratios, new_units))
		return ratios, new_units

	def economy_size_ratio(self):
		"""Population over the opening's: what demand follows for a commodity the household model does not reach."""
		# TEMPORARY HEURISTIC: unreached commodities scale one-for-one with population.
		return float(self.needs.population_total()) / self.opening_population()

	def household_demand_ratio(self, commodity):
		ratios = self.household_demand_ratios()
		if commodity in ratios:
			return ratios[commodity]
		return self.economy_size_ratio()

	def static_book_basket(self):
		"""{"prices": {material: opening price in labour hours}, "units": {material: units a year households bought at the
		opening}, "commodity": {material: its commodity}}. A function of the starting techniques and the civilisation only,
		so kept for the run."""
		cached = self._seat_cache("static_book_basket")
		if cached is not None:
			return cached
		in_hours = self.needs.calculated_goods_prices(frozenset(self.needs.techniques_granted()), self.needs.opening_farmed_hectares())
		prices = {material: price for material, price in sorted(in_hours.items()) if price > 0.0}
		units = self.household_demand_units(prices, self.opening_population(), constants.MEAN_INCOME_HOURS_PER_CAPITA)
		units = {material: wanted for material, wanted in sorted(units.items()) if wanted > 0.0 and material in prices}
		basket = {"prices": prices, "units": units,
		          "commodity": {material: self.needs.material_pool[material][0] for material in units}}
		self._set_seat_cache("static_book_basket", basket)
		return basket
