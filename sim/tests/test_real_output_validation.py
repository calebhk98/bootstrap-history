"""BASELINE VALIDATION (CLAUDE.md 4.2, Complaint 473): a population that falls without a technique lowers output with the
people and leaves output per head within a stated band of an undisturbed run. Fails on 473 while the economy does not settle.
The arithmetic and wiring are in test_real_output_measure and test_real_output_scenario."""
from .harness import *  # noqa: F401,F403
from .real_output_helpers import close_years

# ---: a population that falls without a technique lowers output with the people
# and leaves output per head within a quarter of where it would have been. The quarter is a declared band, not a
# sourced figure. The reference is a run of the same game with no fall, closed the same number of years: the first
# settled year is a ramp (the economy's plants and stocks are still settling), so it is no stand-in for "where it was".
PER_HEAD_BAND = 0.25
YEARS_AFTER_FALL = 2
undisturbed = sim(civ="rome_100ad", capital=1e9)
close_years(undisturbed, 1 + YEARS_AFTER_FALL)
fallen = sim(civ="rome_100ad", capital=1e9)
close_years(fallen, 1)
people_before = fallen.population.total
fallen._apply_population_mortality_shock(0.4)
close_years(fallen, YEARS_AFTER_FALL)
check("validation: a population fall without a technique lowers real output against the same years undisturbed",
      fallen.real_output_hours() < undisturbed.real_output_hours(),
      (undisturbed.real_output_hours(), fallen.real_output_hours()))
check("validation (Complaint 473): ...but not output per head, which stays near where it would have been",
      abs(fallen.real_output_per_head() / undisturbed.real_output_per_head() - 1.0) <= PER_HEAD_BAND,
      (undisturbed.real_output_per_head(), fallen.real_output_per_head(), people_before, fallen.population.total))
