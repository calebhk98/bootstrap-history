"""The numbers literacy, schooling, trade absorption and diffusion are tuned with (each a declared heuristic or source)."""
from sim.constants import declare

# ---- literacy: what limits it and how fast schooling closes the gap ----

UNABLE_TO_READ_SHARE = declare(
    "UNABLE_TO_READ_SHARE", 0.01, kind="temporary_heuristic",
    unit="dimensionless (share of any class, 0..1)", source=None,
    confidence="D",
    why="Share of people who cannot learn to read at all (severe "
        "cognitive or sensory impairment), so no ceiling reaches 1.0. "
        "A small round figure, not taken from a survey.")
FARM_CHILDREN_KEPT_FROM_SCHOOL = declare(
    "FARM_CHILDREN_KEPT_FROM_SCHOOL", 0.8, kind="temporary_heuristic",
    unit="dimensionless (share of farm households' children, 0..1)",
    source=None, confidence="D",
    why="Share of a farming household's children whose labour the farm "
        "needs, so they cannot be spared for a classroom. Multiplied by "
        "the farm share of hours; a round figure, not measured.")
GENERATION_YEARS = declare(
    "GENERATION_YEARS", 25, kind="temporary_heuristic", unit="years",
    source=None, confidence="C",
    why="Length of a human generation; spaces literacy census messages "
        "and decides when schooling has run for a generation.")
# per unit of schooling flow, per year; the flow comes from the schools and academies running
LITERACY_GROWTH_RATE_GENERAL = declare(
    "LITERACY_GROWTH_RATE_GENERAL", 0.006, kind="temporary_heuristic",
    unit="dimensionless per unit of schooling flow, per year",
    source=None, confidence="D",
    why="How fast general literacy closes the gap to its ceiling per "
        "unit of schooling flow: at flow 1.0 "
        "this is a ~167-year time constant, requiring sustained "
        "investment across generations; at flow ~7 it falls to about "
        "24 years. Tuned to hit those two illustrative time constants, "
        "not fitted to any measured literacy-growth curve.")
LITERACY_GROWTH_RATE_ELITE = declare(
    "LITERACY_GROWTH_RATE_ELITE", 0.010, kind="temporary_heuristic",
    unit="dimensionless per unit of schooling flow, per year",
    source=None, confidence="D",
    why="How fast elite literacy closes its gap - faster than the "
        "general rate because the propertied class an academy draws "
        "on is a far smaller pool to reach. "
        "Chosen so Rome's own high starting elite literacy moves only "
        "slightly over a run; not fitted to a measured curve.")
PRINTING_DIFFUSION_SCHOOLING_BOOST = declare(
    "PRINTING_DIFFUSION_SCHOOLING_BOOST", 0.5, kind="temporary_heuristic",
    unit="dimensionless (multiplies information_diffusion_index)",
    source=None, confidence="D",
    why="How much faster schooling closes literacy's gap once "
        "printing has diffused past the founder's own workshop - "
        "texts actually exist to teach from. Tuned to be a real, "
        "visible boost without letting a country of diffused printing "
        "teach anyone by itself (still requires flow>0); not measured.")

# ---- a trade the founder taught becomes a trade the society has ----

TRADE_ABSORPTION_BASE_YEARS = declare(
    "TRADE_ABSORPTION_BASE_YEARS", 110.0, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Years before a founder-taught trade becomes endemic to the "
        "society, absent any schooling flow: an educated society "
        "eventually produces its own electricians. Round figure chosen to put "
        "the total span at about a century; not fitted to any "
        "attested trade-naturalisation record.")
TRADE_ABSORPTION_MIN_YEARS = declare(
    "TRADE_ABSORPTION_MIN_YEARS", 35.0, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Floor on how fast schooling can make a trade endemic, however "
        "much is invested - roughly one working lifetime, so a trade "
        "taught last year cannot already be 'something this society "
        "has always had'. Round figure, not measured.")
TRADE_DIFFUSION_APPROACH_RATE = declare(
    "TRADE_DIFFUSION_APPROACH_RATE", 0.05, kind="temporary_heuristic",
    unit="fraction of the gap per year", source=None, confidence="D",
    why="Yearly approach rate of an endemic trade's workforce toward "
        "its literate_capacity() ceiling: 5% a year means a half-life "
        "of about 14 years, so from a standing start of one workshop "
        "the whole span is century-scale. Tuned to that target pace, "
        "not measured.")

# ---- the founder's venture leaks to imitators ----

VENTURE_DIFFUSION_HALF_LIFE_YEARS = declare(
    "VENTURE_DIFFUSION_HALF_LIFE_YEARS", 40.0, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Years for half of a visibly-run venture's original edge to "
        "leak to competitors, absent any publishing or literacy "
        "effect - pitched at the low end of 'a generation or two'. "
        "Chosen to sit in that plausible range, "
        "not fitted to any measured rate of competitive imitation.")
VENTURE_DIFFUSION_CAP = declare(
    "VENTURE_DIFFUSION_CAP", 0.65, kind="temporary_heuristic",
    unit="dimensionless (share, 0..1)", source=None, confidence="D",
    why="However long a venture has been visibly run, some of a "
        "first-mover's edge never leaves - customers, reputation, a "
        "head start on the next improvement. "
        "Capped so this is never read as eventually reaching 1.0; not "
        "measured.")
LITERACY_DIFFUSION_PACE_BASE = declare(
    "LITERACY_DIFFUSION_PACE_BASE", 0.7, kind="temporary_heuristic",
    unit="dimensionless (pace multiplier floor)", source=None,
    confidence="D",
    why="Floor on the literacy-driven diffusion-pace multiplier, at "
        "the reference literacy level - a society at or below "
        "reference literacy still diffuses at 70% pace, never zero. "
        "Shared with the category pace; tuned, not measured.")
LITERACY_DIFFUSION_PACE_SPAN = declare(
    "LITERACY_DIFFUSION_PACE_SPAN", 0.3, kind="temporary_heuristic",
    unit="dimensionless (pace multiplier span above the floor)",
    source=None, confidence="D",
    why="How much extra diffusion pace a more literate society buys "
        "on top of LITERACY_DIFFUSION_PACE_BASE, up to "
        "LITERACY_DIFFUSION_PACE_CAP_RATIO times the reference "
        "literacy. Shared with the category pace; tuned, not measured.")
LITERACY_DIFFUSION_PACE_CAP_RATIO = declare(
    "LITERACY_DIFFUSION_PACE_CAP_RATIO", 2.0, kind="temporary_heuristic",
    unit="dimensionless (multiple of reference literacy)", source=None,
    confidence="D",
    why="Ceiling on how much a society's literacy, relative to the "
        "reference level, can boost diffusion pace - twice the "
        "reference literacy is treated as maximally literate for this "
        "purpose. Shared with the category pace; tuned, not measured.")
DIFFUSION_PACE_FLOOR = declare(
    "DIFFUSION_PACE_FLOOR", 0.4, kind="temporary_heuristic",
    unit="dimensionless (minimum diffusion pace)", source=None,
    confidence="D",
    why="Floor on the overall diffusion pace divisor, so a society "
        "with no accelerants at all still diffuses at some minimum "
        "rate rather than the half-life going to infinity. Shared "
        "between the venture share and the category pace; tuned, not "
        "measured.")

# ---- what a completed technology does to the whole country, by category ----
# Food is faster than medical and information on purpose: a better crop is something a neighbour can see working and
# copy without reading a word, where germ theory or a press depends on somebody publishing and somebody literate.

DIFFUSION_HALF_LIFE_FOOD_YEARS = declare(
    "DIFFUSION_HALF_LIFE_FOOD_YEARS", 25.0, kind="temporary_heuristic",
    unit="years", source="Nunn and Qian (2011) describe the potato's "
         "spread across Europe as a matter of generations rather than "
         "years.",
    confidence="C",
    why="Years for half of a newly-completed food technology to "
        "spread through the wider society, absent any literacy or "
        "state-capacity effect - a better crop is something a "
        "neighbour can see working and copy without reading a word. "
        "Pitched at the low end of 'a few decades' to match the cited "
        "source's description, not fitted to it numerically.")
DIFFUSION_HALF_LIFE_MEDICAL_YEARS = declare(
    "DIFFUSION_HALF_LIFE_MEDICAL_YEARS", 35.0, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Years for half of a newly-completed medical technology to "
        "spread - slower than food or military because germ theory or "
        "a vaccine depends on publishing and on somebody literate "
        "enough to read it. Tuned, not measured.")
DIFFUSION_HALF_LIFE_INFORMATION_YEARS = declare(
    "DIFFUSION_HALF_LIFE_INFORMATION_YEARS", 30.0, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="Years for half of a newly-completed information technology "
        "(printing and the like) to spread through society. Tuned, "
        "not measured.")

# ---- disease and war: what a diffused technique relieves ----

MEDICAL_COMPLIANCE_BASE = declare(
    "MEDICAL_COMPLIANCE_BASE", 0.5, kind="temporary_heuristic",
    unit="dimensionless (share following public-health guidance at "
         "zero state reach)", source=None, confidence="D",
    why="Share of people who follow quarantine and hygiene guidance "
        "with no administration behind it; state reach supplies "
        "the rest. Not derived from a behavioural model.")
STATE_MIL_RELIEF_PER_WEAPON_OUTPUT = declare(
    "STATE_MIL_RELIEF_PER_WEAPON_OUTPUT", 0.04, kind="temporary_heuristic",
    unit="dimensionless (share of the remaining output-shock harm one held "
         "weapon removes)", source=None, confidence="D",
    why="What the state's armies gain from one more of the founder's weapons "
        "against an output-crushing war; smaller than the sack figure because "
        "output shocks have other causes besides invasion. Tuned, not measured.")
STATE_MIL_RELIEF_PER_WEAPON_SACK = declare(
    "STATE_MIL_RELIEF_PER_WEAPON_SACK", 0.06, kind="temporary_heuristic",
    unit="dimensionless (share of the remaining sack-chance harm one held "
         "weapon removes)", source=None, confidence="D",
    why="What the state's armies gain from one more of the founder's weapons "
        "against being sacked by tribes. Tuned, not measured.")
