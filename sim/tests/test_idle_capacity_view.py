"""Complaint 99: the explanation of why directed hours wait (Complaint 640: rules on built inputs)."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403

from sim.ui.proto import command_registry
from sim.ui.proto.guidance import delay_phrase, wait_explanation

check("idle is in the command registry", "idle" in command_registry.COMMANDS)

# presentation: the explanation is wording a player reads
_calendar = wait_explanation({"calendar": ["a", "b"]})
check("when every project only waits on the calendar the explanation says the wait is the calendar, not removable and not exclusive",
      "calendar" in _calendar and "not exclusive" in _calendar and "cannot be bought down" in _calendar, _calendar)
_mixed = wait_explanation({"calendar": ["a"], "money": ["b", "c"]})
check("when something waits on more than the calendar the explanation says so and names each kind with its count",
      "not only the calendar" in _mixed and "money (2)" in _mixed and "calendar (1)" in _mixed, _mixed)
# presentation: the explanation is wording a player reads
check("with nothing running nothing is waited on and the hours are free",
      "nothing is running" in wait_explanation({}), wait_explanation({}))
check("the delay phrase lists kinds in order with counts", delay_phrase({"money": ["x"], "calendar": ["a", "b"]}) == "calendar (2), money (1)",
      delay_phrase({"money": ["x"], "calendar": ["a", "b"]}))
check("the delay phrase of nothing running says so", delay_phrase({}) == "nothing running")
