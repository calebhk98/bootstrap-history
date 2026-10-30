"""What the actors employ and how many concerns they run: the figures the labour and goods markets read."""
from typing import Any, List, Set, Tuple

from sim.agents.api import SOLDIER_TRADE

from . import rules


class Staff:
	"""Mixed into `Actors`."""

	needs: Any
	world: Any

	def actor_staff_fte(self, trade: str) -> float:
		"""People of this trade that firms and governments employ: they come out of the
		same reachable pool the founder hires from."""
		if not self.world.records:
			return 0.0
		return self.cast().home_staff_fte(trade)  # type: ignore[attr-defined,no-any-return]

	def actor_staff_nationwide(self, trade: str) -> float:
		"""People of this trade that firms and governments hold nationwide. Staff in the founder's
		reachable pool is the slice the actors drew from it; the government's army is its whole
		force, so that one trade reads the army in place of the government's slice."""
		if not self.world.records:
			return 0.0
		beyond = 0.0
		if trade == SOLDIER_TRADE:
			record = self.world.records.get("government:" + str(self.needs.civilisation().get("id")))
			if record is not None:
				beyond = record.army - record.workforce.get(trade, 0.0)
		return rules.nationwide_staff(self.actor_staff_fte(trade), beyond)

	def actor_staff_total(self) -> float:
		"""People of every trade that firms and governments employ."""
		if not self.world.records:
			return 0.0
		return sum(self.cast().staff_by_trade().values())  # type: ignore[attr-defined,no-any-return]

	def actor_concerns_in(self, category: str) -> float:
		"""How many concerns in a goods category actors run, each sharing the founder's market."""
		if not self.world.records:
			return 0
		return self.cast().concerns_in(category, self.needs.tree_nodes())  # type: ignore[attr-defined,no-any-return]

	def concerns_of_active_firms(self) -> Set[str]:
		"""Every concern some firm that has not exited runs (none while no actor is recorded)."""
		if not self.world.records:
			return set()
		return self.cast().concerns_of_active_firms()  # type: ignore[attr-defined,no-any-return]

	def firm_concern_holdings(self) -> List[Tuple[str, float, float]]:
		"""(concern, how many founding sizes the firm runs it at, the share of its staff the firm has found) for each concern of
		each firm in business, firms in the registry's order."""
		if not self.world.records:
			return []
		return [(node_id, firm.capacity_of(node_id), firm.staffed_share(node_id))
		        for firm in self.cast().active_firms() for node_id in firm.concerns]  # type: ignore[attr-defined]

	def concern_versions(self) -> Tuple[int, int]:
		"""(changes whenever the set of concerns actors run does or a concern's size does, changes only when the set does),
		for caches that read them."""
		if not self.world.records:
			return 0, 0
		registry = self.cast()  # type: ignore[attr-defined]
		return registry.version[0], registry.concern_set_version[0]
