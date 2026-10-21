"""Baseline validation (CLAUDE.md 4.2, Complaint 490; slow-only): plagues come from the disease model, not from a dated table.

Ensembles on the stand-in sim (`disease_stand_in.StandInSim`, no game): Rome's major epidemics do not land in the same years in
every run and are a handful in five centuries with the empire surviving; the same outside source reaches the nation in every run
once the outsiders bring ships; over several runs the deaths handed to the population are the model's own count. A failure means
a dated table crept back or the draw stopped following contact (Complaint 490). The rules are in test_plagues_from_contact."""

import functools
import unittest

from sim.tests.disease_stand_in import SEEDS, StandInSim, civilisation, mexica_with_source

MAJOR_EPIDEMIC_SHARE_OF_PEOPLE = 0.005


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
        self.assertTrue(any(major_epidemic_years(rows) for rows, _ in rome_ensemble().values()),
                        "baseline validation, Complaint 490")

    def test_the_epidemic_years_differ_between_runs(self):
        year_sets = [frozenset(major_epidemic_years(rows)) for rows, _ in rome_ensemble().values()]
        self.assertGreater(len(set(year_sets)), 1, "baseline validation, Complaint 490: every run has its major epidemics in the same years")

    def test_no_year_is_a_major_epidemic_in_every_run(self):
        year_sets = [major_epidemic_years(rows) for rows, _ in rome_ensemble().values()]
        self.assertFalse(set.intersection(*year_sets),
                         "baseline validation, Complaint 490: a year is an epidemic year in every run: a dated table")

    def test_the_first_arrival_is_not_in_the_same_year_in_every_run(self):
        first_years = {min((years[0] for years in disease.introduced.values()), default=None)
                       for _rows, disease in rome_ensemble().values()}
        self.assertGreater(len(first_years), 1, "baseline validation, Complaint 490")

    def test_pandemics_per_five_centuries_are_a_handful_and_the_empire_survives(self):
        deadly = []
        for rows, _disease in rome_ensemble().values():
            runs, current = 0, 0.0
            for _year, people, deaths in rows:
                current = current + deaths / people if deaths / people >= 0.002 else 0.0
                runs += 1 if current >= 0.1 and current - deaths / people < 0.1 else 0
            deadly.append(runs)
            self.assertGreater(min(people for _y, people, _d in rows) / rows[0][1], 0.05, "baseline validation, Complaint 490")
        self.assertTrue(1.0 <= sum(deadly) / len(deadly) <= 8.0, ("baseline validation, Complaint 490", deadly))


class ContactEnsembleTest(unittest.TestCase):
    def test_the_same_source_reaches_the_nation_once_the_outsiders_bring_ships(self):
        arrivals = []
        for seed in SEEDS:
            sim = StandInSim(mexica_with_source(["sail"]), seed)
            sim.run(400)
            arrivals.append(bool(sim.state.disease.introduced))
        self.assertTrue(all(arrivals), "baseline validation, Complaint 490")

    def test_the_deaths_handed_to_population_are_the_models_own_count_in_every_run(self):
        for seed in SEEDS[:3]:
            sim = StandInSim(civilisation("rome_100ad"), seed)
            handed = 0
            for _ in range(500):
                handed += sum(sim.disease_year(sim.food, sim.year).values())
                sim.year += 1
            self.assertEqual(handed, sum(sim.state.disease.deaths.values()), "seed %d" % seed)


if __name__ == "__main__":
    unittest.main()
