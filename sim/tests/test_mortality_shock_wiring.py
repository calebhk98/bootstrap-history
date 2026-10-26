"""Complaints 17 to 24: a mortality shock reaches the displayed population at once. The demography module's `cut_population` cuts the
society's cohorts by the share, unevenly by the declared vulnerability of each age, and
`PopulationMixin.population_report` shows the cohort model's population against the civilisation's reference."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.demography.api import CutPopulation
from sim.demography.module import Demography
from sim.demography.state import DemographyWorld
from sim.labour.labour_population import PopulationMixin
from sim.tests import module_harness
from sim.world import demography

# ---- the shock reaches the cohorts
world = DemographyWorld(pop_children=300.0, pop_working_age=600.0, pop_elderly=100.0)
module = module_harness.build(Demography, world=world)
module.cut_population(CutPopulation(0.28))
total = world.pop_children + world.pop_working_age + world.pop_elderly
check("the shock takes the share of the whole from the society's own cohorts", abs(total - 1000.0 * 0.72) < 1e-6, total)
lost = (1.0 - world.pop_children / 300.0, 1.0 - world.pop_working_age / 600.0, 1.0 - world.pop_elderly / 100.0)
check("children and the elderly lose a larger share than the whole, working-age adults a smaller", lost[0] > 0.28 and lost[2] > 0.28 > lost[1], lost)
check("the cut is the declared ratio between the ages",
      abs((1.0 - world.pop_children / 300.0) / (1.0 - world.pop_working_age / 600.0)
          - demography.STARVATION_VULNERABILITY_CHILD / demography.STARVATION_VULNERABILITY_WORKING_AGE) < 1e-9, None)


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
