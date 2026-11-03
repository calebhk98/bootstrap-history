"""The discount rate a household applies to waiting: the one rate the households' lending, storing and
training decisions share. A leaf module, so the modules that read it import it without a cycle."""
from sim.constants import declare

HOUSEHOLD_TIME_PREFERENCE = declare(
    "HOUSEHOLD_TIME_PREFERENCE", 0.05, kind="temporary_heuristic",
    unit="share a year", source=(
        'No source found: a discount rate read from a source that could be opened was not found. Not '
        'measured for any pre-modern society.'), confidence="D",
    why="A household lends its savings only for at least what it gives up by waiting, on top of what "
        "inflation it expects takes from them. The figure is a common assumption in growth models, "
        "not measured for any society here; default risk is priced separately by the credit market.",
    retire="Complaints/607: the opening holds the wealth its households want and saving has a user")
