"""Running totals of the sizes at which active operators run each concern.

Each operator's contribution is remembered, so a change of one operator's
concerns or capacities costs that operator's concern count, never a walk of all
operators. Holds only plain data, so a registry holding it still copies.
"""
from typing import Any, Dict, Optional


class ConcernTotals:
	def __init__(self) -> None:
		self.size_by_node: Dict[str, float] = {}
		self._holder_count: Dict[str, int] = {}
		self._contribution: Dict[str, Dict[str, float]] = {}
		# bumped on every change, so a derived reading knows when it is stale
		self.changes = 0
		self._by_category: Optional[Any] = None

	def sync(self, operator_id: str, record: Any) -> None:
		"""Bring the operator's contribution up to its record: its concerns at their capacities,
		or nothing once it has exited."""
		if record.exited_year is not None:
			current: Dict[str, float] = {}
		else:
			current = {node_id: record.capacity.get(node_id, 1.0) for node_id in record.concerns}
		previous = self._contribution.get(operator_id, {})
		if current == previous:
			return
		for node_id, size in previous.items():
			if node_id not in current:
				self._holder_count[node_id] -= 1
				if self._holder_count[node_id] <= 0:
					del self._holder_count[node_id]
					del self.size_by_node[node_id]
					continue
			self.size_by_node[node_id] -= size
		for node_id, size in current.items():
			if node_id not in previous:
				self._holder_count[node_id] = self._holder_count.get(node_id, 0) + 1
				self.size_by_node.setdefault(node_id, 0.0)
				self.size_by_node[node_id] += size
			else:
				self.size_by_node[node_id] += size
		if current:
			self._contribution[operator_id] = current
		else:
			self._contribution.pop(operator_id, None)
		self.changes += 1

	def forget(self, operator_id: str) -> None:
		"""Remove an operator's contribution (its actor is being rebuilt)."""
		previous = self._contribution.pop(operator_id, None)
		if previous:
			for node_id, size in previous.items():
				self._holder_count[node_id] -= 1
				if self._holder_count[node_id] <= 0:
					del self._holder_count[node_id]
					del self.size_by_node[node_id]
				else:
					self.size_by_node[node_id] -= size
			self.changes += 1

	def size_of_category(self, category: Any, nodes: Dict[str, Any]) -> float:
		"""Sum over the concerns of a goods category (walks the distinct concerns held, not the operators)."""
		if self._by_category is None or self._by_category[0] != self.changes:
			sums: Dict[Any, float] = {}
			for node_id, size in self.size_by_node.items():
				node_category = nodes[node_id].get("cat")
				sums[node_category] = sums.get(node_category, 0.0) + size
			self._by_category = (self.changes, sums)
		return self._by_category[1].get(category, 0)
