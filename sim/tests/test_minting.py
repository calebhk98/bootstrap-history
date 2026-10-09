"""Minting is a production step: metal in, coin out, with labour; fineness
and the mint's charge are data on the civilisation's coin standard."""

QUICK_TOPIC = True

import json
import os
import unittest

from sim.labour import wage_provider

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "data")
COIN_RECIPE = "struck_silver_coin_kg"


def _civ(**extra):
    standard = {"regime": "struck_coin", "material": "silver_kg", "kg_per_unit": 0.0027,
                "source": "test"}
    standard.update(extra)
    return {"id": "probe", "coin_standard": standard}


def _recipe():
    with open(os.path.join(DATA, "production", "98_minting.json")) as handle:
        return json.load(handle)["materials"][COIN_RECIPE]


class Minting(unittest.TestCase):

    def test_a_coin_recipe_turns_metal_into_coin_with_labour(self):
        recipe = _recipe()
        self.assertEqual(list(recipe["outputs"]), [COIN_RECIPE])
        self.assertIn("silver_kg", recipe["inputs"])
        self.assertGreater(sum(recipe["labour_hours"].values()), 0.0)
        self.assertTrue(recipe["yield_basis"])

    def test_the_fine_metal_in_the_recipe_is_the_coins_fineness(self):
        recipe = _recipe()
        fine = recipe["inputs"]["silver_kg"] / recipe["outputs"][COIN_RECIPE]
        with open(os.path.join(DATA, "civilizations", "rome_100ad.json")) as handle:
            standard = json.load(handle)["coin_standard"]
        self.assertAlmostEqual(fine, standard["fineness"], places=6)

    def test_fineness_is_optional_and_must_be_a_share(self):
        wage_provider.validate_coin_standard(_civ())
        wage_provider.validate_coin_standard(_civ(fineness=0.8))
        for bad in (0.0, 1.2, -0.5, "fine"):
            with self.assertRaises(ValueError):
                wage_provider.validate_coin_standard(_civ(fineness=bad))

    def test_a_coin_weighs_its_fine_metal_over_its_fineness(self):
        self.assertAlmostEqual(
            wage_provider.coin_gross_kg_per_unit(_civ(fineness=0.8)["coin_standard"]),
            0.0027 / 0.8, places=12)
        self.assertEqual(wage_provider.coin_gross_kg_per_unit(_civ()["coin_standard"]), 0.0027)


if __name__ == "__main__":
    unittest.main()
