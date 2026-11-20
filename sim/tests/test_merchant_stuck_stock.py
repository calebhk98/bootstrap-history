"""merchant_stuck_stock: stock a merchant holds for a route and cannot crew is offered where it stands, and the coin set
aside to carry what it keeps does not buy new cargo. The plain rules, then `merchants.orders` given them."""

QUICK_TOPIC = True

import unittest

from sim.economy import merchants
from sim.economy.merchant_stuck_stock import (all_cash, carriage_set_aside, cash_less_carriage, crewed_share_by_tile, kept_whole,
                                              part_it_cannot_carry)
from sim.tests.test_economy_merchants import CARRIAGE_PER_UNIT, SPECS, View, merchant, world


def tile_of(key):
    return key.split("|", 1)[1]


class CrewedShareByTile(unittest.TestCase):
    def test_the_share_of_a_tiles_wanted_hours_that_was_hired(self):
        shares = crewed_share_by_tile({"carter|a": 100.0, "carter|b": 40.0}, {"carter|a": 25.0, "carter|b": 40.0}, tile_of)
        self.assertEqual(shares, {"a": 0.25, "b": 1.0})

    def test_the_scarcest_trade_of_a_tile_sets_its_share(self):
        shares = crewed_share_by_tile({"carter|a": 100.0, "boatman|a": 50.0}, {"carter|a": 80.0, "boatman|a": 10.0}, tile_of)
        self.assertAlmostEqual(shares["a"], 0.2)

    def test_nothing_hired_is_no_share_and_more_than_wanted_is_the_whole(self):
        shares = crewed_share_by_tile({"carter|a": 100.0, "carter|b": 10.0}, {"carter|b": 30.0}, tile_of)
        self.assertEqual(shares, {"a": 0.0, "b": 1.0})

    def test_a_tile_the_plan_wants_no_hours_for_is_left_out(self):
        self.assertEqual(crewed_share_by_tile({"carter|a": 0.0}, {"carter|a": 5.0}, tile_of), {})
        self.assertEqual(crewed_share_by_tile({}, {}, tile_of), {})


ROOM = 1e9      # more room at the destinations than any stock here


class StockOfferedWhereItStands(unittest.TestCase):
    def test_under_the_search_rules_stock_on_a_route_is_kept_whole(self):
        for share in (0.0, 0.4, 1.0):
            self.assertEqual(kept_whole(10.0, share, 0.0), 0.0)

    def test_the_part_the_crew_cannot_carry_is_offered(self):
        self.assertEqual(part_it_cannot_carry(10.0, 1.0, ROOM), 0.0)
        self.assertEqual(part_it_cannot_carry(10.0, 0.0, ROOM), 10.0)
        self.assertAlmostEqual(part_it_cannot_carry(10.0, 0.25, ROOM), 7.5)

    def test_the_part_the_destinations_have_no_room_for_is_offered(self):
        self.assertAlmostEqual(part_it_cannot_carry(10.0, 1.0, 4.0), 6.0)
        self.assertEqual(part_it_cannot_carry(10.0, 1.0, 0.0), 10.0)

    def test_the_lesser_of_crew_and_room_is_carried(self):
        self.assertAlmostEqual(part_it_cannot_carry(10.0, 0.25, 1.0), 9.0)
        self.assertAlmostEqual(part_it_cannot_carry(10.0, 0.25, 6.0), 7.5)

    def test_a_share_outside_nothing_to_all_counts_as_the_nearer_end(self):
        self.assertEqual(part_it_cannot_carry(10.0, 1.7, ROOM), 0.0)
        self.assertEqual(part_it_cannot_carry(10.0, -0.3, ROOM), 10.0)

    def test_no_stock_offers_nothing(self):
        self.assertEqual(part_it_cannot_carry(0.0, 0.0, ROOM), 0.0)


class CashForNewCargo(unittest.TestCase):
    def test_under_the_search_rules_all_the_cash_buys(self):
        self.assertEqual(all_cash(100.0, 30.0), 100.0)

    def test_the_carriage_set_aside_is_taken_off_and_never_below_nothing(self):
        self.assertEqual(cash_less_carriage(100.0, 30.0), 70.0)
        self.assertEqual(cash_less_carriage(100.0, 130.0), 0.0)
        self.assertEqual(cash_less_carriage(100.0, 0.0), 100.0)


class CarriageSetAside(unittest.TestCase):
    def test_the_units_kept_are_shared_over_the_legs_by_weight_at_each_legs_carriage(self):
        legs = (("b", "area_b", 3.0), ("c", "area_c", 1.0))
        carriage = {("b", "area_b"): 2.0, ("c", "area_c"): 10.0}
        self.assertAlmostEqual(carriage_set_aside(8.0, carriage, legs), 6.0 * 2.0 + 2.0 * 10.0)

    def test_a_leg_with_no_carriage_named_costs_nothing_and_nothing_kept_sets_nothing_aside(self):
        legs = (("b", "area_b", 1.0),)
        self.assertEqual(carriage_set_aside(8.0, {}, legs), 0.0)
        self.assertEqual(carriage_set_aside(0.0, {("b", "area_b"): 2.0}, legs), 0.0)


def ordered(cash, held, shares=None, clearing=False, price_a=2.0, price_b=5.0):
    """The orders of a merchant on the two-tile world: salt is cheap on `a` and dear on `b`, a unit costs CARRIAGE_PER_UNIT to carry."""
    carriage, area_map, area_a, area_b = world()
    who = merchant()
    who.expected_prices = {("salt", area_a["salt"]): price_a, ("salt", area_b["salt"]): price_b}
    who.expected_volumes = {("salt", area_b["salt"]): 100.0}
    rules = dict(stock_offered_where_it_stands=part_it_cannot_carry, cash_for_new_cargo=cash_less_carriage) if clearing else {}
    return merchants.orders(who, View({}), carriage, area_map, cash, held, SPECS, 0.0, crewed_share_by_tile=shares, **rules)


def offered(orders, tile="a"):
    return sum(offer.quantity for offer in orders.offers if offer.tile == tile)


class OrdersWithStockOnARoute(unittest.TestCase):
    HELD = {("salt", "a"): 10.0}

    def test_as_before_stock_on_a_tile_a_route_starts_from_is_not_offered(self):
        self.assertEqual(ordered(0.0, self.HELD).offers, ())
        self.assertEqual(ordered(0.0, self.HELD, shares={"a": 0.0}).offers, ())

    def test_with_no_crew_hired_the_whole_of_it_is_offered_where_it_stands(self):
        orders = ordered(0.0, self.HELD, shares={"a": 0.0}, clearing=True)
        self.assertAlmostEqual(offered(orders), 10.0)
        self.assertAlmostEqual(orders.offers[0].reservation_price, 2.0)      # its holding reservation: no interest, salt keeps

    def test_with_part_of_the_crew_hired_the_part_it_cannot_carry_is_offered(self):
        self.assertAlmostEqual(offered(ordered(0.0, self.HELD, shares={"a": 0.25}, clearing=True)), 7.5)

    def test_with_the_crew_hired_or_no_plan_yet_nothing_is_offered(self):
        self.assertEqual(ordered(0.0, self.HELD, shares={"a": 1.0}, clearing=True).offers, ())
        self.assertEqual(ordered(0.0, self.HELD, shares={}, clearing=True).offers, ())
        self.assertEqual(ordered(0.0, self.HELD, clearing=True).offers, ())

    def test_stock_with_a_crew_and_no_room_where_it_was_going_is_offered_where_it_stands(self):
        carriage, area_map, area_a, area_b = world()
        who = merchant()
        who.expected_prices = {("salt", area_a["salt"]): 2.0, ("salt", area_b["salt"]): 5.0}
        who.expected_volumes = {("salt", area_b["salt"]): 0.0}        # the market it was bound for takes nothing
        orders = merchants.orders(who, View({}), carriage, area_map, 0.0, self.HELD, SPECS, 0.0, crewed_share_by_tile={"a": 1.0},
                                  stock_offered_where_it_stands=part_it_cannot_carry, cash_for_new_cargo=cash_less_carriage)
        self.assertAlmostEqual(offered(orders), 10.0)

    def test_stock_off_every_route_is_offered_whole_under_either_rule(self):
        held = {("salt", "b"): 4.0}        # salt is dear on b: no route leaves it
        self.assertAlmostEqual(offered(ordered(0.0, held), "b"), 4.0)
        self.assertAlmostEqual(offered(ordered(0.0, held, shares={"b": 0.0}, clearing=True), "b"), 4.0)

    def test_the_route_is_kept_for_what_stays(self):
        carriage, area_map, area_a, area_b = world()
        who = merchant()
        who.expected_prices = {("salt", area_a["salt"]): 2.0, ("salt", area_b["salt"]): 5.0}
        who.expected_volumes = {("salt", area_b["salt"]): 100.0}
        merchants.orders(who, View({}), carriage, area_map, 0.0, self.HELD, SPECS, 0.0, crewed_share_by_tile={"a": 0.25},
                         stock_offered_where_it_stands=part_it_cannot_carry, cash_for_new_cargo=cash_less_carriage)
        self.assertIn(("salt", "a"), who.routes)


class OrdersBuyWithTheCashLeftAfterCarriage(unittest.TestCase):
    HELD = {("salt", "a"): 10.0}
    CASH = 30.0
    OUTLAY = 2.0 + CARRIAGE_PER_UNIT

    def bought(self, orders):
        return sum(bid.flexible_quantity for bid in orders.bids)

    def test_as_before_all_the_cash_buys(self):
        self.assertAlmostEqual(self.bought(ordered(self.CASH, self.HELD, shares={"a": 1.0})),
                               self.CASH * (1.0 - merchants.BUDGET_SAFETY_SHARE) / self.OUTLAY)

    def test_the_carriage_of_the_stock_kept_is_set_aside_first(self):
        left = (self.CASH - 10.0 * CARRIAGE_PER_UNIT) * (1.0 - merchants.BUDGET_SAFETY_SHARE)
        self.assertAlmostEqual(self.bought(ordered(self.CASH, self.HELD, shares={"a": 1.0}, clearing=True)), left / self.OUTLAY)

    def test_only_the_stock_kept_sets_carriage_aside(self):
        # a quarter crewed: 2.5 units stay on the route, 7.5 are offered where they stand
        left = (self.CASH - 2.5 * CARRIAGE_PER_UNIT) * (1.0 - merchants.BUDGET_SAFETY_SHARE)
        orders = ordered(self.CASH, self.HELD, shares={"a": 0.25}, clearing=True)
        self.assertAlmostEqual(self.bought(orders), 0.0)        # it does not buy a good where it is selling its own
        self.assertAlmostEqual(offered(orders), 7.5)
        self.assertGreater(left, 0.0)

    def test_carriage_beyond_the_cash_buys_nothing(self):
        self.assertEqual(ordered(5.0, self.HELD, shares={"a": 1.0}, clearing=True).bids, ())


if __name__ == "__main__":
    unittest.main()
