"""Complaint 644: a learning curve on cumulative output with a floor, an error share that falls with proficiency, and a
first cohort whose start is capped by its teacher. Rules called on numbers; no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.labour import learning_curve as curve
from sim.labour import trade_first_hands as hands

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

# error falls with proficiency, to a floor above zero
check("a first attempt spoils the most", curve.error_share(0.0, 0.3, 0.02) == 0.3)
check("full proficiency spoils the floor share", abs(curve.error_share(1.0, 0.3, 0.02) - 0.02) < 1e-12)
check("error falls as proficiency rises", curve.error_share(0.2, 0.3, 0.02) > curve.error_share(0.8, 0.3, 0.02))
try:
    curve.error_share(1.0, 0.3, 0.0)
    refused = False
except ValueError:
    refused = True
check("an error floor of zero is refused", refused)

# spillover: what others have made counts in part
check("learning pools a share of what others have made", abs(curve.pooled_units(10.0, 100.0, 0.25) - 35.0) < 1e-9)
check("no spillover is own output only", curve.pooled_units(10.0, 100.0, 0.0) == 10.0)
check("a trade that learns from its neighbours is ahead of one that learns alone",
      curve.proficiency(curve.pooled_units(10.0, 100.0, 0.5), FLOOR, RATE) > curve.proficiency(10.0, FLOOR, RATE))

# the teacher caps the first cohort's start
UNCOVERED = 0.25
rows_free = hands.cohort_rows(100, "fitter", 4.0, 3.0, 8.0, UNCOVERED)
rows_capped = hands.cohort_rows(100, "fitter", 4.0, 3.0, 8.0, UNCOVERED, teacher_proficiency=0.3)
check("a teacher who is fully proficient does not cap the start", abs(rows_free[0][3] - 4.0 * 0.75) < 1e-9, rows_free)
check("a less proficient teacher caps the early slice", abs(rows_capped[0][3] - 4.0 * 0.3) < 1e-9, rows_capped)
check("a teacher who holds the knowledge but has never practised starts a cohort at the floor",
      abs(hands.cohort_rows(100, "fitter", 4.0, 3.0, 8.0, UNCOVERED,
                            teacher_proficiency=curve.proficiency(0.0, FLOOR, RATE))[0][3] - 4.0 * FLOOR) < 1e-9)
check("the capped cohort still adds up to the whole cohort", abs(sum(row[3] for row in rows_capped) - 4.0) < 1e-9, rows_capped)
