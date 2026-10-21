"""Merchants that see the same prices at the same rate share one route search per good, and the shared
rows are exactly what a fresh search returns; a changed price, rate or spec is never answered from the memo."""

QUICK_TOPIC = True

import unittest

from sim.economy import merchants, merchants_route_memo
from sim.economy.types import GoodSpec
from sim.tests.test_economy_merchants import SPECS, View, merchant, world

GOODS = ("salt", "fish")


def routes(who, carriage, area_map, rate, specs=SPECS, view=None):
    return merchants._candidate_routes(who, view or View({}), carriage, area_map, {}, specs, rate)


def fresh_routes(who, rate, specs=SPECS, view=None):
    """The same question on a world with nothing remembered."""
    carriage, area_map, _area_a, _area_b = world(GOODS)
    return routes(who, carriage, area_map, rate, specs, view)


class RouteMemoTests(unittest.TestCase):
    def setUp(self):
        self.carriage, self.area_map, self.area_a, self.area_b = world(GOODS)

    def merchant_at(self, price_a, price_b, name="m"):
        prices = {(good, self.area_a[good]): price_a for good in GOODS}
        prices.update({(good, self.area_b[good]): price_b for good in GOODS})
        return merchant(name, prices)

    def test_shared_rows_equal_a_fresh_search(self):
        who = self.merchant_at(2.0, 4.0)
        first = routes(who, self.carriage, self.area_map, 0.05)
        again = routes(self.merchant_at(2.0, 4.0, "other"), self.carriage, self.area_map, 0.05)
        self.assertTrue(first)
        self.assertEqual(again, first)
        self.assertEqual(first, fresh_routes(who, 0.05))

    def test_one_search_per_good_for_merchants_with_the_same_prices(self):
        searches = []
        original = merchants.merchants_routes_array.good_routes_aligned
        merchants.merchants_routes_array.good_routes_aligned = lambda *args: searches.append(args[0]) or original(*args)
        try:
            for name in ("a", "b", "c"):
                routes(self.merchant_at(2.0, 4.0, name), self.carriage, self.area_map, 0.05)
        finally:
            merchants.merchants_routes_array.good_routes_aligned = original
        self.assertEqual(sorted(searches), sorted(GOODS))

    def test_a_different_rate_is_searched_again(self):
        who = self.merchant_at(2.0, 4.0)
        low = routes(who, self.carriage, self.area_map, 0.0)
        high = routes(who, self.carriage, self.area_map, 0.9)
        self.assertNotEqual(low, high)
        self.assertEqual(high, fresh_routes(who, 0.9))
        self.assertEqual(routes(who, self.carriage, self.area_map, 0.0), low)

    def test_a_different_price_is_searched_again(self):
        routes(self.merchant_at(2.0, 4.0), self.carriage, self.area_map, 0.05)
        moved = self.merchant_at(2.0, 3.2)
        self.assertEqual(routes(moved, self.carriage, self.area_map, 0.05), fresh_routes(moved, 0.05))

    def test_a_different_spec_is_searched_again(self):
        who = self.merchant_at(2.0, 4.0)
        routes(who, self.carriage, self.area_map, 0.05)
        spoiling = dict(SPECS, salt=GoodSpec("salt", 1000.0, 0.9, 0.0, "food"))
        self.assertEqual(routes(who, self.carriage, self.area_map, 0.05, spoiling),
                         fresh_routes(who, 0.05, spoiling))

    def test_prices_read_from_the_view_are_part_of_the_question(self):
        who = merchant("v")
        cheap = View({("salt", self.area_a["salt"]): 2.0, ("salt", self.area_b["salt"]): 4.0})
        dear = View({("salt", self.area_a["salt"]): 2.0, ("salt", self.area_b["salt"]): 2.1})
        first = routes(who, self.carriage, self.area_map, 0.05, view=cheap)
        second = routes(who, self.carriage, self.area_map, 0.05, view=dear)
        self.assertNotEqual(first, second)
        self.assertEqual(second, fresh_routes(who, 0.05, view=dear))

    def test_the_memo_is_bounded_per_good(self):
        for step in range(merchants_route_memo.SLOTS_PER_GOOD + 3):
            routes(self.merchant_at(2.0, 4.0 + step), self.carriage, self.area_map, 0.05)
        slots = merchants_route_memo._memos[self.carriage]
        self.assertTrue(all(len(entries) <= merchants_route_memo.SLOTS_PER_GOOD for entries in slots.values()))


class HeldStockSearchTests(unittest.TestCase):
    """A merchant with nothing to spend searches only the goods and areas it holds stock in, and its routes
    are the ones the full search gives."""

    def setUp(self):
        self.carriage, self.area_map, self.area_a, self.area_b = world(GOODS)
        prices = {(good, self.area_a[good]): 2.0 for good in GOODS}
        prices.update({(good, self.area_b[good]): 4.0 for good in GOODS})
        self.who = merchant("m", prices)

    def test_the_partial_rows_are_rows_of_the_full_search(self):
        held = {("salt", "a"): 5.0}
        full = merchants._candidate_routes(self.who, View({}), self.carriage, self.area_map, held, SPECS, 0.05)
        partial = merchants._candidate_routes(self.who, View({}), self.carriage, self.area_map, held, SPECS, 0.05,
                                              merchants.held_by_good(held))
        self.assertTrue(partial)
        self.assertEqual(partial, [row for row in full if row[1] == "salt" and "a" in row[2].tiles])

    def test_no_cash_still_sends_held_stock_along_the_route(self):
        held = {("salt", "a"): 5.0}
        with_cash = merchants.orders(self.who, View({}), self.carriage, self.area_map, 1000.0, held, SPECS, 0.05)
        routes_with_cash = dict(self.who.routes)
        without_cash = merchants.orders(self.who, View({}), self.carriage, self.area_map, 0.0, held, SPECS, 0.05)
        self.assertTrue(with_cash.bids)
        self.assertEqual(without_cash.bids, ())
        self.assertEqual(self.who.routes[("salt", "a")], routes_with_cash[("salt", "a")])


if __name__ == "__main__":
    unittest.main()
