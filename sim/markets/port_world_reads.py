"""The port's reads of prices and materials, money, production and the farm, each from the view its owner publishes.

`PortWorld.materials`, `.finance`, `.production` and `.farm` hold them, as `.state`, `.labour`, `.map` and `.foreign` hold theirs."""
from sim.diffusion.api import NoteFirstRuns
from sim.prices.api import rules as price_rules


class MaterialReads:
	"""The material price tables and the commodity groupings."""

	def __init__(self, needs):
		self._needs = needs

	def prices(self):
		"""Every priced material's money price per unit of the material (a read-only table)."""
		return self._needs.material_prices()

	def price_per_kg(self, tag):
		return self._needs.material_price[tag]

	def priced_key(self, tag, prices):
		return price_rules.priced_key(tag, prices, self._needs.commodity_record[tag])

	def commodity_map(self):
		return self._needs.material_commodity_map()

	def tag(self, material):
		"""The market a material trades in, as (commodity, ...): several material keys can share one."""
		return self._needs.material_pool[material]

	def market_tonnes(self, commodity):
		return self._needs.material_market_tonnes[commodity]

	def commodity_materials(self, commodity):
		return self._needs.commodity_materials[commodity]

	def stock_t(self, commodity):
		return self._needs.goods_stock[commodity]

	def not_traded(self):
		return self._needs.not_traded_materials()

	def serves_a_need(self, material):
		return self._needs.material_serves_a_need[material]


class FinanceReads:
	"""The state's money, the credit market, the coin and the purse."""

	def __init__(self, needs):
		self._needs = needs

	def state_treasury(self):
		return self._needs.state_treasury()

	def state_reach(self):
		return self._needs.state_reach()

	def market_rate(self):
		return self._needs.market_rate()

	def credit_room(self, actor_id):
		return self._needs.credit_room(actor_id)

	def credit_line_sought(self):
		return self._needs.credit_line_sought(None, None, None)

	def debt_bondage_term_years(self):
		return self._needs.debt_bondage_term_years()

	def coin_stock_units(self):
		return self._needs.home_coin_stock()

	def real_output_hours(self, measure=None):
		return self._needs.real_output_hours(measure)

	def can_pay(self, money):
		return self._needs.can_pay(money)

	def spending_power(self, kind="buy"):
		return self._needs.spending_power(kind)


class ProductionReads:
	"""The techniques, the concerns' books and the tree's projects."""

	def __init__(self, needs):
		self._needs = needs

	def techniques_held(self):
		return self._needs.techniques_held()

	def operating(self):
		return self._needs.operating()

	def techniques_granted(self):
		return self._needs.techniques_granted()

	def techniques_in_use(self):
		return self._needs.techniques_in_use()

	def techniques_spread(self):
		"""The techniques in use that concerns in the same line of business have had time to copy; the techniques in use
		are noted first, so each is stamped with the year it was first seen."""
		self._needs.send(NoteFirstRuns(self.techniques_in_use()))
		return self._needs.techniques_spread()

	def held_and_running(self, include_starting=True):
		return self._needs.held_techniques(include_starting)

	def concern_book_offer(self, node_id):
		return self._needs.concern_book_offer[node_id]

	def concern_book_inputs_cost(self, node_id):
		return self._needs.concern_book_inputs_cost[node_id]

	def concern_takings(self, node_id, ramp):
		return self._needs.concern_takings(node_id, ramp)

	def node_output_market_factor(self, node):
		return self._needs.node_output_market_factor(node)

	def project_cost(self, node_id):
		return self._needs.project_cost(node_id)

	def nodes_with_mechanic(self, name):
		return tuple(self._needs.mechanic[name])

	def literacy(self, field, country=None):
		return self._needs.country_literacy_figure(country, field)


class FarmReads:
	"""The land and the farm: sites, weather, ownership and timber."""

	def __init__(self, needs):
		self._needs = needs

	def sites(self):
		return self._needs.farm_sites()

	def weather_by_tile(self, year):
		return self._needs.farm_weather[year]

	def pooled_weather_multiplier(self, year, weather_stdev_fraction=None, harmed=True):
		return self._needs.harvest_weather(year, weather_stdev_fraction, harmed)

	def externality_yield_factors(self, year):
		return self._needs.externality_yield_factors(year)

	def tile_owner_map(self):
		return self._needs.tile_owner_map()

	def tiles_owned_by(self, actor_id):
		return self._needs.tiles_owned_by[actor_id]

	def timber_felled(self):
		return self._needs.timber_felled()
