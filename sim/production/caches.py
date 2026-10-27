"""The memos production keeps on the seat's household over what is done and operating, and the rules that drop them.

The household object is the agents' facade; these functions touch only its memo fields and its version counters, so the
engine's hooks (which fire while a game is still being built, before any module exists) call them directly and the module's
commands call them too."""
from typing import Dict, Iterable, List


def in_tree_order(tree: Iterable[str], done) -> List[str]:
	"""Everything finished, in the tree's own order: `done` is a set of strings, which iterates in hash order, and a float sum
	over it would differ in its last bits between one process and the next."""
	return [node_id for node_id in tree if node_id in done]


def done_in_order(household, tree: Dict[str, dict], done) -> List[str]:
	"""`in_tree_order`, kept on the household until the done set changes (it is O(nodes) and revenue asks for it constantly).
	The memo is dropped by hand wherever `done` gains or loses a member, not by a length check: a year that abandons one work
	and completes another leaves the length identical and the contents different."""
	sequence = getattr(household, "_done_seq", None)
	if sequence is None:
		sequence = household._done_seq = in_tree_order(tree, done)
	return sequence


def forget_done(household) -> None:
	"""The done set changed. The capability factor walks it too (filtered by granted, which changes in the same breath), so its
	memo goes with it."""
	household._done_seq = None
	household._cap_factor = None
	household.bump_done_version()


def forget_operating(household) -> None:
	"""What is operating changed."""
	household._cap_factor = None
	household.bump_operating_version()


def forget_active(household) -> None:
	"""The projects in hand changed."""
	household.bump_active_version()


def forget_revenue(household) -> None:
	"""Drop every memo derived from what is done and operating (a load and a seat switch need them rebuilt)."""
	household._done_seq = None
	household._cap_factor = None
	household._revenue_cache_key = None
	household._revenue_cache_val = None
	household._rev_up_candidates_cache = None
	household._practice_cache = None
