"""Where and when the actors stand: the year, the tree, the civilisation, the edges, the shared random streams, the home
government and the great-circle distance between places."""
import hashlib
import random
from typing import Any, Dict

from sim.geography.api import distance_between_places

from .world_memo import once


class Setting:
	"""The simulated world's own state that every question starts from. `world` is the root that hands out the parts."""

	def __init__(self, world: Any) -> None:
		self.world = world
		self._memo: Dict[str, Any] = {}

	@property
	def needs(self) -> Any:
		return self.world.needs

	@property
	def year(self) -> int:
		return self.needs.year()

	@property
	def nodes(self) -> Dict[str, Any]:
		return self.needs.tree_nodes()

	@property
	def civ_id(self) -> str:
		return str(self.needs.civilisation().get("id"))

	def edge(self, name: str) -> Any:
		"""The named edge a posting names when its other side is not an actor."""
		return self.world.cast.edge(name)

	def state_weights(self) -> Dict[str, float]:
		return once(self._memo, "weights", self.needs.state_trait_weights)

	def government(self) -> Any:
		"""The government actor of the founder's civilisation."""
		return self.world.cast.state_treasury()

	def distance_km(self, place_a: Any, place_b: Any) -> float:
		"""Great-circle kilometres between two places; 0 when either is not on the map. None is where the founder operates from."""
		founder_place = str(self.needs.base_tile())
		return distance_between_places(place_a if place_a is not None else founder_place,
									   place_b if place_b is not None else founder_place)

	def rng_for(self, *parts: Any) -> random.Random:
		"""A random stream keyed by its inputs, so actors never disturb the world's own."""
		digest = hashlib.sha256("|".join(str(part) for part in parts).encode()).hexdigest()
		return random.Random(int(digest[:16], 16))
