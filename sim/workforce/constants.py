"""Numbers the workforce module declares."""
from sim.constants import declare

BASE_WORKING_DAY_HOURS = declare(
    "BASE_WORKING_DAY_HOURS", 10.0, kind="engineering_estimate", unit="hours per working day",
    source="The ten-hour day behind HOURS_PER_PERSON_YEAR in sim/unit_conversions.py.", confidence="B",
    why="The day that extra lit hours are added to; the working year grows in the same proportion.")

WAGE_SCARCITY_ELASTICITY = declare(
    "WAGE_SCARCITY_ELASTICITY", 0.9, kind="hardcoded_outcome",
    unit="dimensionless (wage premium per unit of population shortfall)",
    source="Phelps Brown and Hopkins' English real-wage index shows "
           "roughly a doubling across the century after 1348.",
    confidence="C",
    why="How much scarcer labour raises its own price - see the wage_index view: at this elasticity, a Black-Death-sized "
        "shortfall reproduces roughly the cited real-wage doubling over "
        "the timescale sim/world/demography.py's own vital rates take "
        "to close it. FLAGGED AS A CLAUDE.md SS3.1/3.2 RISK: chosen "
        "specifically to land in the range that reproduces a known "
        "historical wage-index outcome (Phelps Brown and Hopkins), "
        "rather than derived from labour supply and demand "
        "fundamentals - the same shape as economy.py's DEBT_BASE_RATE, "
        "a real attested figure standing in for a market mechanism "
        "this project has not built. It is not fitted to the series "
        "numerically, but it was picked because it lands near the "
        "answer, which is the thing SS3.2 asks a baseline to reach "
        "independently rather than by construction.")

# Years between one automatic teaching of a trade and the next. Long
# enough that restoring a lost trade is an event rather than a habit.
RETEACH_EVERY = declare(
    "RETEACH_EVERY", 25, kind="temporary_heuristic", unit="years",
    source=None, confidence="D",
    why="Minimum gap between one automatic re-teaching of a lost "
        "trade and the next, so restoring it is an event rather than "
        "a habit the optimizer leans on every year. Round number, not "
        "measured.")

DIRECTORS_EXTRA_APPROACH_RATE = declare(
    "DIRECTORS_EXTRA_APPROACH_RATE", 0.12, kind="temporary_heuristic",
    unit="dimensionless (fraction of the gap to capacity closed per "
         "year)", source=None, confidence="D",
    why="How fast the household's deputy-director pool approaches "
        "what its institutions can support, net of the same "
        "working-age mortality that thins ordinary staff. Tuned so "
        "deputies build up over several years rather than "
        "instantaneously; not measured.")

AUTO_HIRE_CREDIT_ROOM_SHARE = declare(
    "AUTO_HIRE_CREDIT_ROOM_SHARE", 0.75, kind="temporary_heuristic",
    unit="dimensionless (share of credit_limit treated as still "
         "usable for growth)", source=None, confidence="D",
    why="How deep into arrears the automation will still hire, "
        "relative to the credit line - deep arrears means building, "
        "not growing, is the household's actual state (see comment "
        "above). Tuned, not measured.")
AUTO_HIRE_SCHOLAR_EXTRA_SHARE = declare(
    "AUTO_HIRE_SCHOLAR_EXTRA_SHARE", 0.35, kind="temporary_heuristic",
    unit="dimensionless (share of supervision-room headroom spent on "
         "scholars)", source=None, confidence="D",
    why="How much of the household's extra supervision headroom is "
        "aimed at scholars versus artisans when auto_hire grows the "
        "staff. Tuned split, not measured.")
AUTO_HIRE_SCHOLAR_APPROACH_RATE = declare(
    "AUTO_HIRE_SCHOLAR_APPROACH_RATE", 0.18, kind="temporary_heuristic",
    unit="dimensionless (fraction of the gap to target closed per "
         "year)", source=None, confidence="D",
    why="How fast the scholar pool approaches its target headcount "
        "under auto_hire - smoothed rather than instant so growth "
        "reads as hiring over years, not a single jump. Tuned, not "
        "measured.")
AUTO_HIRE_ARTISAN_APPROACH_RATE = declare(
    "AUTO_HIRE_ARTISAN_APPROACH_RATE", 0.22, kind="temporary_heuristic",
    unit="dimensionless (fraction of the gap to target closed per "
         "year)", source=None, confidence="D",
    why="As AUTO_HIRE_SCHOLAR_APPROACH_RATE, for artisans - slightly "
        "faster, tuned rather than measured.")
AUTO_HIRE_SLAVE_CRAFT_CREDIT = declare(
    "AUTO_HIRE_SLAVE_CRAFT_CREDIT", 0.7, kind="temporary_heuristic",
    unit="dimensionless (fraction of a slave counted as a craft "
         "worker already)", source=None, confidence="D",
    why="How much of the desired artisan headcount an existing slave "
        "is treated as already covering, before auto_hire tops up the "
        "generic craft bucket - slaves are not all doing craft work, "
        "so this is a partial credit rather than one-for-one. Tuned, "
        "not measured.")

TRADE_REPLACEMENT_TARGET_HEADCOUNT = declare(
    "TRADE_REPLACEMENT_TARGET_HEADCOUNT", 2.0, kind="temporary_heuristic",
    unit="people", source=None, confidence="D",
    why="Minimum headcount auto_hire tries to keep in any trade the "
        "founder has ever taught, once attrition has thinned it - "
        "enough that a taught trade cannot silently vanish from a "
        "single death. Round number, not measured.")
TRADE_REPLACEMENT_AFFORDABILITY_YEARS = declare(
    "TRADE_REPLACEMENT_AFFORDABILITY_YEARS", 6, kind="temporary_heuristic",
    unit="years of that trade's annual wage", source=None,
    confidence="D",
    why="How much spare capital (in years of the trade's own wage) "
        "the household must hold before auto_hire replaces a lost "
        "taught worker - a buffer so this does not spend the "
        "household into arrears over one specialist. Tuned, not "
        "measured.")
