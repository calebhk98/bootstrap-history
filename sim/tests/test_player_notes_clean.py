"""Complaint 122: player-facing notes must not contain audit markers or patch history."""
from .harness import *  # noqa: F401,F403

# Audit markers and patch history patterns that should never appear in player notes
_FORBIDDEN_PATTERNS = [
    "[REVIEWED",
    "[audit",
    "previously",
    "was changed",
    "was floating free",
    "is now a",
    "FIXED",
    "OPTIONAL, and no longer a prerequisite",
]

_offenders = {}
for node_id, node in NODES.items():
    note = node.get("note") or ""
    for pattern in _FORBIDDEN_PATTERNS:
        if pattern in note:
            if node_id not in _offenders:
                _offenders[node_id] = []
            _offenders[node_id].append(pattern)

check("no node's player-facing note contains audit markers or patch history "
      "(complaint 122)",
      _offenders == {}, _offenders)
