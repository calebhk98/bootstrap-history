"""The markets module's own objects: the agent economy's port, the one goods market and the acting seat's remembered figures."""
from sim.assembly.api import Part

from .goods_market import GoodsMarket
from .port import EconomyPort
from .port_world import PortWorld


class MarketObjects(Part):

	def __init__(self, module):
		super().__init__(module)
		self._caches = {}                  # (seat id, name) -> a remembered figure; never saved

	def setup(self):
		self.reads = PortWorld(self.needs, self.module, self.parts)
		self.economy = EconomyPort(self.reads)       # opens the agent economy when first asked, or on the opening command
		self.goods_market = GoodsMarket(self.reads)

	def seat_cache(self, name):
		return self._caches.get((self.clock.acting_seat, name))

	def set_seat_cache(self, name, value):
		self._caches[(self.clock.acting_seat, name)] = value

	def seat_dict(self, name):
		key = (self.clock.acting_seat, name)
		remembered = self._caches.get(key)
		if remembered is None:
			remembered = self._caches[key] = {}
		return remembered

	def agent_economy_store(self):
		"""The agent economy's record, where the traders' cargo legs are kept; the port and the foreign trade module write it in place."""
		return self.world.agent_economy

	def money_from_economy(self):
		return self.world.money_from_economy
