"""A durable good households buy is not bought again in full: the post-wear holding buys the missing part of the
serving stock. Wear itself is `inventory.wear_moves` (test_economy_inventory)."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import durable_stock, households_orders

SERVICE_LIFE_YEARS = 20.0


class DurablePurchaseRuleTests(unittest.TestCase):
    """The post-wear holding buys the missing part of the serving stock."""
    SPECS = {"metal": types.SimpleNamespace(service_life_years=SERVICE_LIFE_YEARS, spoilage_per_year=0.0)}

    def bought(self, flow, held, scale=1.0):
        return households_orders._durable_ratio("metal", flow, held, self.SPECS, scale) * flow

    def test_a_stock_after_year_end_wear_buys_exactly_the_missing_wear(self):
        held = 5.0 * (SERVICE_LIFE_YEARS - 1.0)
        self.assertAlmostEqual(self.bought(5.0, held), 5.0)

    def test_it_is_not_bought_again_in_full(self):
        held = 5.0 * SERVICE_LIFE_YEARS
        self.assertLess(self.bought(5.0, held), 2.0 * held / SERVICE_LIFE_YEARS)

    def test_a_stock_above_its_wanted_level_buys_only_the_replacement(self):
        self.assertAlmostEqual(self.bought(5.0, 10.0 * SERVICE_LIFE_YEARS), 5.0)

    def test_a_small_rise_in_flow_moves_the_purchase_by_a_share_of_the_stock_it_wants_more(self):
        held = 5.0 * (SERVICE_LIFE_YEARS - 1.0)
        extra_stock_after_losses = 0.01 * 5.0 * (SERVICE_LIFE_YEARS - 1.0)
        self.assertAlmostEqual(self.bought(5.0, held, 1.01) - self.bought(5.0, held),
                               0.01 * 5.0 + durable_stock.DURABLE_GAP_CLOSED_SHARE * extra_stock_after_losses)

    def test_a_good_used_up_in_the_year_is_bought_whole(self):
        self.assertEqual(households_orders._durable_ratio("bread", 5.0, 0.0, self.SPECS), 1.0)


if __name__ == "__main__":
    unittest.main()
