"""What actors do at the one goods market: offer, bid, and forget their dealings of the year."""
from typing import Any

from sim.agents.api import supply
from sim.markets.api import ForgetActorOrders, NoteActorPurchase, NoteActorSale


class Market:
	"""The agent economy's book as actors reach it. `world` is the root that hands out the parts."""

	def __init__(self, world: Any) -> None:
		self.world = world

	@property
	def needs(self) -> Any:
		return self.world.needs

	def market_key(self, node_id: str) -> str:
		"""What a concern's operators share: a goods category is one market, any other concern its own."""
		category = self.world.setting.nodes[node_id].get("cat")
		return category if category in self.world.groups.goods_category_names else node_id

	def market_forget(self, actor_id: str) -> None:
		"""An actor's sales and purchases noted for this year's market end; it deals afresh."""
		self.needs.send(ForgetActorOrders(actor_id))

	def market_sale(self, seller_id: str, material: str, tonnes: float, from_concerns: Any = None) -> None:
		"""An actor sells `tonnes` of a material into the one goods market this year. One whose concerns
		made it, [(node id, tonnes)], will not sell below what they cost it to make. The goods are offered in the agent
		economy's book and the proceeds reach the seller's purse when the year's market has cleared."""
		self.needs.send(NoteActorSale(seller_id, material, tonnes, from_concerns))

	def market_purchase(self, buyer_id: str, commodity: str, tonnes: float, budget: float = 0.0) -> None:
		"""An actor buys `tonnes` of a commodity at the one goods market this year: it bids for them in the agent
		economy's book, paying up to `budget` out of its purse."""
		self.needs.send(NoteActorPurchase(buyer_id, commodity, tonnes, budget))

	def sells_on_book(self, node_id: str) -> bool:
		"""Whether what a concern makes is sold in the agent economy's book, so its takings are the market's and not the
		engine's estimate."""
		return any(self.needs.agent_trades_good[material] for material in supply.materials_made_by(node_id))
