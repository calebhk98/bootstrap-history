"""The goods market's views: quotes, the year's book and the goods categories."""
from .rules import HOME_SELLER


class GoodsViews:

	# ---- quotes ----

	def goods_quote(self, material):
		"""The market's buy and sell terms for a tonne of a material, or None when it has no price."""
		return self.goods_market.quote(material)

	def material_trade_quote(self, material):
		return self.economy.trade_quote(material)

	def material_purchase_cost(self, material, tonnes):
		"""(money, mean money per tonne) to buy `tonnes`; None when the material has no price."""
		return self.economy.purchase_cost(material, tonnes)

	def purchase_quote(self, material, tonnes, already=0.0):
		"""(money, mean money per tonne) to buy `tonnes` of a material now, the price rising as the order is filled; None when
		it has no price."""
		return self.goods_market.quote_buy(material, tonnes, already)

	def can_be_bought(self, material):
		"""Whether anyone in reach sells the material at a price."""
		return self.goods_market.can_be_bought(material)

	def material_seller(self, material):
		"""Who sells a material to the home society: the home society's own id, a trading partner, or None when no one does."""
		return self.goods_market.offered_by(material)

	def partner_import(self, material):
		"""(the partner that sells a material, the tonnes it can still bring this year); (None, None) when the home society is
		its seller or no one is. The tonnes are None when the route has no figure."""
		market = self.goods_market
		seller = market.offered_by(material)
		if seller is None or seller == HOME_SELLER:
			return (None, None)
		return (seller, market.import_tonnes_available(material, seller))

	def home_unit_price(self, material):
		"""Money per unit the home society's sellers ask for a material (or a curated commodity, by the material it is priced as);
		None when no home seller offers it."""
		return self.goods_market.home_unit_price(material)

	def household_prices(self):
		"""{material: what a household pays per unit now}."""
		return self.goods_market.household_prices()

	def commodities_sold_by_acting_party(self):
		market = self.goods_market
		return self.economy.goods.commodities_sold_by(market.acting_party_id)

	def main_material_of(self, commodity):
		return self.economy.main_material_of(commodity)

	# ---- the market's actors ----

	def actor_supply(self, material):
		"""Tonnes of `material` that firms and governments sold into the market this year, summed over every actor; the
		acting seat's own sales are not included."""
		return self.goods_market.others_sold_tonnes(self.needs.material_commodity[material])

	def actor_demand(self, commodity):
		"""Tonnes of a commodity that governments bought on the market this year."""
		return self.goods_market.others_bought_tonnes(commodity)
