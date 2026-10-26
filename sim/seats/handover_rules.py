"""Handing a seat over: when it may be done, and what it moves.

A seat's known nodes, holdings and goal pass to a named replacement seat and the old seat leaves. The replacement keeps
its own founder (the leaver's run is over). Everything else a seat owns moves as the same objects: household, projects
(the known nodes), holdings, institutions, goal record, chosen goal, country and every module's seat state. Records keyed
to the country (the relations store) therefore stay with the country the replacement now plays for.

The replacement is a seat already in the game and must hold no works, staff, holdings or institutions of its own: those
would be overwritten, so a replacement that holds some is refused. What merges without loss is added: its cash, deposits
and debts join the leaver's under the replacement's id, and the techniques it knows join the leaver's. Everything keyed by
the leaver's id outside the seat is renamed to the replacement's, so a handover pays and forgives nothing."""
from typing import Any, List, Mapping, Optional

from sim.refusal import Refusal

# what a refusal names, in the order the player reads it
HOLD_ORDER = ("works", "staff", "arrears or bondage", "holdings", "institutions", "goal record")


def handover_refusal(seats: Mapping[str, Any], from_id: str, to_id: str, holds: List[str]) -> Optional[Refusal]:
    """Why `from_id` cannot hand over to `to_id`, or None when it can. `holds` is what `to_id` holds that a handover
    would overwrite (empty for an empty seat, and unread when `to_id` is not a seat)."""
    known = list(seats)
    for role, seat_id in (("from", from_id), ("to", to_id)):
        if seat_id not in seats:
            return Refusal("unknown_seat", "there is no seat %r to hand %s. The seats are: %s. Nothing was changed."
                           % (seat_id, role, ", ".join(known)), choices=known, seat=seat_id)
    if from_id == to_id:
        return Refusal("same_seat", "a seat cannot be handed to itself. Nothing was changed.", seat=from_id)
    if seats[from_id].kind != seats[to_id].kind:
        return Refusal("replacement_wrong_kind", "seat %r is a %s seat and %r is a %s seat; a seat passes only to a seat of its own kind "
                       "(join adds one). Nothing was changed." % (from_id, seats[from_id].kind, to_id, seats[to_id].kind),
                       seat=to_id, kind=seats[from_id].kind)
    if holds:
        return Refusal("replacement_not_empty", "seat %r already has %s, which a handover would overwrite. Hand over to an empty "
                       "seat (join adds one). Nothing was changed." % (to_id, ", ".join(holds)), seat=to_id, holds=holds)
    return None


def holds_in_order(engine_holds: List[str], has_disclosures: bool, has_dealings: bool, has_goal_record: bool) -> List[str]:
    """What the replacement holds, from the engine's account of the seat's own state plus what the module itself keeps
    (disclosures are works; dealings are holdings; a goal year is a goal record), in the order a player reads them."""
    found = set(engine_holds)
    if has_disclosures:
        found.add("works")
    if has_dealings:
        found.add("holdings")
    if has_goal_record:
        found.add("goal record")
    return sorted(found, key=HOLD_ORDER.index)


def dealings_in_use(slot: Any) -> bool:
    """Whether the seat has patents, shares, offers or an offer count (what `holdings_in_use` once saw of them)."""
    return bool(slot.patents or slot.shares_held or slot.shares_issued or slot.offers or slot.offer_serial)


def goal_record_in_use(slot: Any) -> bool:
    """Whether a goal has been reached (what the goal record once held)."""
    return slot.goal_year is not None or bool(slot.goal_years)
