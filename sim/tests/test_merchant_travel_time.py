"""Complaints/517: a shipment takes the route's travel time (a haul over a year arrives the year after and
carries the goods meanwhile), the merchant prices that into the trade, and a distant market's price reaches
it with a lag that grows with distance."""

import json
import unittest

from sim.economy import merchants, merchants_transit
from sim.economy.accounts import Book
from sim.economy.market_areas import AreaMap
from sim.economy.merchants import Merchant
from sim.economy.record import EconomyRecord
from sim.economy.types import EDGE_PRODUCTION, EDGE_SPOILAGE, Fill, GoodsMove, GoodSpec
from sim.tests import economy_fixture as fixture
from sim.tests.test_economy_merchants import INTEREST_RATE, SPECS, View
from sim.tests.test_economy_tile_costs import star_tiles, unit_cost_table

NEAR_KM = 300.0           # a few weeks by cart
FAR_KM = 5000.0           # more than a year by cart
SPECS_HERE = dict(SPECS)


def world_apart(km, good="salt"):
    tiles = star_tiles("a", ["b"], km)
    carriage = unit_cost_table(tiles, "a", "b")          # a tonne between the tiles costs one
    area_map = AreaMap(("a", "b"), carriage, [(SPECS[good], 2.0)], {"a": 10.0, "b": 5.0}, threshold_share=0.01)
    return carriage, area_map, area_map.area_of(good, "a"), area_map.area_of(good, "b")


def shipper(km, good="salt", quantity=10.0):
    """A merchant holding `quantity` of the good on tile a with a route to tile b `km` away, and the dispatch."""
    carriage, _area_map, area_a, area_b = world_apart(km, good)
    who = Merchant("m1", "a", "owner", 100.0)
    who.routes = {(good, "a"): ("b", area_b)}
    book = Book()
    book.move(GoodsMove(EDGE_PRODUCTION, "m1", good, "a", quantity, "stock"))
    done = merchants.dispatch(who, (Fill("m1", good, area_a, "a", quantity, 2.0, "buy"),), carriage, SPECS, "coin",
                              1000.0, {(good, "a"): quantity})
    book.post((), done.moves)
    return who, book, done


class TravelTimeTests(unittest.TestCase):
    def test_the_carriage_table_gives_days_that_grow_with_distance(self):
        near = world_apart(NEAR_KM)[0].days_between("a", "b")
        far = world_apart(FAR_KM)[0].days_between("a", "b")
        self.assertLess(near, 365.0)
        self.assertGreater(far, 365.0)

    def test_a_short_haul_arrives_at_once(self):
        who, book, _done = shipper(NEAR_KM)
        self.assertEqual(who.in_transit, [])
        self.assertEqual(book.stock("m1", "salt", "b"), 10.0)

    def test_a_haul_over_a_year_is_in_transit_and_arrives_the_year_after(self):
        who, book, _done = shipper(FAR_KM)
        self.assertEqual(book.stock("m1", "salt", "b"), 0.0)
        self.assertEqual([(each.good, each.quantity, each.destination_tile, each.years_left) for each in who.in_transit],
                         [("salt", 10.0, "b", 1)])
        book.move_many(merchants_transit.advance(who, SPECS))
        self.assertEqual(book.stock("m1", "salt", "b"), 10.0)
        self.assertEqual(who.in_transit, [])

    def test_a_haul_of_more_than_two_years_arrives_the_third_year(self):
        who = Merchant("m1", "a", "owner", 100.0)
        who.in_transit = [merchants_transit.Shipment("salt", 4.0, "b", 2)]
        book = Book()
        book.move(GoodsMove(EDGE_PRODUCTION, merchants_transit.EDGE_TRANSIT, "salt", "b", 4.0, "stock"))
        book.move_many(merchants_transit.advance(who, SPECS))
        self.assertEqual((book.stock("m1", "salt", "b"), who.in_transit[0].years_left), (0.0, 1))
        book.move_many(merchants_transit.advance(who, SPECS))
        self.assertEqual(book.stock("m1", "salt", "b"), 4.0)

    def test_a_perishable_good_spoils_on_the_way(self):
        who, book, _done = shipper(FAR_KM, good="fish")
        book.move_many(merchants_transit.advance(who, SPECS))
        kept = 10.0 * (1.0 - SPECS["fish"].spoilage_per_year)
        self.assertAlmostEqual(book.stock("m1", "fish", "b"), kept)
        self.assertAlmostEqual(book.stock(EDGE_SPOILAGE, "fish", "b"), 10.0 - kept)
        self.assertAlmostEqual(book.goods_total("fish"), 0.0)          # nothing created or lost beyond the production edge

    def test_a_durable_good_arrives_whole(self):
        who, book, _done = shipper(FAR_KM, good="salt")
        book.move_many(merchants_transit.advance(who, SPECS))
        self.assertEqual(book.stock("m1", "salt", "b"), 10.0)

    def test_goods_in_transit_count_toward_the_merchant_wealth(self):
        who, _book, _done = shipper(FAR_KM)
        who.expected_prices = {("salt", "x"): 3.0}
        paid = merchants.close_year(who, {}, {}, 100.0, {}, lambda good, tile: "x", "coin", 0.05)
        # 100 cash and 10 in transit at 3 against a capital base of 100: a profit of 30, half of it paid out
        self.assertEqual(paid[0].amount, merchants.MERCHANT_PROFIT_PAYOUT_SHARE * 30.0)

    def test_a_shipment_in_transit_is_part_of_the_destination_supply(self):
        carriage, area_map, _area_a, _area_b = world_apart(NEAR_KM)
        who = Merchant("m1", "a", "owner", 100.0)
        who.in_transit = [merchants_transit.Shipment("salt", merchants.MERCHANT_MARKET_SHARE * 100.0, "b", 1)]
        _c, _m, area_a, area_b = world_apart(NEAR_KM)
        who.expected_prices = {("salt", area_a): 2.0, ("salt", area_b): 5.0}
        who.expected_volumes = {("salt", area_b): 100.0}
        orders = merchants.orders(who, View({}), carriage, area_map, 1e6, {}, SPECS, 0.0)
        self.assertEqual(orders.bids, ())


class FinancingTests(unittest.TestCase):
    def bids(self, km):
        carriage, area_map, area_a, area_b = world_apart(km)
        who = Merchant("m1", "a", "owner", 100.0)
        who.expected_prices = {("salt", area_a): 2.0, ("salt", area_b): 3.7}
        who.expected_volumes = {("salt", area_b): 100.0}
        return merchants.orders(who, View({}), carriage, area_map, 1000.0, {}, SPECS, 0.2).bids

    def test_a_trade_that_pays_for_one_year_of_interest_does_not_pay_for_two(self):
        self.assertEqual(len(self.bids(NEAR_KM)), 1)
        self.assertEqual(self.bids(FAR_KM), ())

    def test_years_held_follow_the_days(self):
        self.assertEqual([merchants_transit.years_held(days) for days in (0.0, 30.0, 365.0, 366.0, 800.0)],
                         [1, 1, 1, 2, 3])


class SaveTests(unittest.TestCase):
    def test_a_save_made_while_goods_are_in_transit_loads_with_them_in_transit(self):
        economy, _outcomes = fixture.run(fixture.small_setup(), 1)
        record = economy.record
        merchant = sorted(record.merchants.values(), key=lambda each: each.agent_id)[0]
        merchant.in_transit = [merchants_transit.Shipment("ore", 3.5, merchant.home_tile, 2)]
        record.book.move(GoodsMove(EDGE_PRODUCTION, merchants_transit.EDGE_TRANSIT, "ore", merchant.home_tile, 3.5, "stock"))
        loaded = EconomyRecord.from_record(json.loads(json.dumps(record.to_record())))
        again = loaded.merchants[merchant.agent_id]
        self.assertEqual(again.in_transit, merchant.in_transit)
        self.assertEqual(loaded.book.stock(merchants_transit.EDGE_TRANSIT, "ore", merchant.home_tile), 3.5)


class InformationLagTests(unittest.TestCase):
    """A merchant hears a price after the news has travelled: a year late for each year of the haul beyond
    the first, so a far market is seen as it was."""

    def lag(self, km):
        carriage = world_apart(km)[0]
        return lambda good, area: merchants_transit.years_held(carriage.days_between("a", "b")) - 1

    def test_the_lag_in_years_grows_with_distance(self):
        self.assertEqual(self.lag(NEAR_KM)("salt", "x"), 0)
        self.assertGreaterEqual(self.lag(FAR_KM)("salt", "x"), 1)

    def test_a_distant_price_is_learned_one_year_late(self):
        who = Merchant("m1", "a", "owner", 100.0)
        lag = self.lag(FAR_KM)
        merchants.close_year(who, {("salt", "far"): 10.0}, {("salt", "far"): 5.0}, 100.0, {}, lambda good, tile: "far",
                             "coin", 0.0, lag_years=lag)
        self.assertNotIn(("salt", "far"), who.expected_prices)          # the first year's news has not arrived
        merchants.close_year(who, {("salt", "far"): 20.0}, {("salt", "far"): 5.0}, 100.0, {}, lambda good, tile: "far",
                             "coin", 0.0, lag_years=lag)
        self.assertEqual(who.expected_prices[("salt", "far")], 10.0)     # it sees the first year, not the second

    def test_a_market_whose_area_is_gone_from_the_map_is_not_heard_from(self):
        who = Merchant("m1", "a", "owner", 100.0)
        merchants.close_year(who, {("salt", "gone"): 10.0, ("salt", "near"): 4.0}, {}, 100.0, {},
                             lambda good, tile: "near", "coin", 0.0,
                             lag_years=lambda good, area: 0 if area == "near" else None)
        self.assertNotIn(("salt", "gone"), who.expected_prices)
        self.assertEqual(who.expected_prices[("salt", "near")], 4.0)

    def test_a_near_price_is_learned_at_once(self):
        who = Merchant("m1", "a", "owner", 100.0)
        merchants.close_year(who, {("salt", "near"): 10.0}, {("salt", "near"): 5.0}, 100.0, {}, lambda good, tile: "near",
                             "coin", 0.0, lag_years=self.lag(NEAR_KM))
        self.assertEqual(who.expected_prices[("salt", "near")], 10.0)

    def test_a_merchant_does_not_read_the_distant_market_this_year(self):
        carriage, area_map, area_a, area_b = world_apart(FAR_KM)
        who = Merchant("m1", "a", "owner", 100.0)
        who.expected_volumes = {("salt", area_b): 100.0}
        view = View({("salt", area_a): 2.0, ("salt", area_b): 9.0})       # the far market is dear today
        lagged = merchants.orders(who, view, carriage, area_map, 1000.0, {}, SPECS, 0.0)
        self.assertEqual(lagged.bids, ())                                 # nothing known of it yet: no trade
        who.expected_prices = {("salt", area_a): 2.0, ("salt", area_b): 2.1}   # the news that has arrived says it is cheap
        self.assertEqual(merchants.orders(who, view, carriage, area_map, 1000.0, {}, SPECS, 0.0).bids, ())
        who.expected_prices = {("salt", area_a): 2.0, ("salt", area_b): 9.0}
        self.assertEqual(len(merchants.orders(who, view, carriage, area_map, 1000.0, {}, SPECS, 0.0).bids), 1)


if __name__ == "__main__":
    unittest.main()
