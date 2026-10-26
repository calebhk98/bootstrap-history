"""The founder's seat as a researcher, so its start goes through the same `research.begin` every actor uses.

The seat answers the questions the shared path asks (what it knows, what hands it has, what it holds, what it can
spend) from its own books, and `commit_research` begins the project there instead of in an actor's `works`."""
from typing import Any, Dict

from . import funding


class SeatResearcher:
	researches = True

	def __init__(self, projects: Any, precaution: bool = False) -> None:
		self._projects = projects
		self._needs = projects.needs
		self.precaution = precaution
		self.works = self._needs.legacy_projects().active
		self.workforce = self._needs.legacy_acting_household().employees

	def identity(self) -> str:
		return "seat:%s" % self._needs.acting_seat()

	def knows(self, node_id: str, world: Any) -> bool:
		return node_id in self._needs.techniques_held()

	def research_hands(self, family: str) -> float:
		return self._needs.hours_available["scholar_hands" if family == "scholar" else "craft_hands"]

	def held_tonnes(self, material: str) -> float:
		return self._needs.goods_stock[self._needs.material_pool[material][0]]

	def copy_budget(self, world: Any) -> float:
		"""Cash and credit not already owed on work in hand."""
		return max(0.0, self._needs.acting_balance()) + self._needs.credit_limit() - self._projects._owed_on_work_in_hand()

	def research_price(self, costs: Dict[str, Any], node_id: str, world: Any) -> float:
		"""What the seat still owes on the node: the shared bill less what it already paid towards it."""
		price = self._needs.project_cost(node_id)
		paid_towards = self._needs.legacy_projects().paid_towards or {}
		return max(0.0, price - funding.paid_credit(price, paid_towards.get(node_id, 0.0)))

	def commit_research(self, node_id: str, costs: Dict[str, Any], world: Any) -> str:
		return self._projects.begin_project(node_id, self.precaution)
