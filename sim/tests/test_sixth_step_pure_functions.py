"""The arithmetic moved out of the engine's farm, disease and coin mixins, tested without a `Sim`."""
import unittest

from sim.disease.api import technology_scales, working_age_death_share
from sim.world import coin_metal

QUICK_TOPIC = True


class CoinMetalTests(unittest.TestCase):
    def test_revaluation_closes_part_of_the_gap_and_respects_the_cap(self):
        self.assertAlmostEqual(coin_metal.revalued_ratio(1.0, 1.21, 0.5, 2.0), 1.1)
        self.assertEqual(coin_metal.revalued_ratio(1.0, 100.0, 0.9, 1.25), 1.25)
        self.assertEqual(coin_metal.revalued_ratio(1.0, 0.0001, 0.9, 1.25), 0.8)

    def test_unmeasured_metal_counts_as_unchanged(self):
        self.assertEqual(coin_metal.revalued_ratio(1.0, 0.0, 0.5, 2.0), 1.0)

    def test_keeping_cost_is_by_mass_and_never_negative(self):
        self.assertEqual(coin_metal.keeping_cost_per_year(1000.0, 5.0, 60.0, 2.0), 5.0 * 60.0 * 2.0)
        self.assertEqual(coin_metal.keeping_cost_per_year(-3.0, 5.0, 60.0, 2.0), 0.0)

    def test_carriage_never_exceeds_the_units_moved(self):
        self.assertEqual(coin_metal.carriage_units(10.0, 5.0, 1000.0, 1.0), 10.0)
        self.assertAlmostEqual(coin_metal.carriage_units(10.0, 5.0, 10.0, 1.0), 0.5)


class DiseaseEffectTests(unittest.TestCase):
    def test_technology_relief_scales_with_reach_and_names_pathogens(self):
        effects = [({"acts_on": "case_fatality", "factor": 0.5, "pathogens": ["a"]}, 0.5),
                   ({"acts_on": "transmission", "factor": 0.8}, 1.0),
                   ({"acts_on": "case_fatality", "factor": 0.1}, 0.0)]
        fatality, transmission = technology_scales(["a", "b"], effects)
        self.assertEqual(fatality, {"a": 0.75, "b": 1.0})
        self.assertAlmostEqual(transmission["b"], 0.8)

    def test_death_share_of_working_age(self):
        self.assertEqual(working_age_death_share({"working_age": 25.0}, 75.0), 0.25)
        self.assertEqual(working_age_death_share({}, 75.0), 0.0)
        self.assertEqual(working_age_death_share({"working_age": 5.0}, 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
