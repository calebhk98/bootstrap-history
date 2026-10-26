"""Handing a seat over (the rules are handover_rules.py): the module decides whether it may be done, has the registry move
the seat and rename it in the stores the engine keeps, and renames it in its own and diffusion's."""
from typing import Any

from sim.diffusion.api import RekeyDisclosures
from sim.rekey import rekey

from . import handover_rules
from .commands import HandOverSeat, MoveSeat

DEALING_FIELDS = ("patents", "shares_held", "shares_issued", "offers", "offer_serial")


class Handover:

    def hand_over_seat(self, command: HandOverSeat) -> Any:
        """Pass `from_id`'s seat to `to_id`: the seat's fields, its account with the debts and claims, and whatever else is
        keyed by its id; it leaves the year. Answers a Refusal that changed nothing, or what moved (the registry's account)."""
        from_id, to_id = command.from_id, command.to_id
        seats = self.needs.legacy_seats()
        holds = []
        if to_id in seats:
            slot = self.seat_of(to_id)
            holds = handover_rules.holds_in_order(
                self.needs.seat_holds[to_id], bool(self.needs.disclosures[to_id]),
                handover_rules.dealings_in_use(slot), handover_rules.goal_record_in_use(slot))
        refusal = handover_rules.handover_refusal(seats, from_id, to_id, holds)
        if refusal:
            return refusal
        moved = self.needs.send(MoveSeat(from_id, to_id))
        for seat_id in seats:
            slot = self.seat_of(seat_id)
            for name in DEALING_FIELDS:
                renamed = rekey(getattr(slot, name), from_id, to_id)
                if renamed is not getattr(slot, name):
                    setattr(slot, name, renamed)
            self.needs.send(RekeyDisclosures(seat_id, from_id, to_id))
            slot.offers[:] = [offer for offer in slot.offers if offer.get("from") != offer.get("to")]
        self.seat_of(to_id).shares_held.pop(to_id, None)   # a stake in oneself is no stake
        return moved
