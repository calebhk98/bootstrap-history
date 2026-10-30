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

WAGE_FALLBACK_MIN_HOURS = declare(
    "WAGE_FALLBACK_MIN_HOURS", 100.0, kind="temporary_heuristic",
    unit="founder-hours", source=None, confidence="D",
    why="Minimum unused hours before the optimizer's wage-work "
        "fallback bothers activating - not worth the overhead of "
        "selling a token amount. Round number, not measured.")
WAGE_FALLBACK_LIVING_COST_YEARS = declare(
    "WAGE_FALLBACK_LIVING_COST_YEARS", 2, kind="temporary_heuristic",
    unit="years of living cost", source=None, confidence="D",
    why="How thin a cash buffer (in years of living cost) triggers "
        "the optimizer selling idle hours for wages rather than "
        "riding out a bad year - see comment above: without this, a "
        "single early fire could end a run in a handful of years. "
        "Tuned, not measured.")
WAGE_FALLBACK_MAX_HOURS = declare(
    "WAGE_FALLBACK_MAX_HOURS", 1200.0, kind="temporary_heuristic",
    unit="founder-hours/year", source=None, confidence="D",
    why="Ceiling on how many hours a year the wage-work fallback will "
        "sell, so it cannot consume the entire year even when nothing "
        "else has any claim on the founder's time. Tuned, not "
        "measured.")

HOUSING_LABOUR_HOURS_PER_PLACE = declare(
    "HOUSING_LABOUR_HOURS_PER_PLACE", 12000.0, kind="temporary_heuristic",
    unit="labour hours per place", source=None, confidence="D",
    why="Cost to build one place of durable worker housing. Not "
        "sourced to any attested construction cost; an invented figure "
        "sized to make the lever meaningful without being free.")
TRADE_SCHOOL_LABOUR_HOURS_PER_SEAT = declare(
    "TRADE_SCHOOL_LABOUR_HOURS_PER_SEAT", 24000.0, kind="temporary_heuristic",
    unit="labour hours per seat", source=None, confidence="D",
    why="Cost to found one seat of a named trade school (see "
        "labour.py's consumer of this figure, outside this file's "
        "scope). Not sourced to any attested cost of pre-industrial "
        "vocational training.")
HOUSEHOLD_DEPENDANT_PEOPLE = declare(
    "HOUSEHOLD_DEPENDANT_PEOPLE", 1.0, kind="initial_condition",
    unit="people besides the founder and the household's freedmen and slaves",
    source=None, confidence="D",
    why="How many kin and retainers a founder arrives keeping; each is a person with the full need floors. "
        "A real figure would come from the civilisation's household structure.")

AUTO_BUY_PEOPLE_CAPITAL_FLOOR_IN_PRICES = declare(
    "AUTO_BUY_PEOPLE_CAPITAL_FLOOR_IN_PRICES", 20.0, kind="temporary_heuristic",
    unit="base prices of one person", source=None, confidence="D",
    why="Capital the optimizer must hold, as a number of what one person costs to buy, before its "
        "standing policy buys people. A price multiple, so it follows the cost of a person in any coin. "
        "Tuned, not measured.")
AUTO_BUY_PEOPLE_CAPITAL_PER_PERSON_IN_PRICES = declare(
    "AUTO_BUY_PEOPLE_CAPITAL_PER_PERSON_IN_PRICES", 5.0, kind="temporary_heuristic",
    unit="base prices of one person", source=None, confidence="D",
    why="Capital kept in reserve per person the optimizer's standing policy buys, as a multiple of "
        "one person's base price, so a purchase never spends the purse down to the price. "
        "Tuned, not measured.")

AUTO_MANUMIT_ANNUAL_CHANCE = declare(
    "AUTO_MANUMIT_ANNUAL_CHANCE", 0.25, kind="temporary_heuristic",
    unit="dimensionless (yearly probability, optimizer only)",
    source=None, confidence="D",
    why="Yearly chance the optimizer's standing policy manumits some "
        "slaves, when it holds any. Invented frequency, not fitted to "
        "any attested manumission rate.")
AUTO_MANUMIT_SHARE_DIVISOR = declare(
    "AUTO_MANUMIT_SHARE_DIVISOR", 4, kind="temporary_heuristic",
    unit="dimensionless (divisor; frees roughly a quarter)",
    source=None, confidence="D",
    why="How large a bite auto-manumission takes when it fires - "
        "roughly a quarter of current slaves, at least one. Tuned, "
        "not measured.")

MARKET_PRESSURE_DECAY = declare(
    "MARKET_PRESSURE_DECAY", 0.55, kind="temporary_heuristic",
    unit="dimensionless (fraction kept per year)", source=None,
    confidence="D",
    why="How much of last year's market pressure (the price bump a "
        "household's own buying caused) survives into this year - "
        "sellers restock, so the pressure fades. Tuned, not measured.")
MARKET_PRESSURE_ANNUAL_FADE = declare(
    "MARKET_PRESSURE_ANNUAL_FADE", 2.0, kind="temporary_heuristic",
    unit="market-pressure points", source=None, confidence="D",
    why="Flat yearly reduction in market pressure on top of "
        "MARKET_PRESSURE_DECAY's proportional fade, so a small "
        "residual pressure reaches exactly zero rather than decaying "
        "forever. Tuned, not measured.")
