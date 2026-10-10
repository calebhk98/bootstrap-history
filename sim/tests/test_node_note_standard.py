"""Complaint 128: every node note is long enough to teach the thing from zero.

The audit is a length screen (`sim/engine/validate_note_quality.py`); the standard the
notes are written to is `data/branches/NOTE_STANDARD.md`."""

QUICK_TOPIC = True

from sim.engine import validate_note_quality

from .harness import *  # noqa: F401,F403

_MINIMUM = validate_note_quality.MINIMUM_NOTE_LENGTH

check("the audit flags a missing note and a note below the minimum",
      validate_note_quality.short_notes({
          "empty": {"note": ""}, "absent": {}, "brief": {"note": "x" * (_MINIMUM - 1)},
          "long": {"note": "x" * _MINIMUM}}) == ["absent", "brief", "empty"])

check("the audit report counts the flagged notes",
      validate_note_quality.report_lines({"a": {"note": "short"}, "b": {"note": "y" * 200}})[0]
      == "NODE NOTES below the teaching minimum: 1 of 2")

_flagged = validate_note_quality.short_notes(NODES)
check("no loaded node has a note below the teaching minimum (complaint 128)",
      _flagged == [], _flagged[:20])
