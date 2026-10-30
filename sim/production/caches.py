"""The memos production keeps for each seat over what is done and operating, and the rules that drop them.

The module drops them when the engine sends `RefreshDoneCaches`, `RefreshOperatingCaches` or `ForgetRevenueCaches`; the version
counters those moments bump stay with the household."""
from typing import Any, Dict, Iterable, List, Optional


def in_tree_order(tree: Iterable[str], done) -> List[str]:
	"""Everything finished, in the tree's own order: `done` is a set of strings, which iterates in hash order, and a float sum
	over it would differ in its last bits between one process and the next."""
	return [node_id for node_id in tree if node_id in done]


class SeatMemos:
	"""One seat's remembered figures; each is dropped where what it was computed from changes."""

	def __init__(self) -> None:
		self.done_sequence: Optional[List[str]] = None
		self.capability_factor: Optional[float] = None
		self.revenue_key: Any = None
		self.revenue_value: Any = None
		self.candidates: Any = None
		self.practice: Any = None

	def done_in_order(self, tree: Dict[str, dict], done) -> List[str]:
		"""`in_tree_order`, kept until the done set changes (it is O(nodes) and revenue asks for it constantly). The memo is dropped
		wherever `done` gains or loses a member, not by a length check: a year that abandons one work and completes another leaves
		the length identical and the contents different."""
		if self.done_sequence is None:
			self.done_sequence = in_tree_order(tree, done)
		return self.done_sequence

	def forget_done(self) -> None:
		"""The done set changed. The capability factor walks it too (filtered by granted, which changes in the same breath), so its
		memo goes with it."""
		self.done_sequence = None
		self.capability_factor = None

	def forget_operating(self) -> None:
		"""What is operating changed."""
		self.capability_factor = None

	def forget_all(self) -> None:
		"""Drop every memo derived from what is done and operating."""
		self.__init__()  # type: ignore[misc]
