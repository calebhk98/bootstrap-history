"""Plagues come from the disease model, not from a dated hazard table (Complaint 490).

No game is built: a stand-in with the few members `DiseasePortMixin` reads carries a real civilisation file, the real
map and a real `Population`. Food is held at what the people need. The three gates: Rome's major epidemics do not land
in the same years in every run; a civilisation with no contact to a pathogen's source never gets it; the deaths an
epidemic causes are the model's own count, and no civilisation file carries a dated plague.
"""

QUICK_TOPIC = False

import functools
import json
import os
import types
import unittest

from sim.engine import disease_port, state
from sim.geography import api as geography
from sim.world import demography

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEEDS = (1, 2, 3, 4, 5, 6)
MAJOR_EPIDEMIC_SHARE_OF_PEOPLE = 0.005
PLAGUE_HAZARD_NAMES = ("Antonine plague", "Plague of Cyprian", "The Justinianic plague", "Recurrent plague", "Black Death",
                       "Black Death in Scandinavia", "The Great Plague of London", "The matlazahuatl of 1736")


@functools.lru_cache(maxsize=1)
def world_map():
    return geography.open_map()


def civilisation(civ_id):
    with open(os.path.join(ROOT, "data", "civilizations", civ_id + ".json"), encoding="utf-8") as handle:
        return json.load(handle)


class StandInSim(disease_port.DiseasePortMixin):
    """The members the disease step reads from `Sim`."""

    def __init__(self, civ, seed):
        self.civ = civ
        self.year = civ["year"]
        self.seed = seed
        self.world_map = world_map()
        self.state = types.SimpleNamespace(disease=state.DiseaseState())
        self.population = demography.Population.stationary(float(civ["population"]) / 50.0, seed=seed)
        self.food = (self.population.children * demography.CHILD_CALORIE_EQUIVALENT + self.population.working_age
                     + self.population.elderly * demography.ELDERLY_CALORIE_EQUIVALENT
                     ) * demography.SUBSISTENCE_CALORIES_PER_ADULT_EQUIVALENT_DAY

    def _farm_year_weather_seed(self, year, region=None):
        return self.seed * 7919 + year

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


def major_epidemic_years(rows):
    return {year for year, people, deaths in rows if deaths / people >= MAJOR_EPIDEMIC_SHARE_OF_PEOPLE}


@functools.lru_cache(maxsize=1)
def rome_ensemble():
    """{seed: (rows, saved disease state)} for Rome over five centuries from its start."""
    runs = {}
    for seed in SEEDS:
        sim = StandInSim(civilisation("rome_100ad"), seed)
        runs[seed] = (sim.run(500), sim.state.disease)
    return runs


class RomeEpidemicsAreDrawnTest(unittest.TestCase):
    def test_some_run_has_a_major_epidemic(self):
        self.assertTrue(any(major_epidemic_years(rows) for rows, _ in rome_ensemble().values()))

    def test_the_epidemic_years_differ_between_runs(self):
        year_sets = [frozenset(major_epidemic_years(rows)) for rows, _ in rome_ensemble().values()]
        self.assertGreater(len(set(year_sets)), 1, "every run has its major epidemics in the same years")

    def test_no_year_is_a_major_epidemic_in_every_run(self):
        year_sets = [major_epidemic_years(rows) for rows, _ in rome_ensemble().values()]
        self.assertFalse(set.intersection(*year_sets), "a year is an epidemic year in every run: a dated table")

    def test_the_first_arrival_is_not_in_the_same_year_in_every_run(self):
        first_years = {min((years[0] for years in disease.introduced.values()), default=None)
                       for _rows, disease in rome_ensemble().values()}
        self.assertGreater(len(first_years), 1)


    def test_pandemics_per_five_centuries_are_a_handful_and_the_empire_survives(self):
        deadly = []
        for rows, _disease in rome_ensemble().values():
            runs, current = 0, 0.0
            for _year, people, deaths in rows:
                current = current + deaths / people if deaths / people >= 0.002 else 0.0
                runs += 1 if current >= 0.1 and current - deaths / people < 0.1 else 0
            deadly.append(runs)
            self.assertGreater(min(people for _y, people, _d in rows) / rows[0][1], 0.05)
        self.assertTrue(1.0 <= sum(deadly) / len(deadly) <= 8.0, deadly)


class NoContactTest(unittest.TestCase):
    def mexica(self, carrier_modes):
        civ = civilisation("mexica_1500")
        civ["disease_exposure"]["outside_contact"][0]["carrier_modes"] = carrier_modes
        civ["disease_exposure"]["outside_contact"][0]["years"] = [civ["year"], civ["year"] + 400]
        return civ

    def test_a_source_no_route_joins_to_the_nation_never_gives_it_a_pathogen(self):
        for seed in SEEDS:
            sim = StandInSim(self.mexica([]), seed)
            sim.run(400)
            self.assertEqual(sim.state.disease.introduced, {}, "seed %d" % seed)
            self.assertEqual(sim.state.disease.deaths, {}, "seed %d" % seed)

    def test_the_same_source_reaches_the_nation_once_the_outsiders_bring_ships(self):
        arrivals = []
        for seed in SEEDS:
            sim = StandInSim(self.mexica(["sail"]), seed)
            sim.run(400)
            arrivals.append(bool(sim.state.disease.introduced))
        self.assertTrue(all(arrivals))

    def test_a_source_closer_by_route_gives_more_arrivals_than_a_far_one(self):
        civ = civilisation("rome_100ad")
        sim = StandInSim(civ, 1)
        near = {"tiles": ("iran_01",), "carrier_modes": (), "circulating": False, "first_year": None, "last_year": None,
                "pathogens": ("smallpox",)}
        far = dict(near, tiles=("china_60",))
        self.assertGreater(disease_port.DiseaseWorld(sim).contact_weight(near), disease_port.DiseaseWorld(sim).contact_weight(far))


class DeathsComeFromTheModelTest(unittest.TestCase):
    def test_the_deaths_handed_to_population_are_the_models_own_count(self):
        for seed in SEEDS[:3]:
            sim = StandInSim(civilisation("rome_100ad"), seed)
            handed = 0
            for _ in range(500):
                handed += sum(sim.disease_year(sim.food, sim.year).values())
                sim.year += 1
            self.assertEqual(handed, sum(sim.state.disease.deaths.values()), "seed %d" % seed)

    def test_no_civilisation_file_carries_a_dated_plague(self):
        directory = os.path.join(ROOT, "data", "civilizations")
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json") or name.startswith("_"):
                continue
            hazard_names = {hazard["name"] for hazard in civilisation(name[:-5]).get("hazards", [])}
            self.assertFalse(hazard_names & set(PLAGUE_HAZARD_NAMES), name)

    def test_every_civilisation_states_where_its_pathogens_live_not_when_they_come(self):
        for civ_id in ("rome_100ad", "england_1300", "norse_900ad", "han_china_100ad", "mexica_1500"):
            sources = civilisation(civ_id)["disease_exposure"]["outside_contact"]
            self.assertTrue(sources, civ_id)
            for source in sources:
                self.assertTrue(source["tiles"], civ_id)
                self.assertTrue(set(source["tiles"]) <= set(world_map().tiles), civ_id)


class SeatsFeelTheModelsDeathsTest(unittest.TestCase):
    def test_an_epidemic_year_cuts_the_founders_staff_by_the_share_of_working_age_people_killed(self):
        from .harness import unopened_sim
        game = unopened_sim(civ="rome_100ad", capital=1e6)
        game.scholars, game.artisans = 5000.0, 5000.0
        before = game.scholars
        share = game.epidemic_hits_seats({"working_age": game.population.working_age * 0.25}, game.year)
        self.assertAlmostEqual(share, 0.2, places=6)
        self.assertLess(game.scholars, before * 0.85)
        self.assertGreater(game.scholars, before * 0.7)

    def test_a_quiet_year_takes_nothing(self):
        from .harness import unopened_sim
        game = unopened_sim(civ="rome_100ad", capital=1e6)
        game.scholars = 5000.0
        self.assertEqual(game.epidemic_hits_seats({}, game.year), 0.0)
        self.assertEqual(game.scholars, 5000.0)


if __name__ == "__main__":
    unittest.main()
