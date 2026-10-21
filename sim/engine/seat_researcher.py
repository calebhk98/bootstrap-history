"""The founder's seat as a researcher, so its start goes through the same `research.begin` every actor uses.

The seat answers the questions the shared path asks (what it knows, what hands it has, what it holds, what it
can spend) from its own books, and `commit_research` begins the project there instead of in an actor's `works`.
"""
from typing import Any, Dict

from .project_funding import paid_credit


class SeatResearcher:
	researches = True

	def __init__(self, sim: Any, precaution: bool = False) -> None:
		self._sim = sim
		self.precaution = precaution
		self.works = sim.state.projects.active
		self.workforce = sim.state.household.employees

	def identity(self) -> str:
		return "seat:%s" % self._sim.state.acting_seat

	def knows(self, node_id: str, world: Any) -> bool:
		return node_id in self._sim.state.projects.done

	def research_hands(self, family: str) -> float:
		labour = self._sim.labour
		return labour.scholar_hands_available() if family == "scholar" else labour.craft_hands_available()

	def held_tonnes(self, material: str) -> float:
		sim = self._sim
		return sim.material_stock_t(sim._material_tag(material)[0])

	def copy_budget(self, world: Any) -> float:
		"""Cash and credit not already owed on work in hand."""
		sim = self._sim
		active = sim.state.projects.active
		owed = sum(active[node_id].get("cost_left") or 0.0 for node_id in sorted(active))
		return max(0.0, sim.state.household.capital) + sim.credit_limit() - owed

	def research_price(self, costs: Dict[str, Any], node_id: str, world: Any) -> float:
		"""What the seat still owes on the node: the shared bill less what it already paid towards it."""
		sim = self._sim
		price = sim.project_cost(node_id)
		return max(0.0, price - paid_credit(price, (sim.state.projects.paid_towards or {}).get(node_id, 0.0)))

	def commit_research(self, node_id: str, costs: Dict[str, Any], world: Any) -> str:
		return self._sim.begin_seat_project(node_id, self.precaution)
