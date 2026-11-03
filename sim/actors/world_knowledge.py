"""What the society knows, what can be seen made, and how far an onlooker sees it."""
from typing import Any, Dict, List, Optional, Set

from sim.agents.api import OBSERVATION_RANGE_KM, SECRET_EXPOSURE
from sim.seats import api as seats_api

from .world_memo import once


class Knowledge:
	"""Knowledge held by the society, the seats and the actors, and its visibility."""

	def __init__(self, world: Any) -> None:
		self.world = world
		self._memo: Dict[str, Any] = {}

	@property
	def needs(self) -> Any:
		return self.world.needs

	def baseline_knowledge(self) -> Set[str]:
		"""What the society already knows without the founder."""
		return once(self._memo, "baseline", lambda: set(self.needs.techniques_granted()))

	def founder_inventions(self) -> List[str]:
		"""Everything any seat has completed that the society did not have."""
		return once(self._memo, "inventions", lambda: sorted(seats_api.built_by_any(self.needs.techniques_by_seat())))

	def actor_held(self) -> Dict[str, List[Any]]:
		"""Every node an active actor holds beyond what the society already knew, with its holders in id order."""
		def compute() -> Dict[str, List[Any]]:
			baseline = self.baseline_knowledge()
			nodes = self.world.setting.nodes
			held: Dict[str, List[Any]] = {}
			for actor in sorted(self.world.registry.actors.values(), key=lambda actor: actor.identity()):
				if actor.record.exited_year is not None:
					continue
				for node_id in sorted(actor.knowledge):
					if node_id in nodes and node_id not in baseline:
						held.setdefault(node_id, []).append(actor)
			return held
		return once(self._memo, "actor_held", compute)

	def demonstrated(self) -> Set[str]:
		"""What can be seen made: every seat's builds and every actor's own knowledge."""
		return once(self._memo, "demonstrated", lambda: set(self.founder_inventions()) | set(self.actor_held()))

	def knowledge_half_life_years(self) -> float:
		return self.needs.knowledge_half_life_years()

	def knowledge_visibility(self, node_id: str, distance_km: float) -> float:
		"""How much of a node some actor holds shows `distance_km` away: its own opacity, public if a seat runs it."""
		visibility = seats_api.base_visibility("default", self.is_public(node_id), self.needs.copy_difficulty[node_id], SECRET_EXPOSURE)
		return seats_api.seen_from(visibility, distance_km, OBSERVATION_RANGE_KM)

	def is_public(self, node_id: str) -> bool:
		"""Whether some seat runs it as a concern, where anyone can see it."""
		return seats_api.operating_anywhere(self.needs.operating_by_seat(), node_id)

	def exposure(self, node_id: str, location: Optional[str]) -> float:
		"""How much of an invention an observer at `location` can learn, 0..1: the best view of any seat
		that built it, from that seat's own place (the acting seat's when no seat built it)."""
		needs = self.needs
		distance_km = self.world.setting.distance_km
		builders = seats_api.builders_of(needs.techniques_by_seat(), node_id)
		holders = self.actor_held().get(node_id, [])
		if not builders and not holders:
			builders = [needs.acting_seat()]
		public = self.is_public(node_id)
		best = 0.0
		for seat_id in builders:
			mode = (needs.disclosures[seat_id].get(node_id) or {}).get("mode", "default")
			visibility = seats_api.base_visibility(mode, public, needs.copy_difficulty[node_id], SECRET_EXPOSURE)
			if location is not None:
				visibility = seats_api.seen_from(visibility, distance_km(location, needs.seat_place[seat_id]), OBSERVATION_RANGE_KM)
			best = max(best, visibility)
		for holder in holders:
			best = max(best, self.knowledge_visibility(
				node_id, distance_km(holder.location(), location) if location is not None else 0.0))
		return best
