"""The markets module: the goods market's year, its clearing, household demand, the goods categories and the agent economy.

It owns the book, the year's flows, the agent economy's record and whether money is counted at the economy's wage
(`MarketsWorld`), and builds the two market objects: `economy` (the port over the agent economy) and `goods_market` (the one goods
market every buyer and seller asks). Both read the game through `PortWorld` (port_world.py). Every view it publishes is uncached:
the goods market writes the flows and the economy writes the record in place. `Sim.economy` and `Sim.goods_market` are forwarders
to these two for callers not yet in a module."""
from sim.assembly.api import Module

from .absorption import Absorption
from .agent_views_labour import AgentLabourViews
from .agent_views_land import AgentLandViews
from .agent_views_outcome import AgentOutcomeViews
from .agent_views_prices import AgentPriceViews
from .agent_views_volumes import AgentVolumeViews
from .category_views import Categories
from .clearing import MarketClearing
from .commands_applied import Applying
from .goods_views import GoodsViews
from .household_views import HouseholdNeeds
from .market_objects import MarketObjects


class Markets(Module):

	PARTS = {
		"market_objects": MarketObjects,
		"clearing": MarketClearing,
		"categories": Categories,
		"household_needs": HouseholdNeeds,
		"absorption": Absorption,
		"goods_views": GoodsViews,
		"agent_price_views": AgentPriceViews,
		"agent_labour_views": AgentLabourViews,
		"agent_land_views": AgentLandViews,
		"agent_volume_views": AgentVolumeViews,
		"agent_outcome_views": AgentOutcomeViews,
		"applying": Applying,
	}
