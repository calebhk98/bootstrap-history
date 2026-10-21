"""SCENARIO (Complaint 640): a mortality shock reaches the displayed population at once (playtest complaints 17 through 24).
The other rules of those complaints are called on built inputs in test_complaints_17_24."""
from .harness import *  # noqa: F401,F403

# A mortality shock reaches the displayed population at once. The wage half is held by
# demographics_and_plague ("wage_index > normal * 1.2" after a shock) and the share removed by cross_system_invariants.
_plague = sim(civ="rome_100ad")
_plague._apply_population_mortality_shock(0.28)
_plague._refresh_demographic_indexes(_plague.year)
_population = _plague.labour.population_report()
check("scenario: plague mortality immediately lowers displayed current population",
      _population["population"] <
      _population["reference_population_before_simulated_changes"], _population)
