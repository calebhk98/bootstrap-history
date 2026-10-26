"""The markets module: the goods market, its clearing, household demand, the goods categories and the agent economy.

While the engine's market objects (`Sim.economy`, the port over the agent economy, and `Sim.goods_market`) have not moved, the
module reaches them through `legacy_game`; every view it publishes is therefore uncached. The handles go as the objects move
into this package."""
from sim.assembly.api import Module

from .agent_views import AgentViews
from .commands_applied import Applying
from .goods_views import GoodsViews


class Markets(GoodsViews, AgentViews, Applying, Module):

	def _game(self):
		return self.needs.legacy_game()

	def _economy(self):
		return self._game().economy

	def _market(self):
		return self._game().goods_market
