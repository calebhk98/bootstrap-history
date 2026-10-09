"""What the world view says about how each invention was disclosed (kept secret, licensed, published)."""
from typing import Any

from sim.agents.api import PROOF_YEARS, SECRET_EXPOSURE, ledger, licence


class DisclosureView:
	"""Mixed into `SimWorld`: reads the founder's choice per invention."""

	_sim: Any

	def disclosure_mode(self, node_id: str) -> str:
		return str(self._sim.disclosure_of(node_id)["mode"])

	def secret_exposure(self, node_id: str) -> float:
		"""Share of full visibility outsiders get of a kept secret: the more trades and materials
		the know-how needs, the less of it can be copied from what is seen."""
		return SECRET_EXPOSURE / self._sim.copy_difficulty(node_id)

	def base_visibility(self, node_id: str) -> float:
		"""How much of an invention can be learned before distance counts, 0..1."""
		mode = self.disclosure_mode(node_id)
		if mode == "publish":
			return 1.0
		if mode in ("secret", "license"):
			return self.secret_exposure(node_id)
		return 1.0 if self.is_public(node_id) else SECRET_EXPOSURE

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
		holders = list(self._sim.actors.actors.values()) + list(self._sim.seat_parties().values())
		return licence.live_patent(holders, node_id, self.year)

	def collect_royalty(self, firm: Any, node_id: str, takings: float) -> float:
		"""The founder's royalty on a licensed firm's takings; the amount paid."""
		record = self._sim.disclosure_of(node_id)["licensees"].get(firm.actor_id)
		if not record:
			return 0.0
		due = licence.royalty_due(takings, record)
		if due > 0.0:
			ledger.transfer(firm, self._sim.household, due, "licence")
		return due
