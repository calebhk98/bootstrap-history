"""SCENARIO: an unopened England 1300 and Rome opening each price ink, a written page and a tallow candle (Complaint 567).

The opening prices come from the whole opening (recipes, deposits, the price closure), so this reads them off built games.
"""

import unittest

from sim.engine.economy_port_setup import build_setup
from sim.tests.harness import unopened_sim

GOODS = ("ink_kg", "written_page", "light_tallow_candle")


def _opening_prices(civilisation_id):
    return build_setup(unopened_sim(civ=civilisation_id)).opening_prices


class InkAndCandleRecipeTests(unittest.TestCase):
    def test_england_prices_ink_page_and_tallow_candle(self):
        prices = _opening_prices("england_1300")
        for good in GOODS:
            with self.subTest(good=good):
                self.assertGreater(prices.get(good, 0.0), 0.0)

    def test_rome_still_prices_them(self):
        prices = _opening_prices("rome_100ad")
        for good in GOODS:
            with self.subTest(good=good):
                self.assertGreater(prices.get(good, 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
