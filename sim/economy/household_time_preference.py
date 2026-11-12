"""The discount rate a household applies to waiting: the one rate the households' lending, storing and
training decisions share. A leaf module, so the modules that read it import it without a cycle."""
from sim.constants import declare

HOUSEHOLD_TIME_PREFERENCE = declare(
    "HOUSEHOLD_TIME_PREFERENCE", 0.05, kind="temporary_heuristic",
    unit="share a year", source=(
        'Clark, Econ 110A chapter 9 "Time Preference and Interest Rates" (faculty.econ.ucdavis.edu/faculty/gclark/'
        'ecn110a/readings/chapter9.pdf, opened): Table 2, rent-charge returns in England, 4.0 to 6.0 percent in '
        'every half-century from 1451 to 1800 (France 4.2 to 9.2); the same chapter cites anthropologists for a '
        'Malthusian-era time preference of 2.3 to 2.8 percent, below what was observed. The value is the safe '
        'rate observed in England after 1450, a lender\'s lowest ask, not a measured household time preference '
        'and not Roman or any other civilisation\'s.'), confidence="C",
    why="A household lends its savings only for at least what it gives up by waiting, on top of what "
        "inflation it expects takes from them. The figure is a common assumption in growth models, "
        "not measured for any society here; default risk is priced separately by the credit market.",
    retire="Complaints/607: the opening holds the wealth its households want and saving has a user")
