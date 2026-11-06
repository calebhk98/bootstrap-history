"""Complaint 644: a learning curve on cumulative output with a floor, an error share that falls with proficiency, and a
first cohort whose start is capped by its teacher. Rules called on numbers; no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.labour import learning_curve as curve

FLOOR = 0.2
RATE = 0.8

# Wright's law: each doubling of cumulative output cuts the unit time to the progress ratio
check("a doubling of cumulative output cuts the unit time to the progress ratio",
      abs(curve.unit_time_ratio(8.0, FLOOR, RATE) / curve.unit_time_ratio(4.0, FLOOR, RATE) - RATE) < 1e-9)
check("the first unit takes the first unit's time", curve.unit_time_ratio(1.0, FLOOR, RATE) == 1.0)
check("a trade that has made nothing is at its first attempt's time", curve.unit_time_ratio(0.0, FLOOR, RATE) == 1.0)
check("a steeper curve (lower ratio) learns faster", curve.unit_time_ratio(16.0, FLOOR, 0.7) < curve.unit_time_ratio(16.0, FLOOR, 0.9))
check("a ratio of one is no learning", curve.unit_time_ratio(1000.0, FLOOR, 1.0) == 1.0)

# the floor: learning stops where the technique's physics does
check("unit time never falls below the floor however much is made", curve.unit_time_ratio(1.0e12, FLOOR, RATE) == FLOOR)
check("proficiency reaches one at the floor and no further", curve.proficiency(1.0e12, FLOOR, RATE) == 1.0)
check("a first attempt is at the floor's share of full proficiency", abs(curve.proficiency(1.0, FLOOR, RATE) - FLOOR) < 1e-12)
check("proficiency rises with cumulative output",
      curve.proficiency(2.0, FLOOR, RATE) < curve.proficiency(20.0, FLOOR, RATE) < curve.proficiency(200.0, FLOOR, RATE))
for bad_floor in (0.0, -1.0, 1.5):
    try:
        curve.unit_time_ratio(10.0, bad_floor, RATE)
        refused = False
    except ValueError:
        refused = True
    check("a floor of %s is refused (a zero floor would make output with no labour)" % bad_floor, refused)
try:
    curve.learning_exponent(1.2)
    refused = False
except ValueError:
    refused = True
check("a progress ratio above one is refused", refused)

# the inverse: units needed for a proficiency
needed = curve.cumulative_for_proficiency(0.5, FLOOR, RATE)
check("the units for a proficiency give that proficiency back", abs(curve.proficiency(needed, FLOOR, RATE) - 0.5) < 1e-9, needed)
check("a first attempt's proficiency needs one unit", curve.cumulative_for_proficiency(FLOOR, FLOOR, RATE) == 1.0)
