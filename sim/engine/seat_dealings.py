"""A seat deals as any actor does: it patents what it made, makes offers, answers the offers it was made, issues
and buys shares. The exchange does the moving; this only addresses it to a seat.

Offers to or from a seat are limited to what moves cleanly between a seat and an actor: money, patents, licences
(with a royalty) and shares. A concern is sold with `sell concern`, and know-how is licensed with `disclose`."""
from typing import Any, Dict, Optional

from sim.agents.api import CommandRejected, exchange, patent

from .agents_port import SimWorld

SEAT_DEALT_KEYS = ("money", "patent", "licence", "royalty", "shares")


class SeatDealingsMixin:

    def dealing_party(self, seat_id: Optional[str] = None) -> Any:
        """The seat as a party to an exchange, with what each concern it runs earns a year (what a taker values)."""
        seat_id = seat_id or self.state.acting_seat
        world = SimWorld(self)
        with self.act_as(seat_id):
            projects = self.state.projects
            margins = {node_id: world.concern_margin(node_id) for node_id in sorted(projects.operating - projects.granted)}
        return self.seat_party(seat_id, margins)

    def find_dealer(self, actor_id: Any) -> Any:
        """The actor with this id: a seat that is playing, else one in the registry."""
        if isinstance(actor_id, str) and actor_id in self.state.seats:
            return self.seat_party(actor_id)
        return self.actors.get(actor_id) if isinstance(actor_id, str) else None

    def _refuse_unsupported(self, side: Dict[str, Any]) -> None:
        extra = sorted(set(side) - set(SEAT_DEALT_KEYS))
        if extra:
            raise CommandRejected("a seat deals in money, patents, licences, royalties and shares, not %s" % ", ".join(extra))

    def seat_patent(self, node_id: str) -> Dict[str, Any]:
        """Apply for the exclusive right to an invention the seat holds."""
        try:
            note = patent.apply(self.dealing_party(), str(node_id or ""), SimWorld(self))
        except CommandRejected as reason:
            return {"ok": False, "error": str(reason)}
        return {"ok": True, "note": note, "patents": self.dealings_listing()["patents"]}

    def seat_offer(self, to: Any, give: Any, take: Any) -> Dict[str, Any]:
        """Offer another actor or seat things for things; it sits in their offers until answered."""
        try:
            for side in (give, take):
                if isinstance(side, dict):
                    self._refuse_unsupported(side)
            party, receiver = self.dealing_party(), self.find_dealer(to)
            made = exchange.make_offer(party, receiver, give or {}, take or {}, SimWorld(self))
        except (CommandRejected, ValueError, TypeError) as reason:
            return {"ok": False, "error": str(reason)}
        return {"ok": True, "offered": made["id"], "to": made["to"], "expires": made["expires"]}

    def seat_answer(self, offer_id: Any, accept: bool) -> Dict[str, Any]:
        """Accept or decline an offer made to this seat."""
        party = self.dealing_party()
        try:
            held = exchange.find_offer(party, offer_id)
            for side in (held["give"], held["take"]):
                self._refuse_unsupported(side)
            if accept:
                note = exchange.accept(party, offer_id, self.find_dealer, SimWorld(self))
            else:
                note = exchange.decline(party, offer_id)
        except CommandRejected as reason:
            return {"ok": False, "error": str(reason)}
        return {"ok": True, "note": note, "offers": self.dealings_listing()["offers"]}

    def dealings_listing(self) -> Dict[str, Any]:
        """What the acting seat holds in patents and shares, and the offers waiting for it."""
        party = self.dealing_party()
        year = self.year
        return {"patents": {node_id: dict(entry, live=patent.live(entry, year)) for node_id, entry in sorted(party.record.patents.items())},
                "shares_held": dict(sorted(party.record.holdings.items())),
                "shares_issued": party.record.issued,
                "offers": [dict(offer) for offer in party.record.offers]}
