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
