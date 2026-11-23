"""What the settle check values a spin-up year's output and stock at: the search rules leave the opening's prices, the
clearing rules carry the year's prices and quantities so a change is read at the earlier year's prices."""

QUICK_TOPIC = True

import unittest

from sim.economy import rule_sets, spin_up_valued


class AtTheOpeningPrices(unittest.TestCase):
    def test_nothing_more_is_carried(self):
        self.assertIsNone(spin_up_valued.at_the_opening_prices({"wood_kg": 0.01}, {"wood_kg": 500.0}, {"wood_kg": 40.0}))


class AtTheYearsPrices(unittest.TestCase):
    def test_the_years_prices_and_the_quantities_made_and_held(self):
        valued = spin_up_valued.at_the_years_prices({"wood_kg": 0.01, "mule": 300.0}, {"wood_kg": 500.0}, {"wood_kg": 40.0, "mule": 2.0})
        self.assertEqual(valued, {"prices": {"wood_kg": 0.01, "mule": 300.0}, "output": {"wood_kg": 500.0}, "stock": {"wood_kg": 40.0, "mule": 2.0}})

    def test_a_good_with_no_price_or_a_price_of_nothing_carries_none(self):
        valued = spin_up_valued.at_the_years_prices({"wood_kg": None, "lead_kg": 0.0, "mule": 300.0}, {}, {})
        self.assertEqual(valued["prices"], {"mule": 300.0})

    def test_a_good_of_which_nothing_is_made_or_held_is_left_out(self):
        valued = spin_up_valued.at_the_years_prices({}, {"wood_kg": 0.0, "mule": 3.0}, {"wood_kg": 0.0})
        self.assertEqual((valued["output"], valued["stock"]), ({"mule": 3.0}, {}))


class Rules(unittest.TestCase):
    def test_which_rule_each_set_runs(self):
        self.assertIs(rule_sets.RULE_SETS["search"].spin_up_valued, spin_up_valued.at_the_opening_prices)
        self.assertIs(rule_sets.RULE_SETS["clearing"].spin_up_valued, spin_up_valued.at_the_years_prices)


if __name__ == "__main__":
    unittest.main()
