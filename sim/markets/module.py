"""The markets module: the goods market's year, its clearing, household demand, the goods categories and the agent economy.

It owns the book, the year's flows, the agent economy's record and whether money is counted at the economy's wage
(`MarketsWorld`), and builds the two market objects: `economy` (the port over the agent economy) and `goods_market` (the one goods
market every buyer and seller asks). Both read the game through `PortWorld` (port_world.py). Every view it publishes is uncached:
the goods market writes the flows and the economy writes the record in place. `Sim.economy` and `Sim.goods_market` are forwarders
to these two for callers not yet in a module."""
from sim.assembly.api import Module

from .absorption import Absorption
from .agent_views import AgentViews
from .category_views import Categories
from .clearing import Clearing
from .commands_applied import Applying
from .demand import Demand
from .household_views import HouseholdNeeds
from .goods_market import GoodsMarket
from .goods_views import GoodsViews
from .port import EconomyPort
from .port_world import PortWorld

# the remembered figures a seat switch drops (the clearing's and the household demand's are keyed on what they read)
_DROPPED_ON_RESET = ("goods_cat_state", "goods_category_ratios", "income_factor", "goods_mkt_op_factor")


class Markets(Clearing, Categories, Demand, HouseholdNeeds, Absorption, GoodsViews, AgentViews, Applying, Module):

	def setup(self):
		self._caches = {}                  # (seat id, name) -> a remembered figure; never saved
		self._needs_served_by_mods = {}    # installed mod ids -> material -> the needs it serves; data, frozen for the game
		self._climate_baskets = {}         # civilisation id -> (its household basket with the tiles' climate floors, the model); frozen for the game
		self._partner_demand = {}          # civilisation id -> tonnes a year its households buy; data, frozen for the game
		self._nodes_by_category = None     # category -> node ids, in the tree's order; the tree does not change after load
		self.reads = PortWorld(self.needs, self)
		self.economy = EconomyPort(self.reads)       # opens the agent economy when first asked, or on the opening command
		self.goods_market = GoodsMarket(self.reads)

	# ---- what the acting seat remembers ----

	def _seat_cache(self, name):
		return self._caches.get((self.clock.acting_seat, name))

	def _set_seat_cache(self, name, value):
		self._caches[(self.clock.acting_seat, name)] = value

	def _seat_dict(self, name):
		key = (self.clock.acting_seat, name)
		remembered = self._caches.get(key)
		if remembered is None:
			remembered = self._caches[key] = {}
		return remembered

	def reset_market_caches(self, command):
		for name in _DROPPED_ON_RESET:
			self._caches.pop((self.clock.acting_seat, name), None)

	def legacy_agent_economy(self):
		"""The agent economy's record, where the traders' cargo legs are kept; the port and the foreign trade module write it in place."""
		return self.world.agent_economy

	def money_from_economy(self):
		return self.world.money_from_economy
