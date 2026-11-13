"""`crop_sites.sites` works the paying floor of a recipe once for all tiles; it names the same tiles as asking `pays` of each tile."""

QUICK_TOPIC = True

import random
import types
import unittest

from sim.economy import crop_sites


def recipe(rng):
    inputs = {"seed": rng.uniform(0.1, 2.0)}
    return types.SimpleNamespace(
        recipe_id="r", inputs=inputs, outputs={"grain": rng.uniform(1.0, 5.0)}, labour_hours={"farmer": rng.uniform(1.0, 20.0)},
        plant_goods={}, plant_life_years=0.0, tool_wear={}, tool_wear_sorted=(), hard_inputs=inputs, site_bound=False, climate_classes=(), joint_cost_basis="value")


class CropSitesTest(unittest.TestCase):
    def test_sites_equal_pays_tile_by_tile(self):
        rng = random.Random(3)
        compared = 0
        for _case in range(200):
            run = recipe(rng)
            prices = {"seed": rng.uniform(0.5, 3.0), "grain": rng.uniform(0.5, 6.0)}
            wages = {"farmer": rng.uniform(0.01, 0.5)}
            yields = {"t%d" % index: rng.choice([0.0, rng.uniform(0.1, 1.5)]) for index in range(rng.randint(1, 12))}
            try:
                reference = [tile for tile, factor in sorted(yields.items()) if crop_sites.pays(run, factor, prices, wages)]
            except (AttributeError, KeyError, TypeError):
                continue
            reference = reference or [tile for tile, factor in sorted(yields.items()) if factor > 0.0]
            self.assertEqual(reference, crop_sites.sites(yields, run, prices, wages))
            compared += 1
        self.assertGreater(compared, 100)      # most cases ran; a case the stand-in recipe cannot price is skipped


if __name__ == "__main__":
    unittest.main()
