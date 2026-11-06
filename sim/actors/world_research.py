"""What a researching actor asks of the world: hands, sellers and substitutes."""
from typing import Any, List, Optional

from sim.agents.api import OBSERVATION_RANGE_KM, TRADE_TONNES_FOR_UNIT_CONTACT, research_gate
from sim.geography.api import flow_ledger
from sim.labour import api as labour_api

from sim.seats import api as seats_api



class Research:
	"""Read-only questions behind the start gates in `sim/agents/research_gate.py`. `world` is the root that hands out the parts."""

	def __init__(self, world: Any) -> None:
		self.world = world

	@property
	def needs(self) -> Any:
		return self.world.needs

	def research_trades(self, family: str) -> List[str]:
		"""The trades whose people count as hands of a family (scholars; or the craft trades), the same for every country."""
		needs = self.needs
		if family == research_gate.SCHOLAR_FAMILY:
			return [labour_api.scholar_trade()]
		return [trade for trade in needs.available_trades()
				if trade != labour_api.scholar_trade() and needs.is_craft_trade[trade]]

	def research_hands(self, actor: Any, family: str) -> float:
		"""People of the family on the actor's staff, plus the free people it could take on."""
		own = getattr(actor, "research_hands", None)
		if own is not None:
			return own(family)
		return sum(actor.workforce.get(trade, 0.0) + (self.world.labour.free_fte(trade, actor.identity()) or 0.0)
				   for trade in self.research_trades(family))

	def unsold_materials(self, actor: Any, node_id: str) -> List[str]:
		"""Materials no one in reach sells, against what the actor itself holds (nothing, unless it says)."""
		return self.needs.materials_without_a_seller(node_id, actor.held_tonnes)

	def contact_volume(self, place_a: Optional[str], place_b: Optional[str]) -> float:
		"""News passing between two places in a year: neighbours see each other's work (the range an onlooker
		sees at), and each tonne carried between them is a visit (`TRADE_TONNES_FOR_UNIT_CONTACT`)."""
		neighbour = seats_api.seen_from(1.0, self.world.setting.distance_km(place_a, place_b), OBSERVATION_RANGE_KM)
		carried = self.needs.goods_carried_last_year()
		tonnes = flow_ledger.tonnes_between(carried, str(place_a), str(place_b)) + flow_ledger.tonnes_between(
			carried, str(place_b), str(place_a))
		return neighbour + tonnes / TRADE_TONNES_FOR_UNIT_CONTACT

	def purchasable_substitute_discount(self) -> float:
		return self.needs.substitute_quality_discount()

	def research_cost(self, node_id: str, max_age_years: int) -> float:
		"""What the node costs to pioneer, worked out afresh only when the last figure is `max_age_years` old
		(the cost walks the founder's materials and labour, so every actor's yearly look would repeat it)."""
		kept = self.world.registry.research_costs
		stamped = kept.get(node_id)
		year = self.world.setting.year
		if stamped is None or year - stamped[0] >= max_age_years:
			stamped = kept[node_id] = (year, self.world.concerns.copy_cost(node_id))
		return stamped[1]
