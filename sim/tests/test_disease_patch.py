"""sim/disease/ stage 1: one patch of people, one pathogen, a sub-year chain-binomial step.

Properties, not outcomes (Complaints/reports/epidemic-model-research.md section 11.6). Nothing here builds a
game; the fixture is a patch of plain numbers.
"""

QUICK_TOPIC = True

import json
import math
import random
import unittest

from sim.disease import api as disease


def make_pathogen(reproduction_number=3.5, case_fatality=0.3, permanent=True, immunity_days=None):
    latent_days, infectious_days = 10.0, 14.0
    return disease.Pathogen.from_plain({
        "id": "test_pathogen", "name": "Test pathogen",
        "stages": [{"id": "exposed", "infectiousness": 0.0, "mean_duration_in_days": latent_days, "shape": 3},
                   {"id": "infectious", "infectiousness": 1.0, "mean_duration_in_days": infectious_days, "shape": 2}],
        "transmissibility_per_day": reproduction_number / infectious_days,
        "case_fatality": case_fatality,
        "immunity": {"permanent": permanent, "duration_in_days": immunity_days},
    })


def final_size_relation(reproduction_number, initial_susceptible_fraction=1.0):
    final_fraction = 0.5
    for _ in range(500):
        final_fraction = 1.0 - initial_susceptible_fraction * math.exp(-reproduction_number * final_fraction)
    return final_fraction


def run_outbreak(pathogen, seed, population=5000, seeded=10, days=400, step_length_in_days=None, **patch_options):
    patch = disease.Patch.naive(pathogen, population, seed=seed, **patch_options)
    patch.seed_infection(pathogen, seeded)
    disease.advance_patch(pathogen, patch, days, step_length_in_days)
    return patch


def mean_final_attack(pathogen, seeds, step_length_in_days=None):
    shares = []
    for seed in seeds:
        patch = run_outbreak(pathogen, seed, step_length_in_days=step_length_in_days)
        shares.append(1.0 - patch.counts["susceptible"] / 5000.0)
    return sum(shares) / len(shares)


class ConservationTest(unittest.TestCase):
    def test_people_plus_deaths_minus_births_is_constant_every_step(self):
        pathogen = make_pathogen()
        patch = disease.Patch.naive(pathogen, 3000, seed=4, births_per_person_per_year=0.03,
                                    background_deaths_per_person_per_year=0.025)
        patch.seed_infection(pathogen, 10)
        start = patch.living()
        for _ in range(250):
            disease.step_patch(pathogen, patch)
            self.assertEqual(patch.living() + patch.deaths_from_disease + patch.deaths_background
                             - patch.births, start)
            self.assertTrue(all(count >= 0 for count in patch.counts.values()))
        self.assertGreater(patch.deaths_from_disease, 0)


class ThresholdTest(unittest.TestCase):
    def test_reproduction_number_comes_from_stage_durations(self):
        self.assertAlmostEqual(disease.reproduction_number(make_pathogen(3.5)), 3.5)
        self.assertAlmostEqual(disease.herd_immunity_threshold(make_pathogen(4.0)), 0.75)

    def test_no_spread_below_one(self):
        pathogen = make_pathogen(0.8)
        for seed in range(5):
            patch = run_outbreak(pathogen, seed, seeded=10, days=1500)
            self.assertEqual(patch.infected_now(), 0)
            self.assertLess(1.0 - patch.counts["susceptible"] / 5000.0, 0.05)

    def test_nothing_happens_without_infection(self):
        pathogen = make_pathogen()
        patch = disease.Patch.naive(pathogen, 1000, seed=1)
        before = patch.to_plain()["counts"]
        disease.advance_patch(pathogen, patch, 100)
        self.assertEqual(patch.to_plain()["counts"], before)
        self.assertEqual(patch.deaths_from_disease, 0)


class FinalSizeTest(unittest.TestCase):
    def test_final_size_matches_the_closed_relation(self):
        pathogen = make_pathogen(3.5, case_fatality=0.0)
        expected = final_size_relation(3.5)
        self.assertAlmostEqual(mean_final_attack(pathogen, range(12)), expected, delta=0.015)

    def test_intermediate_reproduction_number(self):
        pathogen = make_pathogen(1.8, case_fatality=0.0)
        expected = final_size_relation(1.8)
        self.assertAlmostEqual(mean_final_attack(pathogen, range(16)), expected, delta=0.02)

    def test_step_halving_changes_final_size_little(self):
        pathogen = make_pathogen(2.0, case_fatality=0.0)
        coarse, middle, fine = (mean_final_attack(pathogen, range(16), step_length) for step_length in (2.0, 1.0, 0.5))
        self.assertAlmostEqual(coarse, middle, delta=0.02)
        self.assertAlmostEqual(middle, fine, delta=0.02)


class MemoryTest(unittest.TestCase):
    def test_second_wave_is_much_smaller_than_the_first(self):
        pathogen = make_pathogen(3.5)
        patch = disease.Patch.naive(pathogen, 20000, seed=3, births_per_person_per_year=0.03,
                                    background_deaths_per_person_per_year=0.03)
        patch.seed_infection(pathogen, 10)
        disease.advance_patch(pathogen, patch, 3 * 365)
        first_wave_deaths = patch.deaths_from_disease
        self.assertGreater(first_wave_deaths, 1000)
        self.assertGreater(patch.immune_share(), disease.herd_immunity_threshold(pathogen))
        patch.seed_infection(pathogen, 10)
        disease.advance_patch(pathogen, patch, 3 * 365)
        second_wave_deaths = patch.deaths_from_disease - first_wave_deaths
        self.assertLess(second_wave_deaths, 0.25 * first_wave_deaths)


class DeterminismTest(unittest.TestCase):
    def test_same_seed_same_trajectory(self):
        pathogen = make_pathogen()
        first = run_outbreak(pathogen, 9, days=150).to_plain()
        second = run_outbreak(pathogen, 9, days=150).to_plain()
        other = run_outbreak(pathogen, 10, days=150).to_plain()
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)

    def test_saved_and_restored_patch_continues_identically(self):
        pathogen = make_pathogen()
        straight = run_outbreak(pathogen, 5, days=200)
        saved_halfway = run_outbreak(pathogen, 5, days=80)
        restored = disease.Patch.from_plain(json.loads(json.dumps(saved_halfway.to_plain())))
        disease.advance_patch(pathogen, restored, 120)
        self.assertEqual(restored.to_plain(), straight.to_plain())

    def test_package_does_not_touch_the_global_random_generator(self):
        random.seed(1)
        expected = random.random()
        random.seed(1)
        run_outbreak(make_pathogen(), 2, days=60)
        self.assertEqual(random.random(), expected)


class VirginSoilTest(unittest.TestCase):
    def test_endemic_population_loses_far_fewer_people_than_a_naive_one(self):
        pathogen = make_pathogen(4.0, case_fatality=0.2)
        naive_deaths, endemic_deaths = [], []
        for seed in range(6):
            naive = disease.Patch.naive(pathogen, 10000, seed=seed)
            endemic = disease.Patch.endemic(pathogen, 10000, seed=seed)
            for patch, deaths in ((naive, naive_deaths), (endemic, endemic_deaths)):
                patch.seed_infection(pathogen, 10)
                disease.advance_patch(pathogen, patch, 500)
                deaths.append(patch.deaths_from_disease)
        self.assertGreater(sum(naive_deaths), 4 * sum(endemic_deaths))
        self.assertAlmostEqual(disease.Patch.endemic(pathogen, 10000, seed=0).immune_share(),
                               disease.herd_immunity_threshold(pathogen), delta=0.001)


class PathogenDataTest(unittest.TestCase):
    def test_shipped_pathogen_files_pass_the_checks(self):
        self.assertEqual(disease.check_pathogen_data(), [])
        pathogens = disease.load_pathogens()
        self.assertIn("smallpox", pathogens)
        for pathogen in pathogens.values():
            low, high = pathogen.reproduction_number_range
            self.assertTrue(low <= disease.reproduction_number(pathogen) <= high, pathogen.id)

    def test_a_missing_source_tag_is_reported(self):
        plain = json.loads(json.dumps(disease.load_pathogen_plain("smallpox")))
        del plain["sources"]["case_fatality"]
        problems = disease.pathogen_problems(plain)
        self.assertTrue(any("case_fatality" in problem for problem in problems))

    def test_reproduction_number_outside_the_sourced_range_is_reported(self):
        plain = json.loads(json.dumps(disease.load_pathogen_plain("smallpox")))
        plain["transmissibility_per_day"] *= 10
        self.assertTrue(any("reproduction" in problem for problem in disease.pathogen_problems(plain)))


if __name__ == "__main__":
    unittest.main()
