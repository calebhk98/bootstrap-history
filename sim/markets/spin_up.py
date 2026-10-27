"""The hidden spin-up years of the agent economy's opening: their bounds, the tolerance they run to and how the environment shortens
them. Pure declarations and arithmetic, so the tools that read them need not load the port."""
import os

from sim.constants import declare
from sim.prices.api import solve_cache

SPIN_UP_CACHE_DIRECTORY = os.path.join(os.path.dirname(solve_cache.DEFAULT_CACHE_DIRECTORY), "agent_economy")
SPIN_UP_TOLERANCE = declare(
    "SPIN_UP_TOLERANCE", 0.02, kind="temporary_heuristic",
    unit="largest yearly relative change of the price level and the main prices", source=None, confidence="D",
    why="The hidden years before a game run until the economy stops moving more than this a year, so the "
        "first year the player sees is the economy's own and not the price solver's. A looser figure "
        "starts sooner and further from settled.")
SPIN_UP_MAXIMUM_YEARS = declare(
    "SPIN_UP_MAXIMUM_YEARS", 30, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="A bound on the hidden years, so a economy that keeps moving still starts in a known time.")
SPIN_UP_TRIMMED_YEARS = declare(
    "SPIN_UP_TRIMMED_YEARS", 15, kind="temporary_heuristic",
    unit="years", source=None, confidence="D",
    why="After the workforce is trimmed to the hours employers want, the skilled trades need a few years for "
        "wages to leave the market's ceiling and for entry to fill the thinned trades. Their wages swing by "
        "multiples a year in thin labour markets and never meet a tolerance, so the stage is a fixed length, "
        "as long as that takes and no longer (shorter lengths left trades glutted or the staffing wage "
        "reference too high in some civilisations; found by trying lengths against the opening-workforce tests). "
        "A model of hiring and training would derive it per trade.")
SPIN_UP_MEASURED_YEARS = declare(
    "SPIN_UP_MEASURED_YEARS", 4, kind="temporary_heuristic",
    unit="consecutive final years", source=None, confidence="D", retire="Complaints/473",
    why="The opening's reported `spin_up_result` compares this many consecutive last years of the trimmed stage "
        "(one fewer changes), so one quiet year between swings is not read as settled.")
# `<first-stage years>,<trimmed years>` in this variable shortens the spin-up (the test suite sets it); the years
# then enter the cache key, so a full game never reads a shortened record.
SPIN_UP_YEARS_ENV = "ROME_SPIN_UP_YEARS"


def spin_up_years():
    """(most first-stage years, trimmed years): SPIN_UP_YEARS_ENV when set, else the declared bounds."""
    named = os.environ.get(SPIN_UP_YEARS_ENV)
    if named:
        first, trimmed = (int(part) for part in named.split(","))
        return first, trimmed
    return int(SPIN_UP_MAXIMUM_YEARS), int(SPIN_UP_TRIMMED_YEARS)

