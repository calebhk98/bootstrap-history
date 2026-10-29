"""What a seat does with the exchange: it patents what it made, makes offers, answers the offers it was made, licenses its know-how and
sells a concern it runs. The exchange (sim/agents) does the moving; this addresses it to the seat as a party built here
(`seat_parties.py`), and answers the seats, diffusion and ventures modules in plain figures and replies, never a party.

Offers to or from a seat are limited to what moves cleanly between a seat and an actor: money, patents, licences (with a royalty) and shares
(the seats module's `dealing_rules` says which). A concern is sold with `sell concern`, and know-how is licensed with `disclose`."""
from typing import Any, Dict

from sim.agents.api import CommandRejected, exchange, exchange_sale, licence, patent
from sim.seats.api import unsupported_reason

NO_LICENSEE = "no_licensee"
TERMS_REFUSED = "terms_refused"
ALREADY_ABLE = "already_able"
GRANTED = "granted"


class SeatExchange:
    """Mixed into `Actors`."""

    needs: Any

    def dealing_party(self) -> Any:
        """The acting seat as a party to an exchange, with what each concern it runs earns a year (what a taker values)."""
        needs = self.needs
        world = self.actor_world()   # type: ignore[attr-defined]
        margins = {node_id: world.concern_margin(node_id) for node_id in sorted(needs.operating() - needs.techniques_granted())}
        return self.seat_party(needs.acting_seat(), margins)   # type: ignore[attr-defined]

    def _refuse_unsupported(self, side: Dict[str, Any]) -> None:
        reason = unsupported_reason(side)
        if reason:
            raise CommandRejected(reason)

    def apply_for_patent(self, command: Any) -> Dict[str, Any]:
        """Apply for the exclusive right to an invention the seat holds."""
        try:
            note = patent.apply(self.dealing_party(), str(command.node_id or ""), self.actor_world())   # type: ignore[attr-defined]
        except CommandRejected as reason:
            return {"ok": False, "error": str(reason)}
        return {"ok": True, "note": note, "patents": self.needs.dealings_listing()["patents"]}

    def make_offer(self, command: Any) -> Dict[str, Any]:
        """Offer another actor or seat things for things; it sits in their offers until answered."""
        try:
            for side in (command.give, command.take):
                if isinstance(side, dict):
                    self._refuse_unsupported(side)
            party, receiver = self.dealing_party(), self.find_dealer(command.to)   # type: ignore[attr-defined]
            made = exchange.make_offer(party, receiver, command.give or {}, command.take or {}, self.actor_world())   # type: ignore[attr-defined]
        except (CommandRejected, ValueError, TypeError) as reason:
            return {"ok": False, "error": str(reason)}
        return {"ok": True, "offered": made["id"], "to": made["to"], "expires": made["expires"]}

    def answer_offer(self, command: Any) -> Dict[str, Any]:
        """Accept or decline an offer made to this seat."""
        party = self.dealing_party()
        world = self.actor_world()   # type: ignore[attr-defined]
        try:
            held = exchange.find_offer(party, command.offer_id)
            for side in (held["give"], held["take"]):
                self._refuse_unsupported(side)
            if command.accept:
                note = exchange.accept(party, command.offer_id, self.find_dealer, world)   # type: ignore[attr-defined]
            else:
                note = exchange.decline(party, command.offer_id)
        except CommandRejected as reason:
            return {"ok": False, "error": str(reason)}
        return {"ok": True, "note": note, "offers": self.needs.dealings_listing()["offers"]}

    def grant_licence(self, command: Any) -> Dict[str, Any]:
        """License `command.node_id` from the acting seat to `command.licensee`, a firm, the state or another player. Answers
        {"status": one of GRANTED, NO_LICENSEE, TERMS_REFUSED (with the `problem` text) or ALREADY_ABLE}."""
        needs = self.needs
        acting = needs.acting_seat()
        licensee_id = command.licensee
        licensee = self.cast().get(licensee_id) if licensee_id else None   # type: ignore[attr-defined]
        if licensee is None and licensee_id in needs.seat_list()["joined"] and licensee_id != acting:
            licensee = self.seat_party(licensee_id)   # type: ignore[attr-defined]   # another player
        if licensee is None or licensee.kind == "interest_group":
            return {"status": NO_LICENSEE}
        world = self.actor_world()   # type: ignore[attr-defined]
        problem = licence.terms_problem(licensee, command.fee, command.royalty, command.node_id, world)
        if problem:
            return {"status": TERMS_REFUSED, "problem": problem}
        if not licence.grant(self.seat_party(acting), licensee, command.node_id, command.fee, world):   # type: ignore[attr-defined]
            return {"status": ALREADY_ABLE}
        return {"status": GRANTED}

    def _concern_sale_setup(self, node_id: str) -> Any:
        """(the acting seat as seller, the candidate buyers, the finder of an actor by id, the world) for selling a concern."""
        needs = self.needs
        world = self.actor_world()   # type: ignore[attr-defined]
        party = self.seat_party(needs.acting_seat(), {node_id: world.concern_margin(node_id)})   # type: ignore[attr-defined]
        cast = self.cast()   # type: ignore[attr-defined]

        def find_actor(actor_id: Any) -> Any:
            return party if actor_id == party.actor_id else cast.get(actor_id)

        buyers = [actor for actor in cast.of_kind("firm") + cast.of_kind("player")
                  if getattr(actor.record, "exited_year", None) is None]
        return party, buyers, find_actor, world

    def concern_sale_terms(self, node_id: str) -> Dict[str, Any]:
        """What selling the concern would do now, without doing it: {"ok", "buyer", "price"} or {"ok": False, "error"}."""
        party, buyers, _find_actor, world = self._concern_sale_setup(node_id)
        try:
            terms = exchange_sale.sale_terms(party, node_id, buyers, world)
        except CommandRejected as reason:
            return {"ok": False, "error": str(reason)}
        return {"ok": True, "buyer": terms["buyer"].actor_id, "price": terms["price"]}

    def sell_seat_concern(self, command: Any) -> Dict[str, Any]:
        """Sell a concern the acting seat runs to the actor the exchange picks, at the price it sets."""
        party, buyers, find_actor, world = self._concern_sale_setup(command.node_id)
        try:
            sale = exchange_sale.sell_concern(party, command.node_id, buyers, find_actor, world)
        except CommandRejected as reason:
            return {"ok": False, "error": str(reason)}
        return {"ok": True, "buyer": sale["buyer"], "price": sale["price"]}
