"""Complaints/576 and 668: a sale of the founder's own stock (a mine's ore, for one) is cut to what buyers took and still
wanted last year, not to what the sellers hold. The rule is `GoodsMarket.sale_room_tonnes`, called on built quotes."""
QUICK_TOPIC = True

import unittest

from sim.engine.goods_market_api import GoodsMarket


class SaleRoomTests(unittest.TestCase):
    def test_the_room_is_what_buyers_took_however_much_the_sellers_hold(self):
        quote = {"market_available_tonnes_per_year": 1.0e6, "buyers_take_tonnes_per_year": 40.0}
        self.assertEqual(GoodsMarket.sale_room_tonnes(quote, 0.0), 40.0)
        self.assertEqual(GoodsMarket.sale_room_tonnes(quote, 15.0), 25.0)
        self.assertEqual(GoodsMarket.sale_room_tonnes(quote, 99.0), 0.0)

    def test_a_good_buyers_did_not_take_has_no_room(self):
        quote = {"market_available_tonnes_per_year": 1.0e6, "buyers_take_tonnes_per_year": 0.0}
        self.assertEqual(GoodsMarket.sale_room_tonnes(quote, 0.0), 0.0)

    def test_where_the_economy_does_not_trade_the_good_the_old_room_stands(self):
        quote = {"market_available_tonnes_per_year": 70.0, "buyers_take_tonnes_per_year": None}
        self.assertEqual(GoodsMarket.sale_room_tonnes(quote, 10.0), 60.0)

    def test_buying_is_still_cut_to_what_the_sellers_offer(self):
        quote = {"market_available_tonnes_per_year": 70.0, "buyers_take_tonnes_per_year": 5.0}
        self.assertEqual(GoodsMarket.market_room_tonnes(quote, 10.0), 60.0)


if __name__ == "__main__":
    unittest.main()
