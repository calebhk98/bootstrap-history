"""Merchants chasing one destination share it: across its sources one merchant's bids add up to its
share of what the destination usually trades, and rivals together to the group's share."""

QUICK_TOPIC = True

import unittest

from sim.economy import merchants, merchants_credit
from sim.economy.market_areas import AreaMap
from sim.economy.merchants import Merchant
from sim.economy.types import GoodSpec
from sim.tests.test_economy_tile_costs import star_tiles, unit_cost_table

TILES = ("a", "b", "c", "d")        # a, b, c are cheap sources; d is the dear destination
SALT = GoodSpec("salt", 1000.0, 0.0, 0.0, "food")
SPECS = {"salt": SALT}
DESTINATION_VOLUME = 100.0


class View:
    year = 1

    def price(self, good, area):
        return None

    def interest_rate(self, currency):
        return 0.0


def world():
    carriage = unit_cost_table(star_tiles("d", ["a", "b", "c"], 100.0), "a", "d")      # a tonne from any source costs one
    area_map = AreaMap(TILES, carriage, [(SALT, 2.0)], {"a": 10.0, "b": 9.0, "c": 8.0, "d": 5.0}, threshold_share=0.01)
    return carriage, area_map


def merchant(name="m1"):
    carriage, area_map = world()
    area = {tile: area_map.area_of("salt", tile) for tile in TILES}
    expected = {("salt", area["a"]): 2.0, ("salt", area["b"]): 2.0, ("salt", area["c"]): 2.0, ("salt", area["d"]): 5.0}
    return Merchant(name, "a", "owner", 100.0, expected, {("salt", area["d"]): DESTINATION_VOLUME})


def total_bid(orders):
    return sum(bid.flexible_quantity for bid in orders.bids)


class OneMerchantAcrossSourcesTests(unittest.TestCase):
    def test_bids_from_every_source_together_stay_within_the_destinations_share(self):
        carriage, area_map = world()
        orders = merchants.orders(merchant(), View(), carriage, area_map, 1e6, {}, SPECS, 0.0)
        self.assertLessEqual(total_bid(orders), merchants.MERCHANT_MARKET_SHARE * DESTINATION_VOLUME + 1e-9)

    def test_the_whole_share_is_still_bid_when_cash_allows(self):
        carriage, area_map = world()
        orders = merchants.orders(merchant(), View(), carriage, area_map, 1e6, {}, SPECS, 0.0)
        self.assertAlmostEqual(total_bid(orders), merchants.MERCHANT_MARKET_SHARE * DESTINATION_VOLUME)

    def test_a_loan_request_does_not_count_the_same_room_once_per_source(self):
        carriage, area_map = world()
        who = merchant()
        who.capital_base = 1e6          # the leverage limit is not what binds
        asked = merchants_credit.credit_request(who, View(), carriage, area_map, 0.0, {}, SPECS, 0.0, 0.0, "coin")
        self.assertIsNotNone(asked)
        # the cargo fits the one destination: its share of the volume, at no more than price plus carriage a unit
        self.assertLessEqual(asked.amount, merchants.MERCHANT_MARKET_SHARE * DESTINATION_VOLUME * (2.0 + 1.0) + 1e-9)


class SourceTests(unittest.TestCase):
    def test_a_merchant_does_not_bid_for_more_than_the_source_usually_sells(self):
        carriage, area_map = world()
        who = merchant()
        source = area_map.area_of("salt", "a")
        who.expected_volumes[("salt", source)] = 2.0     # the area sold two units last year; the destination takes thirty
        orders = merchants.orders(who, View(), carriage, area_map, 1e6, {}, SPECS, 0.0)
        from_source = sum(bid.flexible_quantity for bid in orders.bids if bid.area == source)
        self.assertLessEqual(from_source, 2.0 + 1e-9)

    def test_the_destinations_room_goes_to_sources_that_can_fill_it(self):
        carriage, area_map = world()
        who = merchant()
        who.expected_prices[("salt", area_map.area_of("salt", "a"))] = 1.9        # the best-priced source...
        who.expected_volumes[("salt", area_map.area_of("salt", "a"))] = 2.0        # ...has little to sell
        who.expected_volumes[("salt", area_map.area_of("salt", "b"))] = 1000.0
        who.expected_volumes[("salt", area_map.area_of("salt", "c"))] = 1000.0
        orders = merchants.orders(who, View(), carriage, area_map, 1e6, {}, SPECS, 0.0)
        self.assertAlmostEqual(total_bid(orders), merchants.MERCHANT_MARKET_SHARE * DESTINATION_VOLUME)
        self.assertGreater(len({bid.area for bid in orders.bids}), 1)


class RivalMerchantsTests(unittest.TestCase):
    def test_merchants_together_stay_within_the_groups_share(self):
        carriage, area_map = world()
        shares = merchants.RouteShares()
        placed = 0.0
        for name in ("m1", "m2", "m3", "m4", "m5", "m6", "m7", "m8", "m9"):
            placed += total_bid(merchants.orders(merchant(name), View(), carriage, area_map, 1e6, {}, SPECS, 0.0, shares))
        from sim.economy import merchants_shares
        self.assertLessEqual(placed, merchants_shares.MERCHANT_GROUP_SHARE * DESTINATION_VOLUME + 1e-9)

    def test_a_late_merchant_gets_what_the_earlier_ones_left(self):
        carriage, area_map = world()
        shares = merchants.RouteShares()
        first = total_bid(merchants.orders(merchant("m1"), View(), carriage, area_map, 1e6, {}, SPECS, 0.0, shares))
        second = total_bid(merchants.orders(merchant("m2"), View(), carriage, area_map, 1e6, {}, SPECS, 0.0, shares))
        self.assertAlmostEqual(first, merchants.MERCHANT_MARKET_SHARE * DESTINATION_VOLUME)
        self.assertGreater(second, 0.0)


if __name__ == "__main__":
    unittest.main()
