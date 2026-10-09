"""Expected spending sizes a durable's wanted stock, and the stock in use is not counted as savings."""

QUICK_TOPIC = True

import unittest

from sim.economy import durable_stock
from sim.tests import economy_fixture as fixture


class DurableStockTests(unittest.TestCase):
    def test_expected_spending_moves_part_of_the_way_to_the_year(self):
        first = durable_stock.update_expected_spending(0.0, 100.0)
        self.assertEqual(first, 100.0)
        later = durable_stock.update_expected_spending(100.0, 200.0)
        self.assertGreater(later, 100.0)
        self.assertLess(later, 200.0)

    def test_a_spending_jump_scales_the_flow_down(self):
        self.assertLess(durable_stock.expected_flow_scale(100.0, 200.0), 1.0)
        self.assertEqual(durable_stock.expected_flow_scale(0.0, 200.0), 1.0)

    def test_in_use_stock_is_flow_times_life_with_the_band_and_only_for_durables(self):
        specs = fixture.specs({fixture.METAL: 10.0})
        stock = durable_stock.in_use_stock({fixture.METAL: 3.0, fixture.GRAIN: 5.0}, specs, 0.5, 0.2)
        self.assertEqual(set(stock), {fixture.METAL})
        self.assertAlmostEqual(stock[fixture.METAL], 3.0 * 0.5 * 10.0 * 1.2)


if __name__ == "__main__":
    unittest.main()
