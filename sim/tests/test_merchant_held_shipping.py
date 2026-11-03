"""A merchant that bought nothing this year still ships the held stock its routes cover."""
QUICK_TOPIC = True

import unittest

from sim.economy import merchants
from sim.tests.test_economy_merchants import merchant, world


class HeldStockShips(unittest.TestCase):
    def test_a_route_over_held_stock_ships_without_a_purchase(self):
        _carriage, _map, _area_a, area_b = world()
        who = merchant()
        who.routes = {("salt", "a"): (("b", area_b["salt"], 1.0),)}
        self.assertTrue(merchants.ships_held_stock(who, {("salt", "a"): 4.0}))

    def test_no_route_over_the_stock_held_ships_nothing(self):
        _carriage, _map, _area_a, area_b = world()
        who = merchant()
        who.routes = {("salt", "a"): (("b", area_b["salt"], 1.0),)}
        self.assertFalse(merchants.ships_held_stock(who, {("salt", "a"): 0.0, ("fish", "a"): 3.0}))


if __name__ == "__main__":
    unittest.main()
