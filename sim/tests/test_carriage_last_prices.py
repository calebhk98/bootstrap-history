"""A carrier good's last price is the volume-weighted mean of the prices its areas cleared at, not of quotes."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.economy import carriage_wear


def stand_in(cleared, quoted):
    setup = SimpleNamespace(carriage_carriers={"cart": (1.0, (("cart", 0.1),))}, currency_id="coin", opening_prices={"cart": 8.0})
    memory = SimpleNamespace(cleared_prices=cleared, prices={**quoted, **cleared}, opening_wage_level=lambda _currency: 2.0)
    return setup, memory


class LastPrices(unittest.TestCase):
    def test_areas_that_cleared_are_weighted_by_volume_and_quotes_are_left_out(self):
        setup, memory = stand_in({"cart|a": 10.0, "cart|b": 20.0}, {"cart|c": 1000.0})
        weights = {"cart|a": 3.0, "cart|b": 1.0, "cart|c": 50.0}
        self.assertAlmostEqual(carriage_wear.last_prices(setup, memory, weights)["cart"], 12.5)

    def test_no_area_cleared_falls_back_to_the_opening_price_in_todays_money(self):
        setup, memory = stand_in({}, {"cart|c": 1000.0})
        self.assertAlmostEqual(carriage_wear.last_prices(setup, memory, {})["cart"], 16.0)

    def test_cleared_areas_with_no_volume_weight_count_equally(self):
        setup, memory = stand_in({"cart|a": 10.0, "cart|b": 20.0}, {})
        self.assertAlmostEqual(carriage_wear.last_prices(setup, memory, {})["cart"], 15.0)


if __name__ == "__main__":
    unittest.main()
