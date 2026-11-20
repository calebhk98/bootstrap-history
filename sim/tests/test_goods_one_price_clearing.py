"""goods_clear_one_price: the price where supply meets demand, the supply at a price, and who bought from whom."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy.goods_clear_one_price import pairing_of, price_where_supply_meets, supply_at
from sim.economy.stock_supply import StockCurve
from sim.economy.types import Fill, Offer


def demand_at(price):
    return 100.0 / price


def supply_at_price(price):
    return 10.0 * price


class PriceWhereSupplyMeets(unittest.TestCase):
    def test_the_price_is_where_the_two_schedules_cross(self):
        # 100 / price = 10 * price at price = sqrt(10)
        price = price_where_supply_meets(demand_at, supply_at_price, 0.5, 20.0)
        self.assertAlmostEqual(price, math.sqrt(10.0), places=6)

    def test_lowest_where_supply_covers_demand_there(self):
        self.assertEqual(price_where_supply_meets(demand_at, supply_at_price, 4.0, 20.0), 4.0)

    def test_highest_where_supply_falls_short_even_there(self):
        self.assertEqual(price_where_supply_meets(demand_at, supply_at_price, 0.5, 2.0), 2.0)


class SupplyAt(unittest.TestCase):
    def test_sums_the_curves_and_the_posted_offers_at_or_under_the_price(self):
        curve = StockCurve(Offer("producer:a", "grain_kg", "area", "tile", 10.0, 1.0), 4.0, 2.0)
        posted = [Offer("producer:b", "grain_kg", "area", "tile", 3.0, 1.5),
                  Offer("producer:c", "grain_kg", "area", "tile", 4.0, 2.0),
                  Offer("producer:d", "grain_kg", "area", "tile", 5.0, 2.5)]
        # at the content price the curve lets go 10 - 4; the offers reserved at 1.5 and 2.0 take it, the one at 2.5 does not
        self.assertAlmostEqual(supply_at(2.0, [curve], posted), (10.0 - 4.0) + 3.0 + 4.0)

    def test_nothing_on_the_market_supplies_nothing(self):
        self.assertEqual(supply_at(2.0, [], []), 0.0)


def fill(agent, quantity, price, side):
    return Fill(agent, "grain_kg", "area", "tile", quantity, price, side)


class PairingOf(unittest.TestCase):
    def setUp(self):
        self.fills = [fill("buyer:1", 5.0, 2.0, "buy"), fill("buyer:2", 3.0, 2.0, "buy"), fill("buyer:3", 0.0, 2.0, "buy"),
                      fill("seller:1", 6.0, 1.8, "sell"), fill("seller:2", 2.0, 1.9, "sell"), fill("seller:3", 0.0, 1.7, "sell")]
        self.pairing = pairing_of(self.fills)

    def test_the_pairs_sum_to_the_quantity_bought(self):
        self.assertAlmostEqual(sum(self.pairing.quantity), 5.0 + 3.0)

    def test_each_buyers_pairs_sum_to_its_fill(self):
        for index, (agent, _tile) in enumerate(self.pairing.buyers):
            bought = sum(amount for amount, buyer in zip(self.pairing.quantity, self.pairing.buyer_index) if buyer == index)
            self.assertAlmostEqual(bought, {"buyer:1": 5.0, "buyer:2": 3.0}[agent])

    def test_each_sellers_pairs_sum_to_its_fill(self):
        for index, (agent, _tile) in enumerate(self.pairing.sellers):
            sold = sum(amount for amount, seller in zip(self.pairing.quantity, self.pairing.seller_index) if seller == index)
            self.assertAlmostEqual(sold, {"seller:1": 6.0, "seller:2": 2.0}[agent])

    def test_asks_are_the_sellers_fill_prices(self):
        self.assertEqual(self.pairing.asks, (1.8, 1.9))

    def test_zero_quantity_fills_are_left_out(self):
        self.assertEqual(self.pairing.buyers, (("buyer:1", "tile"), ("buyer:2", "tile")))
        self.assertEqual(self.pairing.sellers, (("seller:1", "tile"), ("seller:2", "tile")))

    def test_buyers_take_from_the_next_seller_with_units_left(self):
        self.assertEqual(self.pairing.buyer_index, (0, 1, 1))
        self.assertEqual(self.pairing.seller_index, (0, 0, 1))
        self.assertEqual(self.pairing.quantity, (5.0, 1.0, 2.0))

    def test_no_fills_pair_nothing(self):
        self.assertEqual(pairing_of([]).quantity, ())


if __name__ == "__main__":
    unittest.main()
