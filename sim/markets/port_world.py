"""What the goods market and the port over the agent economy read of the game: one member per view the markets module declares.

`GoodsMarket` and `EconomyPort` ask this object where they used to ask the engine's `Sim`. Every member is a view of another
owner (or a send of its command), or one of the markets module's own methods; the raw state objects (the saved state's
sections, the seats' registry) are `legacy_*` views, debts that go when that state moves. Members about the foreign
partners and the freight, coin and resources owners are in port_world_foreign.py."""
from types import SimpleNamespace

from sim.diffusion.api import NoteFirstRuns
from sim.freight.api import FREIGHT_DRIVER_WAGE_TRADE, FREIGHT_FEED_PRICE_MATERIAL
from sim.prices.api import rules as price_rules

from . import trade_duty
from .port_world_foreign import ForeignReads
from .port_world_map import MapReads


class StateReads:
	"""The sections of the saved state the port reads, each from the view that publishes it."""

	def __init__(self, needs, owner):
		self._needs = needs
		self._owner = owner

	@property
	def seats(self):
		return self._needs.seat_list()["joined"]

	@property
	def economy(self):
		return SimpleNamespace(improvements=self._needs.built_ways())

	@property
	def actors(self):
		return self._needs.cast_state()

	@property
	def acting_seat(self):
		return self._owner.clock.acting_seat


class LabourReads:
	"""The workforce views the port reads, under the names `Labour` had."""

	def __init__(self, needs):
		self._needs = needs

	def base_tile(self):
		return self._needs.base_tile()

	def money_per_labour_hour(self):
		return self._needs.money_per_labour_hour()

	def wage_per_hour(self, trade):
		return self._needs.wage[trade]

	def farming_technique(self):
		return self._needs.farming_technique()

	@property
	def market(self):
		return self._needs.labour_market()

	def need_shares(self):
		return self._needs.labour_need_shares()

	def settlement_tiles(self):
		return self._needs.settlement_tiles()


class PortWorld(MapReads, ForeignReads):

	FREIGHT_DRIVER_WAGE_TRADE = FREIGHT_DRIVER_WAGE_TRADE
	FREIGHT_FEED_PRICE_MATERIAL = FREIGHT_FEED_PRICE_MATERIAL

	def __init__(self, needs, owner):
		self._needs = needs
		self._owner = owner          # the markets module: its own views are asked of it directly
		self.state = StateReads(needs, owner)
		self.labour = LabourReads(needs)

	def send(self, command):
		return self._needs.send(command)

	def bound_kernels(self):
		"""The module's kernels as the assembly bound them: a mod's replacement, else the reference."""
		return dict(self._owner.kernels)

	# ---- the module's own objects and records ----

	@property
	def economy(self):
		return self._owner.economy

	@property
	def goods_market(self):
		return self._owner.goods_market

	def agent_record(self):
		"""The agent economy's saved record."""
		return self._owner.world.agent_economy

	def money_from_economy(self):
		return self._owner.world.money_from_economy

	def _market_flows(self):
		return self._owner.legacy_market_flows()

	def _market_entry(self, commodity):
		return self._owner.market_entry(commodity)

	def market_state(self, material):
		return self._owner.market_state(material)

	def remembered(self, name):
		"""What the acting seat's goods market worked out and kept under `name`, or None."""
		return self._owner._seat_cache(name)

	def remember(self, name, value):
		self._owner._set_seat_cache(name, value)

	# ---- the scenario ----

	@property
	def year(self):
		return self._needs.year()

	@property
	def civ(self):
		return self._needs.civilisation()

	def civilisation_record(self, civilization_id):
		"""A civilisation as its file gives it (mods applied, checked)."""
		return self._needs.civilisation_record[civilization_id]

	def border_terms(self, destination, source):
		"""(tariff share, embargoed) `destination`'s state holds toward goods crossing from `source`."""
		return trade_duty.terms_in_book(self._needs.store_book(), destination, source)

	@property
	def cfg(self):
		return self._needs.game_config()

	@property
	def nodes(self):
		return self._needs.tree_nodes()

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

	# ---- the seats ----

	def act_as(self, seat_id):
		return self._needs.act_as(seat_id)

	def acting_country(self):
		return self._needs.acting_country()

	def playing_seats(self):
		return self._needs.seat_list()["playing"]

	def edge(self, name):
		return self._needs.cast_state().edge(name)

	# ---- the money and the state ----

	def state_treasury(self):
		return self._needs.state_treasury()

	def state_reach(self):
		return self._needs.state_reach()

	def market_rate(self):
		return self._needs.market_rate()

	def market_credit_room(self, actor_id):
		return self._needs.credit_room(actor_id)

	def credit_line_sought(self):
		return self._needs.credit_line_sought(None, None, None)

	def debt_bondage_term_years(self):
		return self._needs.debt_bondage_term_years()

	def home_coin_stock_units(self):
		return self._needs.home_coin_stock()

	def real_output_hours(self, measure=None):
		return self._needs.real_output_hours(measure)

	def actor_world(self):
		return self._needs.actor_world()

	# ---- the prices and materials ----

	def _material_prices(self):
		return self._needs.material_prices()

	def _price_tables(self):
		return self._needs.price_tables()

	def _material_price_per_kg(self, tag):
		return self._needs.material_price[tag]

	def _priced_key(self, tag, prices):
		return price_rules.priced_key(tag, prices, self._needs.commodity_record[tag])

	def _material_commodity_map(self):
		return self._needs.material_commodity_map()

	def _material_tag(self, material):
		return self._needs.material_pool[material]

	def _material_market_tonnes(self, commodity):
		return self._needs.material_market_tonnes[commodity]

	def _commodity_materials(self, commodity):
		return self._needs.commodity_materials[commodity]

	def material_stock_t(self, commodity):
		return self._needs.goods_stock[commodity]

	def not_traded_materials(self):
		return self._needs.not_traded_materials()

	def serves_a_need(self, material):
		return self._needs.material_serves_a_need[material]

	@property
	def trade_registry(self):
		return self._needs.trade_registry()

	def can_pay(self, money):
		return self._needs.can_pay(money)

	# ---- production and projects ----

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

	# ---- the land and the farm ----

	def farm_sites(self):
		return self._needs.farm_sites()

	def farm_weather_by_tile(self, year):
		return self._needs.farm_weather[year]

	def _pooled_farm_weather_multiplier(self, year, weather_stdev_fraction=None, harmed=True):
		return self._needs.harvest_weather(year, weather_stdev_fraction, harmed)

	def externality_yield_factors(self, year):
		return self._needs.externality_yield_factors(year)

	def tile_owner_map(self):
		return self._needs.tile_owner_map()

	def tiles_owned_by(self, actor_id):
		return self._needs.tiles_owned_by[actor_id]

	def timber_felled(self):
		return self._needs.timber_felled()
