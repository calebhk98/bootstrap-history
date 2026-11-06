"""What the world says about how each invention was disclosed (kept secret, licensed, published)."""
from typing import Any

from sim.agents.api import PROOF_YEARS, SECRET_EXPOSURE, licence
from sim.ledger.api import UNPAID_CHARGE_KIND, PayActor
from sim.refusal import Refusal, cause_of
from sim.reporting.api import RecordEvent

from sim.seats.api import (base_visibility, builders_of, disclosure_modes, most_open_mode, seat_royalties_due, seat_royalties_paid,
						   years_to_be_believed)


class Disclosure:
	"""Reads the founder's choice per invention. `world` is the root that hands out the parts."""

	def __init__(self, world: Any) -> None:
		self.world = world

	@property
	def needs(self) -> Any:
		return self.world.needs

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
		return base_visibility(self.disclosure_mode(node_id), self.world.knowledge.is_public(node_id),
							   self.needs.copy_difficulty[node_id], SECRET_EXPOSURE)

	def proof_years(self, node_id: str) -> float:
		"""Years a concern must run at a profit before outsiders believe it."""
		return years_to_be_believed(self.disclosure_mode(node_id), PROOF_YEARS, self.secret_exposure(node_id))

	def state_grants_patents(self, actor: Any) -> bool:
		"""Whether the state holds a technology that declares the `patent_grant` mechanic, in its own
		knowledge or in what its society already knows."""
		state = self.world.setting.government()
		return any(state.knows(node_id, self.world) for node_id in self.needs.mechanic["patent_grant"])

	def patent_entry(self, node_id: str) -> Any:
		"""The live patent on an invention as {"holder", "expires", "licensees"}, or None."""
		needs = self.needs
		holders = self.world.registry.patent_holders(node_id) + [self.world.seat_book.seat_party(seat_id) for seat_id in needs.seats_holding_patent(node_id)]
		return licence.live_patent(holders, node_id, self.world.setting.year)

	def _holder_of(self, holder_id: str) -> Any:
		"""The actor with this id: one in the registry, else a seat."""
		seat_book = self.world.seat_book
		return self.world.registry.get(holder_id) or (seat_book.seat_party(holder_id) if holder_id in self.needs.seat_list()["joined"] else None)

	def collect_royalty(self, firm: Any, node_id: str, takings: float) -> float:
		"""The royalty a licensed firm's takings owe each seat that licensed it the invention, never more than its
		purse; the amount paid."""
		needs = self.needs
		paid = 0.0
		owed = seat_royalties_due(needs.techniques_by_seat(), node_id, firm.actor_id, takings, needs.disclosures.__getitem__)
		for seat_id, due in seat_royalties_paid(owed, firm.money):
			refusal = needs.send(PayActor(firm.actor_id, seat_id, due, "licence"))
			if isinstance(refusal, Refusal):   # the firm could not cover it: not paid, and said so
				needs.send(RecordEvent.of(UNPAID_CHARGE_KIND, "could not pay %s a licence royalty: %s" % (seat_id, refusal),
				                          edge=seat_id, amount=due, purpose="licence", cause=cause_of(refusal)))
				continue
			paid += due
		return paid + licence.collect_patent_royalty(self.world, self._holder_of, firm, node_id, takings)
