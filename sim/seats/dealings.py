"""A seat deals as any actor does: it patents what it made, makes offers, answers the offers it was made, issues and buys shares.
The seat's stored dealings (`SeatsSeat`: patents, shares held and issued, offers) are this module's; the exchange does the moving,
and the actors module applies the commands that address it to a seat (sim/actors/seat_exchange.py)."""
from typing import Any, Dict, List

from sim.agents.api import patent


class Dealings:

    def seat_dealings(self, seat_id: str) -> Any:
        """The seat's stored dealings, the record the seat's party in an exchange writes through (the party is the actors')."""
        return self._slots()[seat_id]

    def seats_holding_patent(self, node_id: str) -> List[str]:
        """Ids of the seats that hold a patent on `node_id`, in joining order."""
        return [seat_id for seat_id, slot in self._slots().items() if node_id in slot.patents]

    def dealings_listing(self) -> Dict[str, Any]:
        """What the acting seat holds in patents and shares, and the offers waiting for it."""
        seat = self.seat
        year = self.needs.year()
        return {"patents": {node_id: dict(entry, live=patent.live(entry, year)) for node_id, entry in sorted(seat.patents.items())},
                "shares_held": dict(sorted(seat.shares_held.items())),
                "shares_issued": seat.shares_issued,
                "offers": [dict(offer) for offer in seat.offers]}
