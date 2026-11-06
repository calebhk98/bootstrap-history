"""`RegistryConcerns`: which actors run which concerns, how large, and who the rivals are.

Reached as `registry.concerns`. A `ConcernWatch` hangs on each market operator's business and keeps the `node -> operator ids`
index and the size totals current as its plants open and close.
"""
from typing import Any, Dict, List, Set

from .concern_totals import ConcernTotals
from .firm import Firm


class ConcernWatch:
	"""Keeps one firm's entries in the `node -> firm ids` index current whenever its business opens or closes a plant. Holds
	only plain data, so a state holding a watched business still copies."""

	def __init__(self, firm_id: str, holders: Dict[str, Set[str]], version: List[int],
				 totals: ConcernTotals, record: Any, concern_set_version: List[int]) -> None:
		self.firm_id = firm_id
		self.holders = holders
		self.version = version
		self.concern_set_version = concern_set_version
		self.totals = totals
		self.record = record
		self.known: Set[str] = set()

	def __call__(self) -> None:
		current = set(self.record.business.reading.entry_keys())
		if current != self.known:
			self.version[0] += 1
			self.concern_set_version[0] += 1
		for node_id in self.known - current:
			self.holders[node_id].discard(self.firm_id)
		for node_id in current - self.known:
			self.holders.setdefault(node_id, set()).add(self.firm_id)
		self.known = current
		self.totals.sync(self.firm_id, self.record)


class RegistryConcerns:

	def __init__(self, registry: Any) -> None:
		self.registry = registry
		# which actors hold each concern (kept current by ConcernWatch)
		self._holders: Dict[str, Set[str]] = {}
		# bumped whenever any firm's concerns change, so market caches keyed on it stay honest
		self.version: List[int] = [0]
		# bumped only when the set of concerns a firm runs changes, not when a concern's size does
		self.concern_set_version: List[int] = [0]
		self._totals = ConcernTotals()

	def forget(self, actor_id: str, previous: Any) -> None:
		"""A replaced actor's watch starts over."""
		watch = previous.record.business.watch
		if isinstance(watch, ConcernWatch):
			watch.known = set()
			self._totals.forget(actor_id)
			for holding in self._holders.values():
				holding.discard(actor_id)

	def hook(self, actor: Any) -> None:
		"""An actor that runs concerns in the shared market counts its rivals and is counted as one."""
		registry = self.registry
		if not hasattr(type(actor), "rivals_of"):
			return
		actor.rivals_of = self.rivals_of
		if hasattr(type(actor), "on_capacity_change"):
			actor.on_capacity_change = self.note_capacity_change
		if hasattr(type(actor), "find_actor"):
			actor.find_actor = registry.get
		if hasattr(type(actor), "command_table"):
			actor.command_table = registry.extensions.commands
		watch = ConcernWatch(actor.actor_id, self._holders, self.version, self._totals, actor.record, self.concern_set_version)
		actor.record.business.watch = watch
		watch()

	def note_capacity_change(self, firm_id: str) -> None:
		"""A firm has changed the size it runs a concern at: the totals take its new sizes."""
		self.version[0] += 1
		self._totals.sync(firm_id, self.registry.actors[firm_id].record)

	def capacity_in(self, node_id: str) -> float:
		"""Founding sizes of one concern that every active firm runs, summed."""
		return self._totals.size_by_node.get(node_id, 0.0)

	def concerns_in(self, category: str, nodes: Dict[str, Any]) -> float:
		"""Founding sizes of concerns of goods category `category` that actors operate, summed over operators."""
		return self._totals.size_of_category(category, nodes)

	def market_operators(self) -> List[Any]:
		"""Every actor still in business that runs concerns in the shared market: firms and players."""
		actors = self.registry.actors
		return [actor for actor in (actors[actor_id] for actor_id in self.registry.sorted_ids())
				if hasattr(type(actor), "rivals_of") and actor.record.exited_year is None]

	def proven_concerns(self, world: Any) -> List[str]:
		"""Concerns some player has shown to pay, the founder's and every player actor's, in id order."""
		proven = set(world.concerns.proven_concerns())
		for actor in self.registry.actors.values():
			shown = getattr(actor, "proven_concerns", None)
			if shown is not None and actor.record.exited_year is None:
				proven.update(shown(world))
		return sorted(proven)

	def active_firms(self) -> List[Firm]:
		return [firm for firm in self.registry.of_kind("firm") if firm.record.exited_year is None]  # type: ignore[misc]

	def concerns_of_active_firms(self) -> Set[str]:
		"""Every concern some firm that has not exited runs, read from the holder index."""
		actors = self.registry.actors
		return {node_id for node_id, holders in self._holders.items()
				if any(actors[actor_id].kind == "firm" and actors[actor_id].record.exited_year is None
					   for actor_id in holders)}

	def concern_nodes(self) -> List[str]:
		"""Every concern some actor in business runs."""
		return [node_id for node_id, holders in self._holders.items() if holders]

	def operators_of(self, node_id: str) -> List[Any]:
		"""Actors in business that run a concern, in id order."""
		actors = self.registry.actors
		return [actors[actor_id] for actor_id in sorted(self._holders.get(node_id, ()))
				if actors[actor_id].record.exited_year is None]

	def rivals_of(self, node_id: str, asking_id: str) -> float:
		"""Founding sizes of the concern that other operators run in its market, the founder's included."""
		operators = self._holders.get(node_id, ())
		count = self.capacity_in(node_id)
		if asking_id in operators:
			count -= self.registry.actors[asking_id].holdings.capacity_of(node_id)
		world = self.registry.world
		founder_operates = world is not None and world.knowledge.is_public(node_id)
		return count + (1 if founder_operates else 0)
