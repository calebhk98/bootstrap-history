"""What a researching actor asks of the world: hands, sellers and substitutes (mixed into `SimWorld`)."""
from typing import Any, List

from sim.agents.research_gate import SCHOLAR_FAMILY, SCHOLAR_TRADE

from .material_availability import materials_without_a_seller


class ResearchView:
	"""Read-only questions behind the start gates in `sim/agents/research_gate.py`."""

	_sim: Any

	def research_hands(self, actor: Any, family: str) -> float:
		"""People of the family on the actor's staff, plus the free people it could take on."""
		own = getattr(actor, "research_hands", None)
		if own is not None:
			return own(family)
		sim = self._sim
		trades = [SCHOLAR_TRADE] if family == SCHOLAR_FAMILY else [
			trade for trade in sorted(sim.wages) if trade != SCHOLAR_TRADE and sim.labour.is_craft_trade(trade)]
		return sum(actor.workforce.get(trade, 0.0) + (self.free_fte(trade, actor.identity()) or 0.0) for trade in trades)

	def unsold_materials(self, actor: Any, node_id: str) -> List[str]:
		"""Materials no one in reach sells, against what the actor itself holds (nothing, unless it says)."""
		holding = getattr(actor, "held_tonnes", None)
		if holding is None:
			return materials_without_a_seller(self._sim, node_id, held_tonnes=lambda material: 0.0)
		return materials_without_a_seller(self._sim, node_id, held_tonnes=holding)

	def purchasable_substitute_discount(self) -> float:
		return self._sim.PURCHASABLE_SUBSTITUTE_QUALITY_DISCOUNT
