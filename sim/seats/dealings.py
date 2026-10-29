"""A seat deals as any actor does: it patents what it made, makes offers, answers the offers it was made, issues
and buys shares. The exchange does the moving; this only addresses it to a seat.

Offers to or from a seat are limited to what moves cleanly between a seat and an actor: money, patents, licences
(with a royalty) and shares. A concern is sold with `sell concern`, and know-how is licensed with `disclose`."""
from typing import Any, Dict

from sim.agents.api import CommandRejected, exchange, patent

from . import dealing_rules
from .commands import AnswerOffer, ApplyForPatent, MakeOffer


class Dealings:

    def dealing_party(self) -> Any:
        """The acting seat as a party to an exchange, with what each concern it runs earns a year (what a taker values)."""
        world = self.needs.actor_world()
        projects = self.needs.legacy_projects()
        margins = {node_id: world.concern_margin(node_id) for node_id in sorted(projects.operating - self.needs.techniques_granted())}
        return self.needs.seat_party_with_margins(self.clock.acting_seat, margins)

    def find_dealer(self, actor_id: Any) -> Any:
        """The actor with this id: a seat that is playing, else one in the registry."""
        if isinstance(actor_id, str) and actor_id in self.needs.legacy_seats():
            return self.needs.seat_party[actor_id]
        return self.needs.cast().get(actor_id) if isinstance(actor_id, str) else None

    def _refuse_unsupported(self, side: Dict[str, Any]) -> None:
        reason = dealing_rules.unsupported_reason(side)
        if reason:
            raise CommandRejected(reason)

    def apply_for_patent(self, command: ApplyForPatent) -> Dict[str, Any]:
        """Apply for the exclusive right to an invention the seat holds."""
        try:
            note = patent.apply(self.dealing_party(), str(command.node_id or ""), self.needs.actor_world())
        except CommandRejected as reason:
            return {"ok": False, "error": str(reason)}
        return {"ok": True, "note": note, "patents": self.dealings_listing()["patents"]}

    def make_offer(self, command: MakeOffer) -> Dict[str, Any]:
        """Offer another actor or seat things for things; it sits in their offers until answered."""
        try:
            for side in (command.give, command.take):
                if isinstance(side, dict):
                    self._refuse_unsupported(side)
            party, receiver = self.dealing_party(), self.find_dealer(command.to)
            made = exchange.make_offer(party, receiver, command.give or {}, command.take or {}, self.needs.actor_world())
        except (CommandRejected, ValueError, TypeError) as reason:
            return {"ok": False, "error": str(reason)}
        return {"ok": True, "offered": made["id"], "to": made["to"], "expires": made["expires"]}

    def answer_offer(self, command: AnswerOffer) -> Dict[str, Any]:
        """Accept or decline an offer made to this seat."""
        party = self.dealing_party()
        try:
            held = exchange.find_offer(party, command.offer_id)
            for side in (held["give"], held["take"]):
                self._refuse_unsupported(side)
            if command.accept:
                note = exchange.accept(party, command.offer_id, self.find_dealer, self.needs.actor_world())
            else:
                note = exchange.decline(party, command.offer_id)
        except CommandRejected as reason:
            return {"ok": False, "error": str(reason)}
        return {"ok": True, "note": note, "offers": self.dealings_listing()["offers"]}

    def dealings_listing(self) -> Dict[str, Any]:
        """What the acting seat holds in patents and shares, and the offers waiting for it."""
        party = self.dealing_party()
        year = self.needs.year()
        return {"patents": {node_id: dict(entry, live=patent.live(entry, year)) for node_id, entry in sorted(party.record.patents.items())},
                "shares_held": dict(sorted(party.record.holdings.items())),
                "shares_issued": party.record.issued,
                "offers": [dict(offer) for offer in party.record.offers]}
