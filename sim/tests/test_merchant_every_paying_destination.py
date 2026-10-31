"""A merchant serves every destination whose route pays, not only the best one: the rows of the route search
name each paying destination of a source, the bids spread over them by what each takes, and the routes with the
least profit per unit of outlay wait when cash is short."""

QUICK_TOPIC = True

import unittest

from sim.economy import merchants
from sim.economy.merchants import Merchant
from sim.economy.types import GoodSpec, MarketArea

SALT = GoodSpec("salt", 1000.0, 0.0, 0.0, "food")
TILES = ("t0", "t1", "t2", "t3")
AREAS = [MarketArea("area%d" % number, "salt", (tile,), tile) for number, tile in enumerate(TILES)]


class LineCarriage:
    scale = 1.0

    def costs_from(self, source):
        return {tile: abs(TILES.index(tile) - TILES.index(source)) * 0.1 for tile in TILES}

    def days_between(self, from_tile, to_tile):
        return 10.0

    def cost_per_tonne(self, from_tile, to_tile):
        return abs(TILES.index(to_tile) - TILES.index(from_tile)) * 0.1


class StubAreaMap:
    def goods(self):
        return ["salt"]

    def areas(self, good):
        return AREAS

    def area_of(self, good, tile):
        return "area%d" % TILES.index(tile)


class NoView:
    year = 1

    def price(self, good, area):
        return None


def prices_by_area(*prices):
    return {area.area_id: price for area, price in zip(AREAS, prices)}


def merchant_expecting(prices, volumes):
    expected = {("salt", "area%d" % number): price for number, price in enumerate(prices)}
    return Merchant("m", "t0", "owner", 100.0, expected, {("salt", area): volume for area, volume in volumes.items()})


def orders_for(who, cash=1000.0):
    return merchants.orders(who, NoView(), LineCarriage(), StubAreaMap(), cash, {}, {"salt": SALT}, 0.0)


class GoodRoutesTests(unittest.TestCase):
    def test_two_destinations_that_both_pay_both_get_a_row(self):
        rows = merchants._good_routes("salt", SALT, AREAS, prices_by_area(1.0, 3.0, 3.5, None), LineCarriage(), 0.0, {"area0"})
        self.assertEqual(sorted(row[3].area_id for row in rows), ["area1", "area2"])

    def test_a_destination_that_does_not_pay_gets_no_row(self):
        rows = merchants._good_routes("salt", SALT, AREAS, prices_by_area(1.0, 1.1, 3.5, None), LineCarriage(), 0.0, {"area0"})
        self.assertEqual([row[3].area_id for row in rows], ["area2"])


class OrdersTests(unittest.TestCase):
    def test_a_source_supplies_both_paying_destinations(self):
        who = merchant_expecting((1.0, 3.0, 3.5), {"area1": 10.0, "area2": 10.0})
        orders_for(who)
        self.assertEqual(sorted(leg[0] for leg in who.routes[("salt", "t0")]), ["t1", "t2"])

    def test_a_destination_where_nothing_sold_gets_nothing(self):
        who = merchant_expecting((1.0, 3.0, 3.5), {"area1": 10.0, "area2": 0.0})
        orders_for(who)
        self.assertEqual([leg[0] for leg in who.routes[("salt", "t0")]], ["t1"])

    def test_with_cash_for_one_route_the_better_route_is_served(self):
        who = merchant_expecting((1.0, 3.0, 3.5), {"area1": 100.0, "area2": 100.0})
        orders_for(who, cash=5.0)
        self.assertEqual([leg[0] for leg in who.routes[("salt", "t0")]], ["t2"])      # the dearer destination nets more per unit of outlay

    def test_the_bids_at_the_source_add_up_to_what_the_routes_take(self):
        who = merchant_expecting((1.0, 3.0, 3.5), {"area1": 10.0, "area2": 10.0})
        bids = orders_for(who).bids
        self.assertAlmostEqual(sum(bid.flexible_quantity for bid in bids), sum(leg[2] for leg in who.routes[("salt", "t0")]))


class DispatchTests(unittest.TestCase):
    def test_stock_at_the_source_is_split_over_the_legs_by_weight(self):
        who = merchant_expecting((1.0, 3.0, 3.5), {})
        who.routes = {("salt", "t0"): (("t1", "area1", 3.0), ("t2", "area2", 1.0))}
        result = merchants.dispatch(who, (), LineCarriage(), {"salt": SALT}, "gold", 1000.0, {("salt", "t0"): 8.0})
        self.assertEqual({move.receiver_tile: move.quantity for move in result.moves}, {"t1": 6.0, "t2": 2.0})


if __name__ == "__main__":
    unittest.main()
