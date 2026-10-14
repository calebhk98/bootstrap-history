"""Copies a refusal's cause code (sim/refusal.py) into the reply that carries its text."""
from sim.refusal import cause_of, choices_of


def add_cause(reply):
    """A refused reply whose `error` is a Refusal gains `cause`; every other reply is returned as it is."""
    if isinstance(reply, dict) and reply.get("ok") is False:
        cause = cause_of(reply.get("error"))
        if cause:
            reply["cause"] = cause
        if choices_of(reply.get("error")) is not None:
            reply["choices"] = choices_of(reply.get("error"))
    return reply
