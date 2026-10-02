"""Stocks carried between years: spoilage, wear, the price a holder sells at, and target stock."""
import unittest

from sim.economy import inventory
from sim.economy.types import EDGE_CONSUMPTION, EDGE_SPOILAGE, GoodSpec

SPECS = {
    "grain": GoodSpec("grain", 1.0, 0.2, 0.0, "food"),
    "plough": GoodSpec("plough", 10.0, 0.0, 5.0, "tool"),
    "salt": GoodSpec("salt", 1.0, 0.0, 0.0, "food"),
}


class CarryTests(unittest.TestCase):
    def test_spoilage_takes_each_stocks_share_to_the_spoilage_edge(self):
        moves = inventory.spoilage_moves({("farmer", "grain", "t1"): 100.0, ("farmer", "salt", "t1"): 50.0}, SPECS)
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves[0].receiver, EDGE_SPOILAGE)
        self.assertEqual(moves[0].giver, "farmer")
        self.assertAlmostEqual(moves[0].quantity, 20.0)

    def test_edge_holders_do_not_spoil(self):
        self.assertEqual(inventory.spoilage_moves({("edge:production", "grain", "t1"): 5.0}, SPECS), [])

    def test_wear_applies_to_users_only(self):
        holdings = {("farmer", "plough", "t1"): 10.0, ("merchant", "plough", "t1"): 10.0, ("farmer", "grain", "t1"): 9.0}
        moves = inventory.wear_moves(holdings, SPECS, users={"farmer"})
        self.assertEqual([(move.giver, move.good) for move in moves], [("farmer", "plough")])
        self.assertEqual(moves[0].receiver, EDGE_CONSUMPTION)
        self.assertAlmostEqual(moves[0].quantity, 2.0)


class ReservationTests(unittest.TestCase):
    def test_holding_reservation_is_discounted_net_of_spoilage_and_storage(self):
        self.assertAlmostEqual(inventory.holding_reservation(10.0, 0.0, 0.0, 0.0), 10.0)
        self.assertAlmostEqual(inventory.holding_reservation(10.0, 0.25, 0.2, 0.5), (8.0 - 0.5) / 1.25)

    def test_perishables_are_sold_cheaper(self):
        self.assertLess(inventory.holding_reservation(10.0, 0.05, 0.5, 0.0),
                        inventory.holding_reservation(10.0, 0.05, 0.0, 0.0))

    def test_distress_lowers_the_reservation_as_the_shortfall_grows(self):
        levels = [inventory.distressed_reservation(10.0, shortfall, 100.0) for shortfall in (0.0, 25.0, 50.0, 100.0)]
        self.assertEqual(levels[0], 10.0)
        self.assertEqual(levels, sorted(levels, reverse=True))
        self.assertEqual(levels[-1], 0.0)

    def test_shortfall_beyond_the_stock_sells_at_any_positive_price(self):
        self.assertEqual(inventory.distressed_reservation(10.0, 500.0, 100.0), 0.0)

    def test_waste_reservation_is_left_alone(self):
        self.assertEqual(inventory.distressed_reservation(-2.0, 50.0, 100.0), -2.0)


class TargetStockTests(unittest.TestCase):
    def test_target_scales_with_months_of_cover(self):
        self.assertAlmostEqual(inventory.target_stock(120.0, 3.0), 30.0)

    def test_default_cover_is_the_declared_heuristic(self):
        self.assertAlmostEqual(inventory.target_stock(120.0), 120.0 * inventory.DEFAULT_MONTHS_OF_COVER / 12.0)

    def test_negative_sales_hold_nothing(self):
        self.assertEqual(inventory.target_stock(-5.0), 0.0)


if __name__ == "__main__":
    unittest.main()
