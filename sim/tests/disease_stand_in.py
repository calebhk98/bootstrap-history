"""A stand-in for the views the disease module reads, so the disease model runs on a real civilisation file, the
real map and a real `Population` with no game built. Food is held at what the people need."""
import functools
import json
import os

from sim.disease.api import RunEpidemicYear, nation_tuning
from sim.disease.module import Disease
from sim.disease.state import DiseaseWorld
from sim.geography import api as geography
from sim.tests import module_harness
from sim.world import demography

BANDS = nation_tuning.BANDS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEEDS = (1, 2, 3, 4, 5, 6)


@functools.lru_cache(maxsize=1)
def world_map():
    return geography.open_map()


def civilisation(civ_id):
    with open(os.path.join(ROOT, "data", "civilizations", civ_id + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


class StandInSim:
    """A disease module (built by `module_harness`) over a real civilisation file and `Population`, standing in for the game
    members its views answer from. `module` is the module; `module.world` is its saved state."""

    def __init__(self, civ, seed, people_share=1.0 / 50.0):
        self.civ = civ
        self.year = civ["year"]
        self.seed = seed
        self.population = demography.Population.stationary(float(civ["population"]) * people_share, seed=seed)
        self.food = (self.population.children * demography.CHILD_CALORIE_EQUIVALENT + self.population.working_age
                     + self.population.elderly * demography.ELDERLY_CALORIE_EQUIVALENT
                     ) * demography.SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY
        self.module = module_harness.build(Disease, world=DiseaseWorld(), views={
            "year": lambda: self.year, "civilisation": civ, "legacy_world_map": world_map(),
            "weather_seed": lambda year, region=None: self.seed * 7919 + year,
            "people_by_band": lambda: {band: float(getattr(self.population, band)) for band in BANDS},
            "nutrition_ratio": lambda food: self.population.nutrition_ratio(food),
            "working_age": lambda: self.population.working_age,
            "legacy_regions_of_people": lambda: None, "regional_flows_last_year": lambda: None, "goods_carried_last_year": {},
            "urban_fraction": lambda: self.urban_fraction(),
            "home_tiles_held": lambda: geography.tiles_held(civ, world_map()),
            "held_techniques": lambda include_starting: frozenset(civ.get("starting_techs", ())),
            "effect_terms": lambda channel: [], "civ_diffusion": lambda node_id: 0.0})

    def urban_fraction(self):
        return float(self.civ.get("urban_fraction", 0.0))

    def disease_year(self, food, year):
        return self.module.run_epidemic_year(RunEpidemicYear(food, year))

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
