"""Which seat a command addresses: the command's `as`, else the session's seat, else the first seat.

Pure: takes the seat ids and the command, answers a seat id or a refusal. The dispatcher runs the handler as
that seat (`Sim.act_as`), so handlers keep reading the acting seat."""
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
        return None, {"ok": False, "error": "there is no seat %r. The seats are: %s. Nothing was changed."
                                            % (requested, ", ".join(known))}
    return requested, None


def without_seat(cmd: Mapping[str, Any]) -> dict:
    """The command as a handler sees it: the addressing key is not one of its arguments."""
    return {key: value for key, value in cmd.items() if key != SEAT_KEY}


def run_as_seat(sim, cmd, reply):
    """Answer `cmd` with `reply(command)` while the addressed seat acts; a refusal when no such seat exists."""
    seat_id, refusal = addressed_seat(sim.state.seats, cmd, getattr(sim, "session_seat", None))
    if refusal:
        return refusal
    with sim.act_as(seat_id):
        return reply(without_seat(cmd) if isinstance(cmd, dict) else cmd)
