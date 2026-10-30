"""A seat deals as any actor does: it patents what it made, makes offers, answers the offers it was made, issues and buys shares.
The seat's stored dealings (`SeatsSeat`: patents, shares held and issued, offers) are this module's; the exchange does the moving,
and the actors module applies the commands that address it to a seat (sim/actors/seat_exchange.py)."""
from typing import Any, Dict, List

from sim.agents.api import patent
from sim.agents.tracked import plain

DEALING_FIELDS = ("patents", "shares_held", "shares_issued", "offers", "offer_serial")


class Dealings:

    def seat_dealings(self, seat_id: str) -> Dict[str, Any]:
        """A copy of the seat's stored dealings by field (`DEALING_FIELDS`); the seat's party in an exchange changes them by `SetDealing`."""
        slot = self._slots()[seat_id]
        return {name: plain(getattr(slot, name)) for name in DEALING_FIELDS}

    def set_dealing(self, command: Any) -> None:
        """The named seat's patents, shares held, shares issued, offers or offer count become the figure sent."""
        if command.field not in DEALING_FIELDS:
            raise KeyError("a seat's dealings have no field " + command.field)
        setattr(self._slots()[command.seat_id], command.field, plain(command.value))

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
