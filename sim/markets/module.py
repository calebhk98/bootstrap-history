"""The markets module: the goods market's year, its clearing, household demand, the goods categories and the agent economy.

It owns the book, the year's flows, the agent economy's record and whether money is counted at the economy's wage
(`MarketsWorld`). The engine's market objects (`Sim.economy`, the port over the agent economy, and `Sim.goods_market`) have not
moved into the package yet, so the module reaches them through `legacy_game`; every view it publishes is therefore uncached.
The handles go as the objects move here."""
from sim.assembly.api import Module

from .absorption import Absorption
from .agent_views import AgentViews
from .category_views import Categories
from .clearing import Clearing
from .commands_applied import Applying
from .demand import Demand
from .goods_views import GoodsViews

# the remembered figures a seat switch drops (the clearing's and the household demand's are keyed on what they read)
_DROPPED_ON_RESET = ("goods_cat_state", "goods_category_ratios", "income_factor", "goods_mkt_op_factor")


class Markets(Clearing, Categories, Demand, Absorption, GoodsViews, AgentViews, Applying, Module):

	def setup(self):
		self._caches = {}                  # (seat id, name) -> a remembered figure; never saved
		self._nodes_by_category = None     # category -> node ids, in the tree's order; the tree does not change after load

	def _game(self):
		return self.needs.legacy_game()

	def _economy(self):
		return self._game().economy

	def _market(self):
		return self._game().goods_market

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
