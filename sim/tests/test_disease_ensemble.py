"""Whole Mexica games on the agent economy, checked against the validation envelope of
Complaints/reports/epidemic-model-research.md section 11.5 (Complaint 386's evidence command).

SLOW: each game builds the whole agent economy (over ten minutes cold) and plays decades. Left out of the quick
tier; run with `python3 -m sim.tests --slow --only disease_ensemble`. It was written alongside the wiring but not
run there; the fast stand-in for the same gates is test_disease_century.py. Prints the people per year of each
seed so a run can be compared before and after a change. The gates are ranges for a distribution, not targets."""

QUICK_TOPIC = False

import random
import unittest

from sim.engine.ui_port import Sim, load, load_civ

SEEDS = (1, 2, 3)
YEARS = 60
# Cook and Borah's maximalist series keeps 6.3 of 25.2 million 30 years in (report section 11.5); below that share
# twenty years after contact a run is near extinction, which is what Complaint 386 reported.
MAXIMALIST_SURVIVING_SHARE_AFTER_30_YEARS = 6.3 / 25.2
PUBLISHED_DECLINE_HIGHEST = 0.96


def play(seed):
    """[(year, people)] for a Mexica game with the agent economy, and the saved disease state."""
    _tree, _prices, nodes, _wages, _goods = load()
    game = Sim(nodes, [], random.Random(seed), events=False, manual=True, civ=load_civ("mexica_1500"),
               cfg={"agent_economy": True})
    people = []
    for _ in range(YEARS):
        game.step()
        people.append((game.year, game.population.total))
    return people, game.state.disease


class EnsembleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs = {seed: play(seed) for seed in SEEDS}
        for seed, (people, disease_state) in cls.runs.items():
            print("seed %d introduced %s deaths %s" % (seed, disease_state.introduced, disease_state.deaths))
            print("seed %d people by year: %s" % (seed, [round(count) for _year, count in people]))

    def after_contact(self, seed):
        people, disease_state = self.runs[seed]
        first_year = min(years[0] for years in disease_state.introduced.values())
        return [count for year, count in people if year >= first_year]

    def test_a_pathogen_reaches_every_seed(self):
        for seed in SEEDS:
            self.assertTrue(self.runs[seed][1].introduced, "seed %d" % seed)

    def test_no_seed_nears_extinction_within_twenty_years_of_contact(self):
        for seed in SEEDS:
            counts = self.after_contact(seed)
            self.assertGreater(min(counts[:20]) / counts[0], MAXIMALIST_SURVIVING_SHARE_AFTER_30_YEARS, "seed %d" % seed)

    def test_the_fall_stays_inside_the_published_span(self):
        for seed in SEEDS:
            counts = self.after_contact(seed)
            self.assertLessEqual(1.0 - min(counts) / counts[0], PUBLISHED_DECLINE_HIGHEST, "seed %d" % seed)

    def test_disease_killed_people_and_not_everyone(self):
        for seed in SEEDS:
            deaths = sum(self.runs[seed][1].deaths.values())
            self.assertGreater(deaths, 0, "seed %d" % seed)
            self.assertLess(deaths, 5 * self.runs[seed][0][0][1], "seed %d" % seed)


if __name__ == "__main__":
    unittest.main()
