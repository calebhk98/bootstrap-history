"""The seats commands: who is playing, and adding a player to a game under way."""

from sim.engine.ui_port import STARTING_KITS

from sim.refusal import Refusal

from .command_registry import command
from .notes_store import hand_over_notes


def seat_rows(sim):
    """One row per seat: its id, country and whether its run has ended. The addressed seat also shows its own
    purse and what it has built; another seat's purse and work are not shown (they are its own to tell)."""
    ended = set(sim.ended_seats())
    rows = []
    for seat_id, seat in sim.state.seats.items():
        row = {"seat": seat_id, "country": seat.country or sim.civ.get("id"), "ended": seat.founder.dead_reason
               if seat_id in ended else None, "you": seat_id == sim.state.acting_seat}
        if seat_id == sim.state.acting_seat:
            row.update({"capital": round(seat.household.capital, 1),
                        "built": len(seat.projects.done - seat.projects.granted)})
        rows.append(row)
    return rows


@command("seats", shape="bare", group="game", aliases=("players",),
         summary="who is playing in this game",
         usage=["seats", '{"cmd":"seats"}'],
         description="Lists every seat with its country and whether its run has ended. A command is for the seat "
                     "named in its \"as\" field, else the session's seat (agent --seat), else the first seat. "
                     "The year advances for every seat that is still playing when anyone steps.")
def _cmd_seats(sim, nodes, cmd, ended):
    return {"ok": True, "seats": seat_rows(sim), "year": sim.year,
            "note": 'add "as":"<seat>" to a command to act as that seat; "join" adds a player.'}


@command("join", shape="word", group="game",
         summary="add a player to the game",
         usage=["join <seat>", '{"cmd":"join","seat":"second","kit":"poor_scholar"}'],
         options={"<seat>": "the new seat's id", "kit": "a starting kit (default: the game's own)",
                  "country": "the civilisation the player belongs to (default: this game's)"},
         description="Adds a seat that starts with a kit's money at today's prices and knows what this society "
                     "holds now. Its commands are then sent with \"as\":\"<seat>\". It plays from the next step.")
def _cmd_join(sim, nodes, cmd, ended):
    seat_id = cmd.get("seat") or cmd.get("what")
    if not isinstance(seat_id, str) or not seat_id.strip():
        return {"ok": False, "error": 'name the new seat, e.g. {"cmd":"join","seat":"second"}'}
    seat_id = seat_id.strip()
    if seat_id in sim.state.seats:
        return {"ok": False, "error": "there is already a seat %r. Nothing was changed." % seat_id}
    kit = cmd.get("kit") or sim.cfg["start_kit"]
    if kit not in STARTING_KITS:
        return {"ok": False, "error": "unknown kit %r. Kits: %s. Nothing was changed." % (kit, ", ".join(STARTING_KITS))}
    template = {"kit": kit, "starting_techs": sorted(sim.society_techs_now() & set(sim.nodes)),
                "country": cmd.get("country")}
    sim.join_seat(seat_id, template)
    return {"ok": True, "joined": seat_id, "seats": seat_rows(sim),
            "note": 'send its commands with "as":"%s"; it plays from the next step.' % seat_id}


def hand_over(sim, caller, from_id, to_id):
    """Pass seat `from_id` to `to_id` on behalf of `caller`: the engine moves the seat, then its notes follow.
    Answers the reply; a refusal carries `cause` and changes nothing."""
    if from_id != caller:
        return {"ok": False, "cause": "not_your_seat", "choices": [caller], "seat": from_id,
                "error": "you can hand over only your own seat (%s), not %r. Nothing was changed." % (caller, from_id)}
    moved = sim.hand_over_seat(from_id, to_id)
    if isinstance(moved, Refusal):
        return {"ok": False, "cause": moved.cause, "choices": moved.choices, "error": str(moved), **moved.facts}
    notes = hand_over_notes(sim, from_id, to_id)
    return dict(moved, ok=True, notes=notes, seats=seat_rows(sim),
                note='seat %s now holds what %s held; send its commands with "as":"%s".' % (to_id, from_id, to_id))


@command("handover", shape="word", group="game", aliases=("hand_over",),
         summary="hand your seat's knowledge, holdings and notes to another seat",
         usage=["handover <seat>", '{"cmd":"handover","to":"second"}'],
         options={"<seat>": "the replacement seat (it must already be in the game and empty; 'join' adds one)",
                  "from": "the seat to hand over; only your own is allowed (default: yours)"},
         description="The replacement takes the known techniques, built works, holdings, cash, institutions, goal, "
                     "country and notes of your seat, and your seat leaves the game. Records kept by country, such "
                     "as relations, stay with that country. Your debts pass with the seat. Refusals carry a cause: "
                     "unknown_seat, same_seat, not_your_seat, replacement_not_empty.")
def _cmd_handover(sim, nodes, cmd, ended):
    to_id = cmd.get("to") or cmd.get("seat") or cmd.get("what")
    if not isinstance(to_id, str) or not to_id.strip():
        return {"ok": False, "cause": "no_replacement",
                "error": 'name the replacement seat, e.g. {"cmd":"handover","to":"second"}'}
    caller = sim.state.acting_seat
    return hand_over(sim, caller, cmd.get("from", caller), to_id.strip())
