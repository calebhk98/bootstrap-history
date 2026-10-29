"""The goods market's views: quotes, the year's book and the goods categories."""
from . import categories, goods_imports, trade_duty


class GoodsViews:

	# ---- quotes ----

	def goods_quote(self, material):
		"""The market's buy and sell terms for a tonne of a material, or None when it has no price."""
		return self.goods_market.quote(material)

	def goods_categories(self):
		"""The goods categories: concerns in one share a market."""
		return categories.GOODS_CATEGORIES

	def sale_limits(self, material):
		"""(tonnes the acting seat holds, tonnes the market takes now) of a material."""
		return self.goods_market.sale_limits(material)

	def material_trade_quote(self, material):
		return self.economy.trade_quote(material)

	def material_purchase_cost(self, material, tonnes):
		"""(money, mean money per tonne) to buy `tonnes`; None when the material has no price."""
		return self.economy.purchase_cost(material, tonnes)

	def purchase_quote(self, material, tonnes, already=0.0):
		"""(money, mean money per tonne) to buy `tonnes` of a material now, the price rising as the order is filled; None when
		it has no price."""
		return self.goods_market.quote_buy(material, tonnes, already)

	def sale_quote(self, material, tonnes):
		"""(stock key, tonnes the market takes now, money for them) if the acting seat sold `tonnes` of a material; the figure
		a sale pays. (None, 0.0, 0.0) when the market has no price or takes none."""
		return self.goods_market.quote_sell(material, tonnes)

	def can_be_bought(self, material):
		"""Whether anyone in reach sells the material at a price."""
		return self.goods_market.can_be_bought(material)

	def material_seller(self, material):
		"""Who sells a material to the home society: the home society's own id, a trading partner, or None when no one does."""
		return self.goods_market.offered_by(material)

	def partner_import_tonnes(self, material):
		"""Tonnes a year a trading partner can still bring of a material; zero when the home society is its seller, no one is, or the
		route has no figure."""
		return goods_imports.import_tonnes_to_home(self.goods_market.import_tonnes_available(material))

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

	def others_trade_stamp(self):
		"""What every party but the acting seat has sold and bought this year, comparable for equality, for caches whose
		answers read the posted price."""
		return self.goods_market.others_stamp()

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

	# ---- facts the economy and the border settle ----

	def unit_mass_kg(self, material):
		"""Kilograms in one unit of a material, as the freight model reads it."""
		from .port_setup import unit_mass_kg
		return unit_mass_kg(material)

	def border_duty_per_tonne(self, source, destination, price_per_tonne):
		"""Money the destination country's state charges on a tonne bought at `price_per_tonne` in `source`; infinite on an embargo."""
		return trade_duty.duty_per_tonne(self.reads, source, destination, price_per_tonne)
