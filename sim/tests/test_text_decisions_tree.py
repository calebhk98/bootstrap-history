"""text_decisions over the whole tree: no code under sim/ decides on a log line's or a refusal's text (Complaint 521).
A static scan that runs nothing; slow-tier only because it parses every module under sim/."""
from .harness import check
from sim.tests import text_decisions

_found = text_decisions.scan()
check("no code under sim/ decides on a log line's or refusal's text (python3 -m sim.tests --text-decisions)",
      _found == [], _found[:5])
_plain = text_decisions.scan_appends()
check("every append to a log under sim/ is a LogLine with a kind", _plain == [], _plain[:5])
_unlisted = text_decisions.unlisted_kinds()
check("every kind a LogLine is given is listed in sim/ui/proto/event_kinds.py", _unlisted == [], _unlisted)
