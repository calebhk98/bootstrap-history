"""One market's clearing allocates each buyer's demand across sellers by the logit on their asks, each seller selling
at its own ask, with a second round for what a sold-out seller could not serve (Eurace@Unibi, Household_rank_and_buy_goods_1/2,
Mall_update_mall_stocks_sales_rationing_1/2)."""
QUICK_TOPIC = True

import math
import unittest

from sim.economy.goods_market import clear
from sim.economy.goods_market_demand import DemandSchedule
from sim.economy.goods_market_logit import allocate
from sim.economy.price_setting import logit_share
from sim.economy.types import Bid, Offer


def floor_bid(quantity, buyer="b", priority=0, budget=1e9, maximum_price=math.inf):
    return Bid(buyer, "grain", "area", "tile", quantity, 0.0, 1.0, 1.0, budget, priority, maximum_price)


def offer(seller, quantity, ask):
    return Offer(seller, "grain", "area", "tile", quantity, ask)


def run(bids, offers):
    return clear(bids, offers, "grain", "area", "coin", None)


def sold(result):
    return {fill.agent: fill.quantity for fill in result.fills if fill.side == "sell"}


def bought(result):
    return {fill.agent: fill.quantity for fill in result.fills if fill.side == "buy"}


class LogitAllocationTests(unittest.TestCase):
    def test_equal_asks_split_demand_equally(self):
        result = run([floor_bid(6.0)], [offer("a", 100.0, 1.0), offer("b", 100.0, 1.0)])
        self.assertAlmostEqual(sold(result)["a"], 3.0)
        self.assertAlmostEqual(sold(result)["b"], 3.0)

    def test_a_dearer_seller_sells_less_but_not_nothing(self):
        result = run([floor_bid(6.0)], [offer("a", 100.0, 1.0), offer("b", 100.0, 1.1)])
        self.assertAlmostEqual(sold(result)["b"], 6.0 * logit_share(1.1, [(1.0, 1)]))
        self.assertGreater(sold(result)["a"], sold(result)["b"])

    def test_each_seller_sells_at_its_own_ask(self):
        result = run([floor_bid(6.0)], [offer("a", 100.0, 1.0), offer("b", 100.0, 1.1)])
        prices = {fill.agent: fill.price for fill in result.fills if fill.side == "sell"}
        self.assertEqual(prices, {"a": 1.0, "b": 1.1})

    def test_the_market_price_is_the_quantity_weighted_mean_of_what_traded(self):
        result = run([floor_bid(6.0)], [offer("a", 100.0, 1.0), offer("b", 100.0, 1.1)])
        sales = sold(result)
        mean = (sales["a"] * 1.0 + sales["b"] * 1.1) / (sales["a"] + sales["b"])
        self.assertAlmostEqual(result.traded_price, mean)

    def test_a_sold_out_sellers_leftover_demand_goes_to_the_others(self):
        result = run([floor_bid(10.0)], [offer("a", 1.0, 1.0), offer("b", 100.0, 1.0)])
        self.assertAlmostEqual(sold(result)["a"], 1.0)
        self.assertAlmostEqual(sold(result)["b"], 9.0)
        self.assertAlmostEqual(result.unmet_floor, 0.0)

    def test_demand_beyond_all_stock_goes_unmet(self):
        result = run([floor_bid(10.0)], [offer("a", 1.0, 1.0), offer("b", 2.0, 1.0)])
        self.assertAlmostEqual(result.quantity, 3.0)
        self.assertAlmostEqual(result.unmet_floor, 7.0)

    def test_no_offers_means_no_price(self):
        result = run([floor_bid(6.0)], [])
        self.assertIsNone(result.traded_price)
        self.assertEqual(result.fills, ())

    def test_a_scarce_seller_serves_the_floor_tier_before_the_rest(self):
        result = run([floor_bid(5.0, "need", 0), floor_bid(5.0, "want", 1)], [offer("a", 5.0, 1.0)])
        self.assertAlmostEqual(bought(result)["need"], 5.0)
        self.assertNotIn("want", bought(result))

    def test_a_buyer_never_pays_more_than_its_budget(self):
        result = run([floor_bid(100.0, budget=10.0)], [offer("a", 100.0, 1.0), offer("b", 100.0, 1.1)])
        paid = math.fsum(fill.quantity * fill.price for fill in result.fills if fill.side == "buy")
        self.assertLessEqual(paid, 10.0 * (1.0 + 1e-9))

    def test_a_buyer_does_not_choose_a_seller_asking_above_its_maximum_price(self):
        result = run([floor_bid(4.0, maximum_price=1.05)], [offer("a", 100.0, 1.0), offer("b", 100.0, 1.1)])
        self.assertEqual(set(sold(result)), {"a"})
        self.assertAlmostEqual(sold(result)["a"], 4.0)

    def test_money_paid_equals_money_received(self):
        result = run([floor_bid(6.0, "x"), floor_bid(3.0, "y")], [offer("a", 2.0, 1.0), offer("b", 100.0, 1.1)])
        paid = math.fsum(fill.quantity * fill.price for fill in result.fills if fill.side == "buy")
        received = math.fsum(fill.quantity * fill.price for fill in result.fills if fill.side == "sell")
        self.assertAlmostEqual(paid, received)


class FinalPassTests(unittest.TestCase):
    def test_a_buyer_turned_away_twice_is_served_by_the_seller_still_holding_stock(self):
        bids = [floor_bid(10.0)]
        offers = [offer("a", 1.0, 1.0), offer("b", 4.0, 1.0), offer("c", 100.0, 1.0)]
        allocation = allocate(bids, offers, [1.0, 1.0, 1.0], DemandSchedule(bids))
        self.assertAlmostEqual(allocation.quantity[0], 10.0)
        self.assertAlmostEqual(allocation.sold[2], 5.0)

    def test_no_buyer_who_can_reach_a_seller_with_stock_is_left_unserved(self):
        bids = [floor_bid(6.0, "x"), floor_bid(6.0, "y", maximum_price=1.05), floor_bid(6.0, "z")]
        offers = [offer("a", 1.0, 1.0), offer("b", 2.0, 1.0), offer("c", 3.0, 1.0), offer("d", 30.0, 1.1)]
        allocation = allocate(bids, offers, [1.0, 1.0, 1.0, 1.1], DemandSchedule(bids))
        self.assertAlmostEqual(allocation.quantity[0], 6.0)
        self.assertAlmostEqual(allocation.quantity[2], 6.0)
        self.assertAlmostEqual(allocation.sold[0], 1.0)
        self.assertAlmostEqual(allocation.sold[1], 2.0)
        self.assertAlmostEqual(allocation.sold[2], 3.0)

    def test_the_final_pass_pays_each_sellers_own_ask(self):
        bids = [floor_bid(10.0)]
        offers = [offer("a", 1.0, 1.0), offer("b", 4.0, 1.0), offer("c", 100.0, 1.2)]
        allocation = allocate(bids, offers, [1.0, 1.0, 1.2], DemandSchedule(bids))
        self.assertAlmostEqual(allocation.cost[0], allocation.sold[0] + allocation.sold[1] + 1.2 * allocation.sold[2])


if __name__ == "__main__":
    unittest.main()
