"""What a researching actor asks of the world: hands, sellers and substitutes (mixed into `SimWorld`)."""
from typing import Any, List

from sim.agents.api import research_gate

from .material_availability import materials_without_a_seller


class ResearchView:
	"""Read-only questions behind the start gates in `sim/agents/research_gate.py`."""

	_sim: Any

	def research_trades(self, family: str) -> List[str]:
		"""The trades whose people count as hands of a family (scholars; or the craft trades), the same for every country."""
		sim = self._sim
		if family == research_gate.SCHOLAR_FAMILY:
			return [research_gate.SCHOLAR_TRADE]
		return [trade for trade in sim.labour.available_trades()
				if trade != research_gate.SCHOLAR_TRADE and sim.labour.is_craft_trade(trade)]

	def research_hands(self, actor: Any, family: str) -> float:
		"""People of the family on the actor's staff, plus the free people it could take on."""
		own = getattr(actor, "research_hands", None)
		if own is not None:
			return own(family)
		return sum(actor.workforce.get(trade, 0.0) + (self.free_fte(trade, actor.identity()) or 0.0)
				   for trade in self.research_trades(family))

	def unsold_materials(self, actor: Any, node_id: str) -> List[str]:
		"""Materials no one in reach sells, against what the actor itself holds (nothing, unless it says)."""
		holding = getattr(actor, "held_tonnes", None)
		if holding is None:
			return materials_without_a_seller(self._sim, node_id, held_tonnes=lambda material: 0.0)
		return materials_without_a_seller(self._sim, node_id, held_tonnes=holding)

	def purchasable_substitute_discount(self) -> float:
		return self._sim.PURCHASABLE_SUBSTITUTE_QUALITY_DISCOUNT

	def research_cost(self, node_id: str, max_age_years: int) -> float:
		"""What the node costs to pioneer, worked out afresh only when the last figure is `max_age_years` old
		(the cost walks the founder's materials and labour, so every actor's yearly look would repeat it)."""
		kept = self._sim.actors._research_costs
		stamped = kept.get(node_id)
		if stamped is None or self.year - stamped[0] >= max_age_years:
			stamped = kept[node_id] = (self.year, self.copy_cost(node_id))
		return stamped[1]
