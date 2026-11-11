"""The port's reads of prices and materials, money, production and the farm, each from the view its owner publishes.

`PortWorld.scenario`, `.materials`, `.finance`, `.production` and `.farm` hold them, as `.state`, `.labour`, `.map` and `.foreign` hold theirs."""
from sim.diffusion.api import NoteFirstRuns
from sim.ledger.api import pool_rules as ledger_pool_rules
from sim.prices.api import rules as price_rules


class ScenarioReads:
	"""The scenario and the seats: the year, the civilisation, the configuration, the tree, the price level, the people and who acts."""

	def __init__(self, needs):
		self._needs = needs

	@property
	def year(self):
		return self._needs.year()

	@property
	def civ(self):
		return self._needs.civilisation()

	@property
	def held_civ(self):
		"""The civilisation's record with the tiles the country holds now as its home tiles (what the opening record lists
		are the tiles it opened with)."""
		return {**self._needs.civilisation(), "home_tiles": list(self._needs.home_tiles_held())}

	@property
	def cfg(self):
		return self._needs.game_config()

	@property
	def price_index(self):
		return self._needs.price_index()

	@property
	def output_factor(self):
		return self._needs.output_factor()

	@property
	def population(self):
		return self._needs.population()

	@property
	def HOURS_PER_PERSON_YEAR(self):
		return self._needs.hours_per_person_year()

	@property
	def actors(self):
		return self._needs.cast()

	def act_as(self, seat_id):
		return self._needs.act_as(seat_id)

	def acting_country(self):
		return self._needs.acting_country()


class MaterialReads:
	"""The material price tables and the commodity groupings."""

	def __init__(self, needs):
		self._needs = needs

	def prices(self):
		"""Every priced material's money price per unit of the material (a read-only table)."""
		return self._needs.material_prices()

	def price_per_unit(self, tag):
		"""Money price of one unit of the material, from the cost table."""
		return self._needs.material_price[tag]

	def priced_key(self, tag, prices):
		return price_rules.priced_key(tag, prices, self._needs.commodity_record[tag])

	def sold_material(self, tag):
		"""The material a held tonne of `tag`'s pool sells as (the form its mines raise)."""
		return price_rules.sold_material(tag, self._needs.commodity_record[self._needs.material_pool[tag][0]])

	def stock_form(self, material):
		"""The key a held tonne of `material` is kept under in the ledger: the material itself where its pool names it as a
		form, else the pool's id."""
		commodity = self._needs.material_pool[material][0]
		return ledger_pool_rules.form_key(material, commodity, {commodity: self._needs.commodity_record[commodity]})

	def spoilage_rates(self):
		"""{good: continuous decay rate a year} of the goods that spoil, with the installed mods applied."""
		return self._needs.spoilage_rates()

	def service_life_years(self):
		"""{good: years a stock of it serves} of the goods that wear out, with the installed mods applied."""
		return self._needs.service_life_years()

	def commodity_map(self):
		return self._needs.material_commodity_map()

	def tag(self, material):
		"""The market a material trades in, as (commodity, ...): several material keys can share one."""
		return self._needs.material_pool[material]

	def market_tonnes(self, commodity):
		return self._needs.material_market_tonnes[commodity]

	def stock_t(self, commodity):
		return self._needs.goods_pool_stock[commodity]

	def serves_a_need(self, material):
		return self._needs.material_serves_a_need[material]


class PortFinanceReads:
	"""The state's money, the credit market, the coin and the purse."""

	def __init__(self, needs):
		self._needs = needs

	def state_treasury(self):
		return self._needs.state_treasury()

	def state_reach(self):
		return self._needs.state_reach()

	def market_rate(self):
		return self._needs.market_rate()

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
