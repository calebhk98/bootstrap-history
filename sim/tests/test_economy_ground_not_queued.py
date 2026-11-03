"""Complaint 538: a clearer's expected revenue from ground is the ground's price, not the price of the last unit of a
queue behind a stock that expected sales will never clear. Built inputs, `producers_close._behind_the_stock` called."""

QUICK_TOPIC = True

import unittest

from sim.economy import producers_close
from sim.economy.producers import Producer
from sim.economy.types import Recipe

CLAIM = Recipe("claim", {"ground": 1.0, "grain": 2.0}, {}, {})
PRICES = {"ground": 50.0, "grain": 3.0}


class View:
    def interest_rate(self, currency):
        return 0.1

    def currency_of(self, area):
        return "coin"

    def area_of(self, good, tile):
        return "area"

    def stock(self, agent, good, tile):
        return 800.0


class ShortStockView(View):
    def stock(self, agent, good, tile):
        return 5.0


def behind(ground_goods, view=None, spoilage=None, expected_sales=0.3):
    producer = Producer("p", "lord", "claim", "t", 10.0, expected_sales=expected_sales)
    return producers_close._behind_the_stock(producer, CLAIM, view or View(), PRICES, ground_goods, spoilage)


class GroundNotQueuedTests(unittest.TestCase):
    def test_ground_keeps_its_price_whatever_the_stock_and_expected_sales(self):
        self.assertEqual(behind({"ground"})["ground"], PRICES["ground"])

    def test_a_portable_good_in_the_same_run_still_queues(self):
        self.assertLess(behind({"ground"})["grain"], 1e-6)

    def test_without_the_marker_ground_would_queue_to_nothing(self):
        self.assertLess(behind(())["ground"], 1e-6)

    def test_a_spoiling_good_waits_behind_the_stock_for_less_than_one_that_keeps(self):
        keeps = behind({"ground"}, ShortStockView(), {"grain": 0.0}, expected_sales=1.0)["grain"]
        spoils = behind({"ground"}, ShortStockView(), {"grain": 0.5}, expected_sales=1.0)["grain"]
        self.assertGreater(keeps, 0.0)
        self.assertLess(spoils, keeps)


if __name__ == "__main__":
    unittest.main()
