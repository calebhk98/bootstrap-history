"""Gold's labour follows its placer physics, and gold solves dearer than silver."""
import json
import os
import unittest

from sim.engine.prices import _default_production_entries, solved_prices

# From gold_kg's own yield_basis: placer grade and one labourer's gravel rate.
PLACER_GRAMS_GOLD_PER_CUBIC_METRE = 0.3
GRAVEL_CUBIC_METRES_PER_LABOURER_HOUR = 0.25
GRAMS_PER_KILOGRAM = 1000.0

REPOSITORY_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _per_kilogram_labour(entry, trade):
    return entry["labour_hours"][trade] / entry["outputs"][next(iter(entry["outputs"]))]


class GoldChainPhysics(unittest.TestCase):

    def test_gold_panning_labour_per_kilogram_follows_grade_and_throughput(self):
        entry = _default_production_entries()["gold_kg"]
        floor = (GRAMS_PER_KILOGRAM / PLACER_GRAMS_GOLD_PER_CUBIC_METRE
                 / GRAVEL_CUBIC_METRES_PER_LABOURER_HOUR)
        self.assertGreaterEqual(_per_kilogram_labour(entry, "labourer"), 0.99 * floor)

    def test_kilogram_and_gram_entries_cost_the_same_labour_per_gram(self):
        entries = _default_production_entries()
        per_gram_from_kilogram = (sum(entries["gold_kg"]["labour_hours"].values())
                                  / entries["gold_kg"]["outputs"]["gold_kg"] / GRAMS_PER_KILOGRAM)
        per_gram = sum(entries["gold_g"]["labour_hours"].values())
        self.assertAlmostEqual(per_gram_from_kilogram * GRAMS_PER_KILOGRAM,
                               per_gram * GRAMS_PER_KILOGRAM, delta=0.01 * per_gram * GRAMS_PER_KILOGRAM)


class GoldCostsMoreThanSilver(unittest.TestCase):

    def test_rome_solves_gold_dearer_than_silver_per_kilogram(self):
        path = os.path.join(REPOSITORY_ROOT, "data", "civilizations", "rome_100ad.json")
        with open(path) as handle:
            techs = json.load(handle)["starting_techs"]
        # Only the wage document's shape is read; both metals are priced from the same wages.
        prices_json = {"wage_rates_denarii_per_hour": {"labourer": {"rate": 1.0}},
                       "money_per_labour_hour": 1.0}
        prices = solved_prices(techs, prices_json, civilization_id="rome_100ad").prices_in_labour_hours
        self.assertGreater(prices["gold_kg"], prices["silver_kg"])


if __name__ == "__main__":
    unittest.main()
