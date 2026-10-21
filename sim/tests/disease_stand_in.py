"""A stand-in for the members `DiseasePortMixin` reads from `Sim`, so the disease model runs on a real civilisation file, the
real map and a real `Population` with no game built. Food is held at what the people need."""
import functools
import json
import os
import types

from sim.engine import disease_port, state
from sim.geography import api as geography
from sim.world import demography

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEEDS = (1, 2, 3, 4, 5, 6)


@functools.lru_cache(maxsize=1)
def world_map():
    return geography.open_map()


def civilisation(civ_id):
    with open(os.path.join(ROOT, "data", "civilizations", civ_id + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


class StandInSim(disease_port.DiseasePortMixin):
    """The members the disease step reads from `Sim`."""

    def __init__(self, civ, seed, people_share=1.0 / 50.0):
        self.civ = civ
        self.year = civ["year"]
        self.seed = seed
        self.world_map = world_map()
        self.state = types.SimpleNamespace(disease=state.DiseaseState())
        self.population = demography.Population.stationary(float(civ["population"]) * people_share, seed=seed)
        self.food = (self.population.children * demography.CHILD_CALORIE_EQUIVALENT + self.population.working_age
                     + self.population.elderly * demography.ELDERLY_CALORIE_EQUIVALENT
                     ) * demography.SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY

    def _farm_year_weather_seed(self, year, region=None):
        return self.seed * 7919 + year

    def urban_fraction(self):
        return float(self.civ.get("urban_fraction", 0.0))

    def _effect_terms(self, channel):
        return []

    def civ_diffusion(self, node_id):
        return 0.0

    def held_and_running(self):
        return frozenset(self.civ.get("starting_techs", ()))

    def run(self, years):
        """[(year, people before, deaths from disease)] for `years` years."""
        rows = []
        for _ in range(years):
            people = self.population.total
            deaths = self.disease_year(self.food, self.year)
            self.population.step(self.food, jitter=False, epidemic_deaths=deaths)
            rows.append((self.year, people, sum(deaths.values())))
            self.year += 1
        return rows


def mexica_with_source(carrier_modes):
    """Mexica with its outside source of disease reaching the nation by these carrier modes, for four centuries."""
    civ = civilisation("mexica_1500")
    civ["disease_exposure"]["outside_contact"][0]["carrier_modes"] = carrier_modes
    civ["disease_exposure"]["outside_contact"][0]["years"] = [civ["year"], civ["year"] + 400]
    return civ
