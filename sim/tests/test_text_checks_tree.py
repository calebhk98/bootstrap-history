"""text_checks over the whole tree: the list of behaviour checks that read player text stays empty (Complaint 515).
A static scan that runs nothing; slow-tier only because it parses every test module."""
from .harness import check
from sim.tests import text_checks

_behaviour_rows = text_checks.classify()[0]
check("no check of a behaviour topic reads player text (python3 -m sim.tests --text-checks)",
      _behaviour_rows == [], _behaviour_rows[:5])
