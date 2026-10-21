"""Complaint 644: a cohort converted from a nearby trade gives partial hands on the tasks the source already does,
well before its apprenticeship ends. Functions called on built inputs, no game."""
QUICK_TOPIC = True

import json
from pathlib import Path

from .harness import *  # noqa: F401,F403
from sim.engine.projects_trade_wait import STALL_YEARS_BEFORE_ABANDONMENT
from sim.labour import trade_formation as formation
from sim.labour import trade_first_hands as hands

FULL = 8.0
UNCOVERED = 0.75
COUNT = 4.0
YEAR = 100

# the proficiency a converted person starts with is the share of the new trade's tasks the source does
check("proficiency at first hands is the covered share of tasks", abs(hands.starting_proficiency(UNCOVERED) - 0.25) < 1e-9)
check("proficiency is clamped to zero..one", hands.starting_proficiency(1.5) == 0.0 and hands.starting_proficiency(-1.0) == 1.0)

# first hands come after the part of an apprenticeship even a fully covered trade needs, never after the end
first = hands.first_hands_years(FULL)
check("first hands come after the floor and before the apprenticeship ends",
      0.0 < first < formation.training_years(FULL, UNCOVERED), first)
check("first hands scale with the trade's full apprenticeship", hands.first_hands_years(2.0 * FULL) > first)

# cohort rows: an early slice of person-equivalents and the rest at the end
years = formation.training_years(FULL, UNCOVERED)
rows = hands.cohort_rows(YEAR, "fitter", COUNT, years, FULL, UNCOVERED)
check("a cohort is two rows of the same trade", len(rows) == 2 and all(row[2] == "fitter" for row in rows), rows)
check("the rows add up to the whole cohort", abs(sum(row[3] for row in rows) - COUNT) < 1e-9, rows)
check("the early row is the covered share of the cohort", abs(rows[0][3] - COUNT * 0.25) < 1e-9, rows)
check("the early row is ready before the end row", rows[0][1] < rows[1][1] and abs(rows[1][1] - (YEAR + years)) < 1e-9, rows)

# a nearer source gives more at first hands
near = hands.cohort_rows(YEAR, "fitter", COUNT, formation.training_years(FULL, 0.25), FULL, 0.25)
check("a nearer source gives more early hands", near[0][3] > rows[0][3])

# a source that covers nothing gives no early hands: one row at the end
none = hands.cohort_rows(YEAR, "fitter", COUNT, formation.training_years(FULL, 1.0), FULL, 1.0)
check("a source covering no task gives only the final row", len(none) == 1 and abs(none[0][3] - COUNT) < 1e-9, none)

# the early slice is on the payroll from its date, so the keep paid up front stops short of it
prepaid = hands.prepaid_keep_years(years, FULL, UNCOVERED)
check("keep paid up front is shorter than the training when there are early hands", 0.0 < prepaid < years, (prepaid, years))
check("keep paid up front is the whole time when there are none", abs(hands.prepaid_keep_years(years, FULL, 1.0) - years) < 1e-9)

# the five trades absent from a founding society: with the nearest practised trade as source, each whose
# tasks any practised trade covers gets hands inside the stall window
registry = json.loads((Path(__file__).resolve().parents[2] / "data" / "world" / "trades.json").read_text())
registry = registry.get("trades", registry)
absent = sorted(trade for trade, row in registry.items() if row.get("initially_absent"))
shares = formation.shipped_task_shares()
practised = [trade for trade in registry if trade not in absent]
for trade in absent:
    ranked = formation.nearest_sources(trade, shares, practised)
    uncovered = ranked[0][0] if ranked else 1.0
    full = float(registry[trade]["training_years"])
    if uncovered >= 1.0:
        continue    # no practised trade does any of its tasks (or no recipe books hours to it)
    arrive = hands.first_hands_years(full)
    check("%s has first hands inside the stall window" % trade, arrive < STALL_YEARS_BEFORE_ABANDONMENT - 1, (arrive, uncovered))
    check("%s needs the whole apprenticeship for full hands" % trade, formation.training_years(full, uncovered) > arrive)
