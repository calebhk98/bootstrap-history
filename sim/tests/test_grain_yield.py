"""Seed rate and fold return of wheat are built from Columella's text (data/world/grain_yield.json), not typed.

Each test calls the rule in sim/world/grain_yield.py on inputs built here, then checks that the recipes and the
declared constants follow it."""
import json
import os
import unittest

from sim.world import agriculture, farm_labour, grain_yield, land

QUICK_TOPIC = True

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def built_data(modii_per_iugerum, pounds_per_modius, kg_per_pound, fold):
    return {"seed": {"modii_per_iugerum": modii_per_iugerum, "pounds_per_modius": pounds_per_modius,
                     "kg_per_roman_pound": kg_per_pound},
            "fold_return": {"value": fold}}


class GrainYieldRuleTests(unittest.TestCase):
    def test_seed_is_modii_times_modius_weight_over_the_iugerum(self):
        data = built_data(5.0, 20.0, 0.5, 4.0)
        self.assertAlmostEqual(grain_yield.seed_kg_per_hectare(data, 0.25), 5.0 * 20.0 * 0.5 / 0.25)

    def test_a_smaller_iugerum_means_more_seed_to_the_hectare(self):
        data = built_data(5.0, 20.0, 0.5, 4.0)
        self.assertAlmostEqual(grain_yield.seed_kg_per_hectare(data, 0.125),
                               2.0 * grain_yield.seed_kg_per_hectare(data, 0.25))

    def test_net_yield_is_the_harvest_less_the_seed_it_contains(self):
        # fold 4 means 4 kg reaped per kg sown, one of which is held back
        self.assertAlmostEqual(grain_yield.net_yield_kg_per_hectare(100.0, 4.0), 300.0)
        self.assertAlmostEqual(grain_yield.net_yield_kg_per_hectare(100.0, 1.0), 0.0)

    def test_fold_return_reads_the_data_value(self):
        self.assertEqual(grain_yield.fold_return(built_data(5.0, 20.0, 0.5, 3.5)), 3.5)


class FarmFractionRuleTests(unittest.TestCase):
    """fraction_of_population_that_must_farm on crops built here: each input moves it the way the rule says."""

    def crop(self, seed_kg, fold):
        return agriculture.DEFAULT_CROP._replace(planting_material_kg_per_ha=seed_kg, fold_return_on_planting_material=fold)

    def test_people_fed_by_one_worker_is_hectares_times_net_food_over_the_ration(self):
        crop = self.crop(100.0, 4.0)
        net_food_per_hectare = 300.0 * (1.0 - agriculture.DEFAULT_STORAGE_TECHNIQUE.spoilage_rate_per_year)
        people_fed = (agriculture.hectares_cropped_per_farm_worker(crop) * net_food_per_hectare
                      / agriculture.annual_food_demand_kg_per_person(crop))
        self.assertAlmostEqual(1.0 / agriculture.fraction_of_population_that_must_farm(crop), people_fed)

    def test_a_higher_fold_return_needs_fewer_farmers(self):
        self.assertLess(agriculture.fraction_of_population_that_must_farm(self.crop(100.0, 8.0)),
                        agriculture.fraction_of_population_that_must_farm(self.crop(100.0, 4.0)))

    def test_more_seed_at_the_same_fold_leaves_more_grain_and_needs_fewer_farmers(self):
        self.assertLess(agriculture.fraction_of_population_that_must_farm(self.crop(200.0, 4.0)),
                        agriculture.fraction_of_population_that_must_farm(self.crop(100.0, 4.0)))


class GrainYieldFollowedByTheModelTests(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "data", "production", "40_organics.json"), encoding="utf-8") as handle:
            self.recipes = json.load(handle)["materials"]

    def test_the_constants_follow_the_rule_on_the_data(self):
        data = grain_yield.load_grain_yield()
        seed = grain_yield.seed_kg_per_hectare(data, float(farm_labour.load_farm_labour()["iugerum_hectares"]["value"]))
        self.assertEqual(agriculture.SEED_SOWING_RATE_KG_PER_HA, seed)
        self.assertEqual(agriculture.FOLD_RETURN_ON_SEED_SOWN, grain_yield.fold_return(data))

    def test_the_recipes_output_the_net_yield_and_land_reads_it(self):
        net = grain_yield.net_yield_kg_per_hectare(agriculture.SEED_SOWING_RATE_KG_PER_HA,
                                                   agriculture.FOLD_RETURN_ON_SEED_SOWN)
        self.assertAlmostEqual(self.recipes["wheat_kg"]["outputs"]["wheat_kg"], net)
        self.assertAlmostEqual(self.recipes["wheat_hoe_kg"]["outputs"]["wheat_kg"], net)
        self.assertAlmostEqual(land.REFERENCE_WHEAT_YIELD_KG_PER_HECTARE, net)

    def test_every_input_quotes_its_source(self):
        data = grain_yield.load_grain_yield()
        for key in ("modii_per_iugerum_quote", "pounds_per_modius_quote", "kg_per_roman_pound_quote"):
            self.assertTrue(data["seed"][key].strip(), key)
        self.assertTrue(data["fold_return"]["quote"].strip())


if __name__ == "__main__":
    unittest.main()
