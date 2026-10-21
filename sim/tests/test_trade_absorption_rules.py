"""How a taught trade becomes the society's own (Complaint 640): the years, the yearly step and the drift of an endemic
trade toward its literacy ceiling, called on built inputs with no game."""
QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.engine.trade_absorption import (BECOME_ENDEMIC, GROW, RECORD_INTRODUCTION, WAIT, absorption_step,
                                         absorption_years, headcount_toward_ceiling)

MINIMUM, BASE = 35.0, 110.0

# --- the years a trade takes to become endemic
check("with no schooling the trade takes the base span", absorption_years(0.0, MINIMUM, BASE) == BASE)
check("more schooling shortens it", absorption_years(3.0, MINIMUM, BASE) < absorption_years(1.0, MINIMUM, BASE) < BASE)
check("schooling shortens it with diminishing returns: a ninth school does not cut as much as the first",
      absorption_years(0.0, MINIMUM, BASE) - absorption_years(1.0, MINIMUM, BASE)
      > absorption_years(8.0, MINIMUM, BASE) - absorption_years(9.0, MINIMUM, BASE))
check("however much is invested it never takes less than the floor",
      absorption_years(1e9, MINIMUM, BASE) == MINIMUM)
check("heavy schooling lands between the floor and the base span", MINIMUM < absorption_years(7.0, MINIMUM, BASE) < BASE)


def years_needed(flow):
    return absorption_years(flow, MINIMUM, BASE)


# --- what one year does to one taught trade
check("the first year a taught trade is seen only records its introduction",
      absorption_step(None, False, 5.0, 100, years_needed) == RECORD_INTRODUCTION)
check("...even with no schooling and even if flagged endemic",
      absorption_step(None, True, 0.0, 100, years_needed) == RECORD_INTRODUCTION)
check("a taught trade never naturalises with no school running, however long the run",
      absorption_step(0, False, 0.0, 10_000, years_needed) == WAIT)
check("a taught trade is not endemic before its years are up",
      absorption_step(0, False, 7.0, years_needed(7.0) - 1.0, years_needed) == WAIT)
check("a taught trade becomes endemic once its years are up",
      absorption_step(0, False, 7.0, years_needed(7.0), years_needed) == BECOME_ENDEMIC)
check("the unschooled span is longer than the heavily schooled one",
      absorption_step(0, False, 0.5, years_needed(7.0) + 1.0, years_needed) == WAIT)
check("an endemic trade grows, whatever the schooling", absorption_step(0, True, 0.0, 5, years_needed) == GROW)

# --- the drift of an endemic trade
check("an endemic trade closes a fraction of the room to its ceiling each year",
      abs(headcount_toward_ceiling(2.0, 12.0, 0.05) - 2.5) < 1e-12)
check("...never reaching the ceiling in one year", headcount_toward_ceiling(2.0, 12.0, 0.05) < 12.0)
check("a trade with no ceiling is not grown", headcount_toward_ceiling(2.0, float("inf"), 0.05) == 2.0)
check("a trade already at its ceiling stays", headcount_toward_ceiling(12.0, 12.0, 0.05) == 12.0)
check("a trade above a ceiling that fell is not cut by the drift", headcount_toward_ceiling(15.0, 12.0, 0.05) == 15.0)
check("room under a millionth of a person changes nothing", headcount_toward_ceiling(11.9999999, 12.0, 0.5) == 11.9999999)
