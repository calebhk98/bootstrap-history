"""Complaint 421: `auto_hire` has a replace-only mode that hires only for staff lost.

The replace-only rule is tested on a stand-in for the household (`replace_lost_staff`) and the typed switch is parsed
on its own. The mode the staff phase takes, the policy switch and the mine order id from audit row to working are
in test_automation_wiring."""

QUICK_TOPIC = True
from sim.tests import workforce_stand_in
from types import SimpleNamespace

from .harness import *  # noqa: F401,F403

from sim.workforce.staff_replacement import REPLACE_ONLY
from sim.ui.proto.typed import parse_typed
from sim.tests.workforce_host import workforce_over

# ---- the switch is typed and parsed
check("typed 'policy auto_hire replace' parses",
      parse_typed("policy auto_hire replace")[0] == {"cmd": "policy", "set": {"auto_hire": REPLACE_ONLY}},
      parse_typed("policy auto_hire replace"))
check("another policy refuses 'replace'", parse_typed("policy auto_mine replace")[0] is None)


