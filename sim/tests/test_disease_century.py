"""The disease model alone, a century of sub-year steps, on the Mexica start's population (Complaint 386).

No game is built: a stand-in with the few members `DiseasePortMixin` reads carries the real civilisation file,
a real `Population` and the real pathogen files. Food is held at what the opening people need, so the people
who survive an epidemic meet the same land they had; births and baseline deaths come from `Population.step`.
The gates are the validation envelope of Complaints/reports/epidemic-model-research.md section 11.5, stated as
ranges for a distribution, never as targets the model was tuned to.
"""

QUICK_TOPIC = False

import functools
import json
import os
import types
import unittest

from sim.engine import disease_port, state
from sim.world import demography

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEEDS = (1, 2, 3)
YEARS_AFTER_CONTACT = 75
# McCaa's table of published estimates for the Indian population of Mexico, 1519 to 1595: the lowest and the
# highest decline any author gives (report section 11.5), as shares of the population at contact.
PUBLISHED_DECLINE_LOWEST = 0.22
PUBLISHED_DECLINE_HIGHEST = 0.96
# Cook and Borah's maximalist series (a summary seen, not the volume; report section 11.5) keeps 6.3 of 25.2
# million 30 years in. Twenty years in, a run below that share is near extinction, which Complaint 386 was
# (a few hundred left of five million).
MAXIMALIST_SURVIVING_SHARE_AFTER_30_YEARS = 6.3 / 25.2


class StandInSim(disease_port.DiseasePortMixin):
    """The members the disease step reads from `Sim`."""

    def __init__(self, civ, seed):
        self.civ = civ
        self.year = civ["year"]
        self.seed = seed
        self.state = types.SimpleNamespace(disease=state.DiseaseState())
        self.population = demography.Population.stationary(float(civ["population"]), seed=seed)
        self.food = self._need()

    def _need(self):
        return (self.population.children * demography.CHILD_CALORIE_EQUIVALENT + self.population.working_age
                + self.population.elderly * demography.ELDERLY_CALORIE_EQUIVALENT
                ) * demography.SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY

    def _farm_year_weather_seed(self, year, region=None):
        return self.seed * 7919 + year

    def _effect_terms(self, channel):
        return []

    def civ_diffusion(self, node_id):
        return 0.0

    def run(self, years):
        """[(year, people, deaths from disease)] for `years` years from the start year."""
        rows = []
        for _ in range(years):
            deaths = self.disease_year(self.food, self.year)
            self.population.step(self.food, jitter=False, epidemic_deaths=deaths)
            rows.append((self.year, self.population.total, sum(deaths.values())))
            self.year += 1
        return rows


def mexica():
    with open(os.path.join(ROOT, "data", "civilizations", "mexica_1500.json"), encoding="utf-8") as handle:
        civ = json.load(handle)
    civ["year"] = civ["disease_exposure"]["outside_contact"][0]["years"][0] - 1
    return civ


@functools.lru_cache(maxsize=1)
def century_runs():
    """{seed: (people at the start, [(year, people, deaths)], saved disease state)}; computed once per process."""
    runs = {}
    for seed in SEEDS:
        sim = StandInSim(mexica(), seed)
        start = sim.population.total
        runs[seed] = (start, sim.run(100), sim.state.disease)
    return runs


class CenturyTest(unittest.TestCase):
    @property
    def runs(self):
        return century_runs()

    def contact_row(self, seed):
        start, rows, disease_state = self.runs[seed]
        first_year = min(years[0] for years in disease_state.introduced.values())
        return first_year, [row for row in rows if row[0] >= first_year]

    def test_the_scenario_seeds_pathogens_the_files_define(self):
        for seed in SEEDS:
            introduced = self.runs[seed][2].introduced
            self.assertTrue(introduced, "no pathogen reached the nation in seed %d" % seed)
            self.assertLessEqual(set(introduced), set(disease_port.pathogens()))

    def test_no_seed_nears_extinction_within_twenty_years_of_contact(self):
        for seed in SEEDS:
            _first, rows = self.contact_row(seed)
            lowest = min(people for _year, people, _deaths in rows[:20])
            self.assertGreater(lowest / rows[0][1], MAXIMALIST_SURVIVING_SHARE_AFTER_30_YEARS, "seed %d" % seed)

    def test_the_deepest_fall_in_seventy_five_years_is_inside_the_published_span(self):
        for seed in SEEDS:
            _first, rows = self.contact_row(seed)
            at_contact = rows[0][1]
            deepest = 1.0 - min(people for _year, people, _deaths in rows[:YEARS_AFTER_CONTACT]) / at_contact
            self.assertGreaterEqual(deepest, PUBLISHED_DECLINE_LOWEST, "seed %d" % seed)
            self.assertLessEqual(deepest, PUBLISHED_DECLINE_HIGHEST, "seed %d" % seed)

    def test_the_seeds_do_not_all_land_on_one_value(self):
        falls = []
        for seed in SEEDS:
            _first, rows = self.contact_row(seed)
            falls.append(1.0 - min(people for _y, people, _d in rows[:YEARS_AFTER_CONTACT]) / rows[0][1])
        self.assertGreater(max(falls) - min(falls), 0.005)

    def test_later_waves_kill_far_fewer_than_the_first(self):
        # The failing behaviour of the authored hazard: a wave with no memory of who is immune.
        for seed in SEEDS:
            _first, rows = self.contact_row(seed)
            deaths = [row[2] for row in rows]
            self.assertLess(sum(deaths[40:]), sum(deaths[:40]))


if __name__ == "__main__":
    unittest.main()
