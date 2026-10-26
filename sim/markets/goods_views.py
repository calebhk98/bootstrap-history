"""The goods market's views: quotes, the year's book and the goods categories."""
from .rules import HOME_SELLER


class GoodsViews:

	# ---- quotes ----

	def goods_quote(self, material):
		"""The market's buy and sell terms for a tonne of a material, or None when it has no price."""
		return self._market().quote(material)

	def material_trade_quote(self, material):
		return self._economy().trade_quote(material)

	def material_purchase_cost(self, material, tonnes):
		"""(money, mean money per tonne) to buy `tonnes`; None when the material has no price."""
		return self._economy().purchase_cost(material, tonnes)

	def purchase_quote(self, material, tonnes, already=0.0):
		"""(money, mean money per tonne) to buy `tonnes` of a material now, the price rising as the order is filled; None when
		it has no price."""
		return self._market().quote_buy(material, tonnes, already)

	def can_be_bought(self, material):
		"""Whether anyone in reach sells the material at a price."""
		return self._market().can_be_bought(material)

	def material_seller(self, material):
		"""Who sells a material to the home society: the home society's own id, a trading partner, or None when no one does."""
		return self._market().offered_by(material)

	def partner_import(self, material):
		"""(the partner that sells a material, the tonnes it can still bring this year); (None, None) when the home society is
		its seller or no one is. The tonnes are None when the route has no figure."""
		market = self._market()
		seller = market.offered_by(material)
		if seller is None or seller == HOME_SELLER:
			return (None, None)
		return (seller, market.import_tonnes_available(material, seller))

	def home_unit_price(self, material):
		"""Money per unit the home society's sellers ask for a material (or a curated commodity, by the material it is priced as);
		None when no home seller offers it."""
		return self._market().home_unit_price(material)

	def household_prices(self):
		"""{material: what a household pays per unit now}."""
		return self._market().household_prices()

	def commodities_sold_by_acting_party(self):
		market = self._market()
		return self._economy().goods.commodities_sold_by(market.acting_party_id)

	def main_material_of(self, commodity):
		return self._economy().main_material_of(commodity)

	# ---- the year's book ----

	def market_state(self, commodity):
		return self._game().market_state(commodity)

	def market_floor_ratio(self, commodity):
		"""The lowest price over the incumbents' cost their producers sell a commodity at."""
		return self._game()._floor_ratio(commodity)

	def opening_population(self):
		return self._game()._opening_population()

	def new_goods_units(self):
		"""{material: units a year households want} of goods offered now that the opening did not offer."""
		return self._game().household_new_goods_units()

	# ---- the goods categories ----

	def goods_category_factor(self, category):
		return self._game().goods_category_factor(category)

	def goods_category_factor_with_entrants(self, category, entrants):
		return self._game().goods_category_factor_with_entrants(category, entrants)

	def goods_category_price_ratio(self, category):
		return self._game().goods_category_price_ratio(category)

	def goods_category_state(self, category):
		return self._game()._goods_category_state(category)

	def nodes_in_category(self, category):
		return self._game()._nodes_in_cat(category)

	# ---- the market's actors ----

	def actor_supply(self, material):
		"""Tonnes of `material` that firms and governments sold into the market this year, summed over every actor; the
		acting seat's own sales are not included."""
		return self._market().others_sold_tonnes(self.needs.material_commodity[material])

	def actor_demand(self, commodity):
		"""Tonnes of a commodity that governments bought on the market this year."""
		return self._market().others_bought_tonnes(commodity)
