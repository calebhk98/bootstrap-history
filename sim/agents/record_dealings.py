"""How an actor's record changes its patents, shares and offers: each step is a rule of `dealing_figures.py` applied to the record's figures.
A seat's record (`household_party.py`) has the same methods and sends the seats module the matching command instead."""
from typing import Any, Dict, List

from . import dealing_figures as figures


class RecordDealings:
	"""The methods an exchange uses to change an actor's record; `own_id` of the issuer decides whether shares are the actor's own issue."""

	def _hold_patents(self, patents: Dict[str, Any]) -> None:
		self.patents.clear()
		self.patents.update(patents)

	def release_patent(self, node_id: str, taker_id: str) -> Dict[str, Any]:
		"""The right on `node_id` leaves the record, with `taker_id` struck from its licensees; answers it."""
		patents, entry = figures.release_patent(self.patents, node_id, taker_id)
		self._hold_patents(patents)
		return entry

	def receive_patent(self, node_id: str, entry: Dict[str, Any]) -> None:
		self._hold_patents(figures.receive_patent(self.patents, node_id, entry))

	def add_licensee(self, node_id: str, licensee_id: str) -> None:
		self._hold_patents(figures.add_licensee(self.patents, node_id, licensee_id))

	def give_shares(self, issuer_id: str, share: float, own_issue: bool) -> None:
		self.issued, self.shares_held = figures.give_shares(self.issued, self.shares_held, issuer_id, share, own_issue)

	def take_shares(self, issuer_id: str, share: float, own_issue: bool) -> None:
		self.issued, self.shares_held = figures.take_shares(self.issued, self.shares_held, issuer_id, share, own_issue)

	def keep_offer(self, offer: Dict[str, Any]) -> None:
		self.offers[:] = figures.keep_offer(self.offers, offer)

	def drop_offer(self, offer_id: str) -> None:
		self.offers[:] = figures.drop_offer(self.offers, offer_id)

	def drop_lapsed_offers(self, year: int) -> List[str]:
		"""Drop the offers past their last year; answers their ids."""
		self.offers[:], lapsed = figures.drop_lapsed_offers(self.offers, year)
		return lapsed

	def next_offer_serial(self) -> int:
		"""Count one more offer made; answers the count."""
		self.offer_serial += 1
		return self.offer_serial
