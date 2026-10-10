"""Validation rule: a node's note is long enough to teach the thing from zero.

A length screen, not a quality judgement: the standard a note is written to is in
`data/branches/NOTE_STANDARD.md`. A note below the minimum cannot hold what the thing is,
how it works, what it needs and why it is hard."""
from typing import Any, List, Mapping

MINIMUM_NOTE_LENGTH = 120
LISTED_LIMIT = 12


def short_notes(nodes: Mapping[str, Mapping[str, Any]]) -> List[str]:
    """Ids of nodes whose note is missing or below the minimum length, sorted."""
    return sorted(node_id for node_id, node in nodes.items()
                  if len((node.get("note") or "").strip()) < MINIMUM_NOTE_LENGTH)


def report_lines(nodes: Mapping[str, Mapping[str, Any]]) -> List[str]:
    flagged = short_notes(nodes)
    lines = ["NODE NOTES below the teaching minimum: %d of %d" % (len(flagged), len(nodes))]
    if flagged:
        lines.append("  " + ", ".join(flagged[:LISTED_LIMIT])
                     + (", ..." if len(flagged) > LISTED_LIMIT else ""))
    return lines


def check_note_quality(nodes: Mapping[str, Mapping[str, Any]]) -> List[str]:
    return ["%s: note is shorter than the teaching minimum; see data/branches/NOTE_STANDARD.md" % node_id
            for node_id in short_notes(nodes)]
