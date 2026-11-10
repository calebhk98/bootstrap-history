"""The JSON text the solve key hashes, with the text of a large input kept while the input is unchanged.

`payload_text(inputs, environment)` is exactly `json.dumps({"inputs": inputs, "environment": environment}, sort_keys=True,
default=sorted)`. A large value (the production catalogue, the same object for the whole process) is serialised once; a later
call reuses its text when `marshal` writes the same bytes for it, which holds only for the same types and values, so a changed
catalogue is serialised again."""
import json
import marshal
from typing import Any, Dict, List, Tuple

# TEMPORARY HEURISTIC (CLAUDE.md 4.4): a value this long is worth keeping the text of; retire: Complaint 968.
LARGE_INPUT = 100
_KEPT_VALUES = 4
_kept: List[Tuple[Any, bytes, str]] = []     # (the value itself, its marshal bytes, its text), newest last


def _text(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=lambda element: sorted(element))


def value_text(value: Any) -> str:
    """`_text(value)`; a large dict or list keeps its text between calls while its marshal bytes are unchanged."""
    if not isinstance(value, (dict, list)) or len(value) < LARGE_INPUT:
        return _text(value)
    try:
        snapshot = marshal.dumps(value)
    except ValueError:      # a type marshal does not write
        return _text(value)
    for held, held_snapshot, held_text in _kept:
        if held is value and held_snapshot == snapshot:
            return held_text
    text = _text(value)
    _kept[:] = [entry for entry in _kept if entry[0] is not value][-(_KEPT_VALUES - 1):]
    _kept.append((value, snapshot, text))
    return text


def payload_text(inputs: Dict[str, Any], environment: str) -> str:
    """The text of `{"inputs": inputs, "environment": environment}` as `json.dumps(..., sort_keys=True)` writes it."""
    if not all(isinstance(key, str) for key in inputs):
        return _text({"inputs": inputs, "environment": environment})
    members = ", ".join("%s: %s" % (json.dumps(key), value_text(inputs[key])) for key in sorted(inputs))
    return '{"environment": %s, "inputs": {%s}}' % (json.dumps(environment), members)
