"""priced_total (sim/world/plant_baskets.py): a basket's worth, or None when one of its goods has no price."""

QUICK_TOPIC = True

import unittest

from sim.world.plant_baskets import priced_total


class PricedTotal(unittest.TestCase):
    def test_every_good_priced(self):
        self.assertAlmostEqual(priced_total({"iron": 2.0, "coal": 3.0}, {"iron": 5.0, "coal": 1.0}), 13.0)

    def test_an_unpriced_good_makes_the_worth_unknown(self):
        self.assertIsNone(priced_total({"iron": 2.0, "coal": 3.0}, {"iron": 5.0}))

    def test_an_empty_basket_is_worth_nothing(self):
        self.assertEqual(priced_total({}, {}), 0.0)


if __name__ == "__main__":
    unittest.main()
