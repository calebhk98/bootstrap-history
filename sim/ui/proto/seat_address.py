"""Which seat a command addresses: the command's `as`, else the session's seat, else the first seat.

Pure: takes the seat ids and the command, answers a seat id or a refusal. The dispatcher runs the handler as
that seat (`Sim.act_as`), so handlers keep reading the acting seat."""
from . import command_registry
from typing import Any, Iterable, Mapping, Optional, Tuple

SEAT_KEY = "as"


def addressed_seat(seat_ids: Iterable[str], cmd: Mapping[str, Any], session_seat: Optional[str] = None
                   ) -> Tuple[Optional[str], Optional[dict]]:
    """(seat id, None) for the seat the command is for, or (None, refusal reply) when it names none that exists."""
    known = list(seat_ids)
    requested = cmd.get(SEAT_KEY) if isinstance(cmd, Mapping) else None
    if requested is None:
        requested = session_seat if session_seat is not None else (known[0] if known else None)
    elif not isinstance(requested, str):
        return None, {"ok": False, "error": "as must be a seat id in quotes, not %s. Nothing was changed."
                                            % type(requested).__name__}
    if requested not in known:
        return None, {"ok": False, "cause": "unknown_seat", "choices": known,
                      "error": "there is no seat %r. The seats are: %s. Nothing was changed."
                               % (requested, ", ".join(known))}
    return requested, None


def without_seat(cmd: Mapping[str, Any]) -> dict:
    """The command as a handler sees it: the addressing key is not one of its arguments."""
    return {key: value for key, value in cmd.items() if key != SEAT_KEY}


# What a seat with no household of its own may be asked: reads about the world, the seats, the game and the
# country's relations. `step` runs the year as the first household seat that is playing.
COUNTRY_SEAT_COMMANDS = frozenset({"seats", "join", "handover", "help", "save", "load", "quit", "options", "game_options",
                                   "relations", "set_relation", "lever", "levers", "population", "demography", "map", "groups", "values",
                                   "world_events", "step"})


def _command_name(cmd):
    entry = command_registry.resolve(cmd.get("cmd") if isinstance(cmd, dict) and isinstance(cmd.get("cmd"), str) else "")
    return entry["name"] if entry else None


def country_seat_refusal(sim, seat_id, cmd):
    """A refusal when `cmd` needs a household and `seat_id` holds a country's government, else None."""
    name = _command_name(cmd)
    if sim.state.seats[seat_id].holds_household or name is None or name in COUNTRY_SEAT_COMMANDS:
        return None
    return {"ok": False, "cause": "country_seat_has_no_household", "choices": sorted(COUNTRY_SEAT_COMMANDS),
            "error": "seat %r holds a country's government and has no household, so %r does not apply to it. "
                     "Nothing was changed." % (seat_id, name)}


def run_as_seat(sim, cmd, reply):
    """Answer `cmd` with `reply(command)` while the addressed seat acts; a refusal when no such seat exists."""
    seat_id, refusal = addressed_seat(sim.state.seats, cmd, getattr(sim, "session_seat", None))
    if refusal:
        return refusal
    refusal = country_seat_refusal(sim, seat_id, cmd)
    if refusal:
        return refusal
    if not sim.state.seats[seat_id].holds_household and _command_name(cmd) == "step":
        playing = sim.playing_seats()
        if not playing:
            return {"ok": False, "cause": "no_household_seat",
                    "error": "no household seat is playing, so the year has no one to run it. Nothing was changed."}
        seat_id = playing[0]
    with sim.act_as(seat_id):
        return reply(without_seat(cmd) if isinstance(cmd, dict) else cmd)
