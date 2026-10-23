"""Complaints 17 to 24: a mortality shock reaches the displayed population at once. `Sim._apply_population_mortality_shock` hands the
society's cohorts and the declared vulnerability ratios to the cut (`cut_cohorts`, replaced here by a recorder), and
`PopulationMixin.population_report` shows the cohort model's population against the civilisation's reference. Each runs on a stand-in `self`."""

QUICK_TOPIC = True

from types import SimpleNamespace
from unittest import mock

from .harness import check

import sim.engine.core as core
from sim.engine.core import Sim
from sim.labour.labour_population import PopulationMixin

# ---- the shock reaches the cohorts
recorded = []
population = object()
game = SimpleNamespace(population=population, _demography=SimpleNamespace(
    STARVATION_VULNERABILITY_CHILD=1.6, STARVATION_VULNERABILITY_WORKING_AGE=1.0, STARVATION_VULNERABILITY_ELDERLY=1.4))
with mock.patch.object(core, "cut_cohorts", lambda *arguments: recorded.append(arguments)):
    Sim._apply_population_mortality_shock(game, 0.28)
check("the shock cuts the society's own cohorts by the share, with the declared vulnerability of each age", recorded == [(population, 0.28, 1.6, 1.0, 1.4)], recorded)


# ---- the screen shows the cohort model's population against the reference
class Labour(PopulationMixin):
    def __init__(self, total, reference=1000.0):
        self._world = SimpleNamespace(civ={"id": "rome_100ad", "short_name": "Rome", "population": reference}, population=SimpleNamespace(total=total),
                                      urban_fraction=lambda: 0.2, wages={}, plain_number=lambda number: "%d" % number)

    def home_town_population_estimate(self):
        return 100.0


report = Labour(total=720.0).population_report()
check("after a shock the displayed population is the cohort model's, below the reference", report["population"] == 720
      and report["reference_population_before_simulated_changes"] == 1000 and report["population"] < report["reference_population_before_simulated_changes"], report)
check("the change from the reference is the share lost", report["population_change_from_reference"] == -0.28, report)
check("the urban estimate follows the displayed population", report["urban_population_estimate"] == 144, report)
check("with no reference population the change is zero", Labour(total=720.0, reference=0.0).population_report()["population_change_from_reference"] == 0.0, None)
