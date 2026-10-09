"""What the world view says about how each invention was disclosed (kept secret, licensed, published)."""
from typing import Any

from sim.agents.api import PROOF_YEARS, SECRET_EXPOSURE, ledger, licence

from . import seat_builds
from .visibility import base_visibility, most_open_mode


class DisclosureView:
	"""Mixed into `SimWorld`: reads the founder's choice per invention."""

	_sim: Any

	def disclosure_mode(self, node_id: str) -> str:
		"""What the makers of an invention chose: the widest choice any seat that built it made."""
		seats = self._sim.state.seats
		if not seat_builds.builders_of(seats, node_id):
			return str(self._sim.disclosure_of(node_id)["mode"])
		return most_open_mode(seat_builds.disclosure_modes(seats, node_id))

	def secret_exposure(self, node_id: str) -> float:
		"""Share of full visibility outsiders get of a kept secret: the more trades and materials
		the know-how needs, the less of it can be copied from what is seen."""
		return SECRET_EXPOSURE / self._sim.copy_difficulty(node_id)

	def base_visibility(self, node_id: str) -> float:
		"""How much of an invention can be learned before distance counts, 0..1."""
		return base_visibility(self.disclosure_mode(node_id), self.is_public(node_id),  # type: ignore[attr-defined]
							   self._sim.copy_difficulty(node_id), SECRET_EXPOSURE)

	def proof_years(self, node_id: str) -> float:
		"""Years a concern must run at a profit before outsiders believe it."""
		mode = self.disclosure_mode(node_id)
		if mode == "publish":
			return 0.0
		if mode in ("secret", "license"):
			return PROOF_YEARS / self.secret_exposure(node_id)
		return float(PROOF_YEARS)

	def seat_parties(self) -> Any:
		"""Every seat as an actor, by seat id: the founder and other players hold patents and shares."""
		return self._sim.seat_parties()

	def state_grants_patents(self, actor: Any) -> bool:
		"""Whether the state holds a technology that declares the `patent_grant` mechanic, in its own
		knowledge or in what its society already knows."""
		state = self.government()
		return any(state.knows(node_id, self) for node_id in self._sim.nodes_with_mechanic("patent_grant"))

	def patent_entry(self, node_id: str) -> Any:
		"""The live patent on an invention as {"holder", "expires", "licensees"}, or None."""
		sim = self._sim
		holders = list(sim.actors.actors.values()) + [sim.seat_party(seat_id) for seat_id, seat in sim.state.seats.items()
													  if node_id in seat.holdings.patents]
		return licence.live_patent(holders, node_id, self.year)

	def _holder(self, holder_id: str) -> Any:
		"""The actor with this id: one in the registry, else a seat."""
		sim = self._sim
		return sim.actors.get(holder_id) or (sim.seat_party(holder_id) if holder_id in sim.state.seats else None)

	def collect_royalty(self, firm: Any, node_id: str, takings: float) -> float:
		"""The royalty a licensed firm's takings owe each seat that licensed it the invention; the amount paid."""
		sim = self._sim
		paid = 0.0
		for seat_id in seat_builds.licensors_of(sim.state.seats, node_id, firm.actor_id):
			record = sim.state.seats[seat_id].projects.disclosures[node_id]["licensees"][firm.actor_id]
			due = licence.royalty_due(takings, record)
			if due > 0.0:
				ledger.transfer(firm, sim.seat_party(seat_id), due, "licence")
				paid += due
		return paid + licence.collect_patent_royalty(self, self._holder, firm, node_id, takings)
