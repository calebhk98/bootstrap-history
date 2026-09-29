"""What an actor can see and price: a read-only view of the simulated world.

Actors never touch `Sim` directly. They ask this view, which keeps them free
of the engine and lets a test or a second scenario supply another one.
"""
import hashlib
import random
from typing import Any, Dict, List, Optional, Set

from .tuning import OBSERVATION_RANGE_KM, PROOF_YEARS, SECRET_EXPOSURE


class SimWorld:
	"""The `Sim`'s answers to the questions actors ask."""

	def __init__(self, sim: Any) -> None:
		self._sim = sim
		# Answers that hold for the whole of one yearly turn.
		self._memo: Dict[str, Any] = {}

	def _once(self, key: str, compute: Any) -> Any:
		if key not in self._memo:
			self._memo[key] = compute()
		return self._memo[key]

	@property
	def year(self) -> int:
		return self._sim.state.scenario.year

	@property
	def nodes(self) -> Dict[str, Any]:
		return self._sim.nodes

	@property
	def civ_id(self) -> str:
		return str(self._sim.civ.get("id"))

	def baseline_knowledge(self) -> Set[str]:
		"""What the society already knows without the founder."""
		return self._once("baseline", lambda: set(self._sim.state.projects.granted))

	def founder_inventions(self) -> List[str]:
		"""Everything the founder has completed that the society did not have."""
		def compute() -> List[str]:
			projects = self._sim.state.projects
			return sorted(projects.done - projects.granted)
		return self._once("inventions", compute)

	def demonstrated(self) -> Set[str]:
		return self._once("demonstrated", lambda: set(self.founder_inventions()))

	def is_public(self, node_id: str) -> bool:
		return node_id in self._sim.state.projects.operating

	def exposure(self, node_id: str, location: Optional[str]) -> float:
		"""How much of an invention an observer at `location` can learn, 0..1."""
		visibility = 1.0 if self.is_public(node_id) else SECRET_EXPOSURE
		if location is None:
			return visibility
		distance = self._sim.distance_to_tile_km(location)
		return visibility / (1.0 + distance / OBSERVATION_RANGE_KM)

	def state_weights(self) -> Dict[str, float]:
		return self._once("weights", self._sim.state_trait_weights)

	def society_output(self) -> float:
		"""Yearly value of the working population's labour at the unskilled wage."""
		sim = self._sim
		return self._once("output", lambda: (
			sim.population.working_age * sim.HOURS_PER_PERSON_YEAR * sim.wage_per_hour("labourer")))

	def state_revenue(self) -> float:
		sim = self._sim
		return self._once("revenue", lambda: (
			self.society_output() * float(sim.civ["starting_tax_share"]) * sim.state_capacity))

	def wage_per_hour(self, trade: str) -> float:
		return self._sim.wage_per_hour(trade)

	@property
	def hours_per_person_year(self) -> float:
		return self._sim.HOURS_PER_PERSON_YEAR

	def copy_cost(self, node_id: str) -> float:
		"""Money the pioneer's version of this work costs, labour included."""
		return self._sim.project_cost(node_id)

	def copy_risk(self, node_id: str) -> float:
		return self._sim.effective_risk(node_id)

	def concern_gross(self, node_id: str) -> float:
		"""Yearly takings of the founder's concern once it has ramped up."""
		sim = self._sim
		return sim.concern_takings(node_id, 1.0) * sim.goods_market_factor(node_id)

	def concern_margin(self, node_id: str) -> float:
		"""Yearly profit of the founder's concern once it has ramped up."""
		return self.concern_gross(node_id) - self.upkeep(node_id)

	def proven_concerns(self) -> List[str]:
		"""Founder concerns that have been running at a profit long enough to be believed."""
		sim = self._sim
		projects = sim.state.projects
		proven = []
		for node_id in sorted(projects.operating):
			if node_id in projects.granted or not sim.is_venture(node_id):
				continue
			opened = (projects.opened_year or {}).get(node_id, self.year)
			if self.year - opened >= PROOF_YEARS and self.concern_margin(node_id) > 0:
				proven.append(node_id)
		return proven

	def concern_takings(self, node_id: str, opened_year: int) -> float:
		sim = self._sim
		ramp = min(1.0, (self.year - opened_year + 1) / sim.cfg["revenue_ramp_years"])
		return sim.concern_takings(node_id, ramp)

	def upkeep(self, node_id: str) -> float:
		return self.nodes[node_id]["up"] * self._sim.price_index

	def rng_for(self, *parts: Any) -> random.Random:
		"""A random stream keyed by its inputs, so actors never disturb the world's own."""
		digest = hashlib.sha256("|".join(str(part) for part in parts).encode()).hexdigest()
		return random.Random(int(digest[:16], 16))
