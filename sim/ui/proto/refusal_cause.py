"""Copies a refusal's cause code (sim/refusal.py) into the reply that carries its text."""
from sim.refusal import cause_of, choices_of, facts_of


def add_cause(reply):
    """A refused reply whose `error` is a Refusal gains `cause`; every other reply is returned as it is."""
    if isinstance(reply, dict) and reply.get("ok") is False:
        cause = cause_of(reply.get("error"))
        if cause:
            reply["cause"] = cause
        if choices_of(reply.get("error")) is not None:
            reply["choices"] = choices_of(reply.get("error"))
    return reply


def event_codes(message):
    """{"event_kind", "facts"} for a log line that carries a kind (sim/refusal.py LogLine), else {}."""
    kind = cause_of(message)
    if not kind:
        return {}
    return {"event_kind": kind, "facts": facts_of(message)}


def event_rows(log_rows):
    """The reply's event rows, one per `(year, message)` log row in order, each with its own year and codes."""
    return [{"year": year, "message": message, **event_codes(message)} for year, message in log_rows]
