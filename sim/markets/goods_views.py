"""The goods market's views: quotes, the year's book and the goods categories."""
from sim.assembly.api import Part

from sim.world.demand import production_data

from . import trade_duty, unit_mass


class GoodsViews(Part):

	# ---- quotes ----

	def goods_quote(self, material):
		"""The market's buy and sell terms for a tonne of a material, or None when it has no price."""
		return self.parts.market_objects.goods_market.quote(material)

	def sale_limits(self, material):
		"""(tonnes the acting seat holds, tonnes the market takes now) of a material."""
		return self.parts.market_objects.goods_market.sale_limits(material)

	def purchase_quote(self, material, tonnes, already=0.0):
		"""(money, mean money per tonne) to buy `tonnes` of a material now, the price rising as the order is filled; None when
		it has no price."""
		return self.parts.market_objects.goods_market.pricing.quote_buy(material, tonnes, already)

	def sale_quote(self, material, tonnes):
		"""(stock key, tonnes the market takes now, money for them) if the acting seat sold `tonnes` of a material; the figure
		a sale pays. (None, 0.0, 0.0) when the market has no price or takes none."""
		return self.parts.market_objects.goods_market.quote_sell(material, tonnes)

	def can_be_bought(self, material):
		"""Whether anyone in reach sells the material at a price."""
		return self.parts.market_objects.goods_market.offers.can_be_bought(material)

	def material_seller(self, material):
		"""Who sells a material to the home society: the home society's own id, a trading partner, or None when no one does."""
		return self.parts.market_objects.goods_market.offers.offered_by(material)

	def home_unit_price(self, material):
		"""Money per unit the home society's sellers ask for a material (or a curated commodity, by the material it is priced as);
		None when no home seller offers it."""
		return self.parts.market_objects.goods_market.offers.home_unit_price(material)

	def household_prices(self):
		"""{material: what a household pays per unit now}."""
		return self.parts.market_objects.goods_market.offers.household_prices()

	def commodities_sold_by_acting_party(self):
		return self.parts.market_objects.goods_market.commodities_sold_by(self.parts.market_objects.goods_market.acting_party_id)

	def seat_goods_orders(self):
		"""The acting seat's goods orders waiting for the year's clearing: [{"side", "material", "stock_key", "tonnes",
		"limit_per_tonne", "carriage_per_tonne", "cost_factor", "project"}]."""
		return self.parts.market_objects.goods_market.seat_orders()

	def seat_goods_traded(self):
		"""What the last clearing bought and sold for the acting seat: {"bought": {stock key: tonnes}, "sold": {stock key: tonnes},
		"orders": [one result per order, with its project and, when the order was not posted, its refusal's cause]}."""
		return self.parts.market_objects.goods_market.seat_trades()

	def others_trade_stamp(self):
		"""What every seat but the acting one has ordered to buy and sell this year, comparable for equality, for caches whose
		answers read the posted price."""
		return self.parts.market_objects.goods_market.others_stamp()

	def main_material_of(self, commodity):
		return self.parts.market_objects.economy.main_material_of(commodity)

	# ---- facts the economy and the border settle ----

	def unit_mass_kg(self, material):
		"""Kilograms in one unit of a material, as the freight model reads it."""
		return unit_mass.unit_mass_kg(material, production_data(self.needs.mods_directory()))

	def border_duty_per_tonne(self, source, destination, price_per_tonne):
		"""Money the destination country's state charges on a tonne bought at `price_per_tonne` in `source`; infinite on an embargo."""
		return trade_duty.duty_per_tonne(self.parts.market_objects.reads, source, destination, price_per_tonne)
