"""Answers read from the market memory, kept until the memory is next written to (`market_memory.note_written`)."""
from . import market_memory

_kept = {"memory": None, "writes": None, "answers": {}}


def writes_made() -> int:
    """How many writes the market memory has seen; an answer read from it holds while this number does."""
    return market_memory._writes[0]


def kept(memory, key, compute):
    """`compute()` once per `key` for this memory until it is written to. The answer is a number, shared by every caller."""
    if _kept["memory"] is not memory or _kept["writes"] != writes_made():
        _kept["memory"], _kept["writes"], _kept["answers"] = memory, writes_made(), {}
    answers = _kept["answers"]
    try:
        return answers[key]
    except KeyError:
        found = answers[key] = compute()
        return found
