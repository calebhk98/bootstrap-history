"""A seat deals as any actor does: it patents what it made, makes offers, answers the offers it was made, issues and buys shares.
The seat's stored dealings (`SeatsSeat`: patents, shares held and issued, offers) are this module's; the exchange does the moving,
and the actors module applies the commands that address it to a seat (sim/actors/seat_exchange.py)."""
from typing import Any, Dict, List

from sim.agents.api import dealing_figures, patent, plain
from sim.assembly.api import Part

DEALING_FIELDS = ("patents", "shares_held", "shares_issued", "offers", "offer_serial")


class Dealings(Part):

    def seat_dealings(self, seat_id: str) -> Dict[str, Any]:
        """A copy of the seat's stored dealings by field (`DEALING_FIELDS`); the seat's party in an exchange changes them by the commands of this module."""
        slot = self.parts.run.slots()[seat_id]
        return {name: plain(getattr(slot, name)) for name in DEALING_FIELDS}

    def release_patent(self, command: Any) -> Dict[str, Any]:
        """The seat's right on the node goes to the taker: out of its patents, the taker struck from the licensees. Answers the right."""
        slot = self.parts.run.slots()[command.seat_id]
        slot.patents, entry = dealing_figures.release_patent(slot.patents, command.node_id, command.taker_id)
        return entry

    def receive_patent(self, command: Any) -> None:
        slot = self.parts.run.slots()[command.seat_id]
        slot.patents = dealing_figures.receive_patent(slot.patents, command.node_id, command.entry)

    def add_licensee(self, command: Any) -> None:
        slot = self.parts.run.slots()[command.seat_id]
        slot.patents = dealing_figures.add_licensee(slot.patents, command.node_id, command.licensee_id)

    def give_shares(self, command: Any) -> None:
        slot = self.parts.run.slots()[command.seat_id]
        slot.shares_issued, slot.shares_held = dealing_figures.give_shares(
            slot.shares_issued, slot.shares_held, command.issuer_id, command.share, command.own_issue)

    def take_shares(self, command: Any) -> None:
        slot = self.parts.run.slots()[command.seat_id]
        slot.shares_issued, slot.shares_held = dealing_figures.take_shares(
            slot.shares_issued, slot.shares_held, command.issuer_id, command.share, command.own_issue)

    def keep_offer(self, command: Any) -> None:
        slot = self.parts.run.slots()[command.seat_id]
        slot.offers = dealing_figures.keep_offer(slot.offers, command.offer)

    def drop_offer(self, command: Any) -> None:
        slot = self.parts.run.slots()[command.seat_id]
        slot.offers = dealing_figures.drop_offer(slot.offers, command.offer_id)

    def drop_lapsed_offers(self, command: Any) -> List[str]:
        slot = self.parts.run.slots()[command.seat_id]
        slot.offers, lapsed = dealing_figures.drop_lapsed_offers(slot.offers, command.year)
        return lapsed

    def next_offer_serial(self, command: Any) -> int:
        slot = self.parts.run.slots()[command.seat_id]
        slot.offer_serial += 1
        return slot.offer_serial

    def seats_holding_patent(self, node_id: str) -> List[str]:
        """Ids of the seats that hold a patent on `node_id`, in joining order."""
        return [seat_id for seat_id, slot in self.parts.run.slots().items() if node_id in slot.patents]

    def dealings_listing(self) -> Dict[str, Any]:
        """What the acting seat holds in patents and shares, and the offers waiting for it."""
        seat = self.seat
        year = self.needs.year()
        return {"patents": {node_id: dict(entry, live=patent.live(entry, year)) for node_id, entry in sorted(seat.patents.items())},
                "shares_held": dict(sorted(seat.shares_held.items())),
                "shares_issued": seat.shares_issued,
                "offers": [dict(offer) for offer in seat.offers]}
