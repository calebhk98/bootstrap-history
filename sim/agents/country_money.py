"""What a country's actors see of its collection, its prices, its goods market and its credit."""
from typing import Any, Dict, List, Optional

from sim.geography.api import settlement, usable_modes

from . import collection, ledger
from .collection_world import CollectionView
from .country_part import SharedPart
from .edges import EDGE_STATE_SPENDING


class CountryCollection(CollectionView):
	"""What the country's officials collect, over its held tiles and the routes its starting technologies open."""

	def collection_people_by_tile(self) -> Dict[str, float]:
		"""The country's people spread over its tiles by settlement."""
		return collection.spread_people(self.world.people.population_total(), settlement.population_shares(self.world.revenue.held_tiles()))

	def collection_modes(self) -> List[str]:
		"""The route modes the country's starting technologies open."""
		return usable_modes([self.world.knowledge.baseline_knowledge()])


class CountryQuotes(SharedPart):
	"""The prices the country's own markets quote."""

	part = "quotes"
	# home: which commodity and staple a material is, is a fact of the material
	home_members = frozenset(("commodity_of", "staple_material"))

	def material_cost(self, material: str, tonnes: float) -> Optional[float]:
		"""Money to buy this many tonnes of a material at the price the country's own markets quote; None when
		they quote none (not on sale)."""
		price = self.world.own.get().price_per_tonne(material)
		return None if price is None else price * tonnes

	def material_price(self, material: str) -> Optional[float]:
		"""Money for one tonne of a material at the country's own quote; None when it is not on sale."""
		return self.material_cost(material, 1.0)


class CountryMarket(SharedPart):
	"""A country has no goods market of its own in the book: what its state buys and sells is paid for at once."""

	part = "market"
	# home: market keys and what sells on the book are the shared market's
	home_members = frozenset(("market_forget", "market_key", "sells_on_book"))

	def market_purchase(self, buyer_id: str, commodity: str, tonnes: float, budget: float = 0.0) -> None:
		"""What its state buys is paid for at once."""
		buyer = self.world.holder.actors.get(buyer_id)
		if buyer is not None and budget > 0.0:
			ledger.transfer(buyer, self.world.setting.edge(EDGE_STATE_SPENDING), budget, "purchase")

	def market_sale(self, seller_id: str, material: str, tonnes: float, from_concerns: Any = None) -> None:
		"""What a country's state sells is paid for at the price the market quotes."""
		seller = self.world.holder.actors.get(seller_id)
		proceeds = self.world.quotes.material_cost(material, tonnes)
		if seller is not None and tonnes > 0.0 and proceeds is not None:   # a good with no quote does not sell
			ledger.transfer(self.world.setting.edge(EDGE_STATE_SPENDING), seller, proceeds, "sale")


class CountryCredit(SharedPart):
	"""The country's credit."""

	part = "credit"
	# home: the founder's own credit and debts are the home seat's; rate and lending figures are the shared market's until a country keeps its own
	home_members = frozenset(("credit_headroom", "debt_service_share_of_surplus", "founder_credit_limit", "founder_debt_rate", "founder_defaults", "household_saving", "market_rate", "nodes_with_mechanic", "pay_interest", "starting_rate", "state_lending"))

	def state_may_borrow(self, state: Any) -> bool:
		"""Whether the state holds a technology declaring the `state_credit` mechanic, in its own knowledge or its country's."""
		return any(state.knows(node_id, self.world) for node_id in self.shared.nodes_with_mechanic("state_credit"))
