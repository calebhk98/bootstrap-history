"""What the goods market and the port over the agent economy read of the game: one member per view the markets module declares.

`GoodsMarket` and `EconomyPort` ask this object where they used to ask the engine's `Sim`. Every member is a view of another
owner (or a send of its command), or one of the markets module's own methods; the raw state objects (the saved state's
sections, the seats' registry) are `legacy_*` views, debts that go when that state moves. Members about the foreign
partners and the freight, coin and resources owners are in port_world_foreign.py (`foreign`), those about the map in
port_world_map.py (`map`)."""
from typing import Optional
from types import SimpleNamespace

from sim.freight.api import FREIGHT_FEED_PRICE_MATERIAL

from . import trade_duty
from .port_world_foreign import ForeignReads
from .port_world_map import MapReads
from .port_world_reads import FarmReads, MaterialReads, PortFinanceReads, ProductionReads, ScenarioReads


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

	@property
	def trade_registry(self):
		return self._needs.trade_registry()

	def playing_seats(self):
		return self._needs.seat_list()["playing"]

	def edge(self, name):
		return self._needs.cast_state().edge(name)

	def actor_world(self):
		return self._needs.actor_world()

	def regional_people_by_band(self):
		return self._needs.regional_people_by_band()


class LabourReads:
	"""The workforce views the port reads, under the names `Labour` had."""

	def __init__(self, needs):
		self._needs = needs

	def base_tile(self):
		return self._needs.base_tile()

	def money_per_labour_hour(self):
		return self._needs.money_per_labour_hour()

	def wage_per_hour(self, trade) -> Optional[float]:
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

	def staff_posting(self):
		return self._needs.staff_posting()

	def once_posting(self):
		return self._needs.once_posting()

	def wage_work_offered(self):
		return self._needs.wage_work_offered()

	def newcomers(self):
		return self._needs.newcomers()

	def employed_by_trade(self):
		return self._needs.employed_by_trade()


class PortWorld:

	FREIGHT_FEED_PRICE_MATERIAL = FREIGHT_FEED_PRICE_MATERIAL

	def __init__(self, needs, owner, parts):
		self._needs = needs
		self._owner = owner          # the markets module: its clock, kernels and saved state
		self._parts = parts          # its parts: the objects, the clearing
		self.scenario = ScenarioReads(needs)     # the year, the civilisation, the tree, the price level and the seats
		self.state = StateReads(needs, owner)
		self.labour = LabourReads(needs)
		self.map = MapReads(needs)               # the land module's map views
		self.foreign = ForeignReads(needs)       # partners, freight, the partners' coin and the deposits
		self.materials = MaterialReads(needs)    # price tables and commodity groupings
		self.finance = PortFinanceReads(needs)   # the state's money, credit, coin and purse
		self.production = ProductionReads(needs)  # techniques, the concerns' books, projects
		self.farm = FarmReads(needs)             # farm sites, weather, ownership, timber

	def send(self, command):
		return self._needs.send(command)

	def bound_kernels(self):
		"""The module's kernels as the assembly bound them: a mod's replacement, else the reference."""
		return dict(self._owner.kernels)

	# ---- the module's own objects and records ----

	@property
	def economy(self):
		return self._parts.market_objects.economy

	@property
	def goods_market(self):
		return self._parts.market_objects.goods_market

	def agent_record(self):
		"""The agent economy's saved record."""
		return self._owner.world.agent_economy

	def money_from_economy(self):
		return self._owner.world.money_from_economy

	def market_flows(self):
		return self._parts.clearing.legacy_market_flows()

	def market_state(self, material):
		return self._parts.clearing.market_state(material)

	def remembered(self, name):
		"""What the acting seat's goods market worked out and kept under `name`, or None."""
		return self._parts.market_objects.seat_cache(name)

	def remember(self, name, value):
		self._parts.market_objects.set_seat_cache(name, value)

	# ---- the civilisation and the borders ----

	def civilisation_record(self, civilization_id):
		"""A civilisation as its file gives it (mods applied, checked)."""
		return self._needs.civilisation_record[civilization_id]

	def border_terms(self, destination, source):
		"""(tariff share, embargoed) `destination`'s state holds toward goods crossing from `source`."""
		return trade_duty.terms_in_book(self._needs.store_book(), destination, source)
