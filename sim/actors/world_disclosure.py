"""What the world view says about how each invention was disclosed (kept secret, licensed, published)."""
from typing import Any

from sim.agents.api import PROOF_YEARS, SECRET_EXPOSURE, licence
from sim.ledger.api import PayActor

from sim.seats.api import (base_visibility, builders_of, disclosure_modes, most_open_mode, seat_royalties_due, seat_royalties_paid,
						   years_to_be_believed)


class DisclosureView:
	"""Mixed into `ActorWorld`: reads the founder's choice per invention."""

	needs: Any
	registry: Any

	def disclosure_mode(self, node_id: str) -> str:
		"""What the makers of an invention chose: the widest choice any seat that built it made."""
		techniques = self.needs.techniques_by_seat()
		if not builders_of(techniques, node_id):
			return str(self.needs.disclosure[node_id]["mode"])
		return most_open_mode(disclosure_modes(techniques, node_id, self.needs.disclosures.__getitem__))

	def secret_exposure(self, node_id: str) -> float:
		"""Share of full visibility outsiders get of a kept secret: the more trades and materials
		the know-how needs, the less of it can be copied from what is seen."""
		return SECRET_EXPOSURE / self.needs.copy_difficulty[node_id]

	def base_visibility(self, node_id: str) -> float:
		"""How much of an invention can be learned before distance counts, 0..1."""
		return base_visibility(self.disclosure_mode(node_id), self.is_public(node_id),  # type: ignore[attr-defined]
							   self.needs.copy_difficulty[node_id], SECRET_EXPOSURE)

	def proof_years(self, node_id: str) -> float:
		"""Years a concern must run at a profit before outsiders believe it."""
		return years_to_be_believed(self.disclosure_mode(node_id), PROOF_YEARS, self.secret_exposure(node_id))

	def seat_parties(self) -> Any:
		"""Every seat as an actor, by seat id: the founder and other players hold patents and shares."""
		return {seat_id: self.needs.seat_party[seat_id] for seat_id in self.needs.seat_list()["joined"]}

	def state_grants_patents(self, actor: Any) -> bool:
		"""Whether the state holds a technology that declares the `patent_grant` mechanic, in its own
		knowledge or in what its society already knows."""
		state = self.government()
		return any(state.knows(node_id, self) for node_id in self.needs.mechanic["patent_grant"])

	def patent_entry(self, node_id: str) -> Any:
		"""The live patent on an invention as {"holder", "expires", "licensees"}, or None."""
		needs = self.needs
		holders = self.registry.patent_holders(node_id) + [needs.seat_party[seat_id] for seat_id in needs.seats_holding_patent(node_id)]
		return licence.live_patent(holders, node_id, self.year)

	def _holder(self, holder_id: str) -> Any:
		"""The actor with this id: one in the registry, else a seat."""
		needs = self.needs
		return self.registry.get(holder_id) or (needs.seat_party[holder_id] if holder_id in needs.seat_list()["joined"] else None)

	def collect_royalty(self, firm: Any, node_id: str, takings: float) -> float:
		"""The royalty a licensed firm's takings owe each seat that licensed it the invention, never more than its
		purse; the amount paid."""
		needs = self.needs
		paid = 0.0
		owed = seat_royalties_due(needs.techniques_by_seat(), node_id, firm.actor_id, takings, needs.disclosures.__getitem__)
		for seat_id, due in seat_royalties_paid(owed, firm.money):
			needs.send(PayActor(firm.actor_id, seat_id, due, "licence"))
			paid += due
		return paid + licence.collect_patent_royalty(self, self._holder, firm, node_id, takings)
