"""The calendar a failed attempt banks toward the next one, called on built numbers."""
from sim.engine.retry_calendar import retry_calendar_retain

from .harness import check

QUICK_TOPIC = True

CAP, DECAY = 0.65, 0.5
banked = [retry_calendar_retain(CAP, DECAY, count) for count in range(6)]
check("before any failure nothing is banked", banked[0] == 0.0)
check("each failure banks more than the one before", all(later > earlier for earlier, later in zip(banked, banked[1:])), banked)
check("the first failure banks a real share of the clock", 0.0 < banked[1] < CAP, banked)
check("the increments shrink", all(banked[i + 1] - banked[i] < banked[i] - banked[i - 1] for i in range(1, 5)), banked)
check("it never reaches the cap", all(value < CAP for value in banked) and retry_calendar_retain(CAP, DECAY, 60) <= CAP)
check("a negative count banks nothing", retry_calendar_retain(CAP, DECAY, -2) == 0.0)
