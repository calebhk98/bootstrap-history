"""Complaint 631: a merchant holds a fleet of carriers, and what it can carry follows the carriers it holds or hires."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import carriage_fleet, carriage_fleet_book, carriage_wear, inventory, merchants
from sim.economy.accounts import Book
from sim.economy.carriage_fleet import FleetLimit
from sim.economy.types import EDGE_PRODUCTION, Fill, GoodsMove, GoodSpec
from sim.tests.test_economy_merchants import SPECS, merchant, plan, world

CART = "cart"
CART_LIFE = 10.0
WEAR_PER_TONNE = 0.1        # carts worn carrying one tonne the haul


def fleet_of(capacity):
    return FleetLimit(lambda _source, _destination: {CART: WEAR_PER_TONNE}, capacity)


def ship(limit, held=10.0):
    carriage, _area_map, area_a, _area_b = world()
    who = merchant()
    plan(who, 2.0, 5.0)
    fills = (Fill("m1", "salt", area_a["salt"], "a", held, 2.0, "buy"),)
    return merchants.dispatch(who, fills, carriage, SPECS, "coin", 1000.0, {("salt", "a"): held}, fleet=limit)


class DispatchIsBoundByTheFleet(unittest.TestCase):
    def test_a_merchant_with_no_fleet_ships_nothing(self):
        done = ship(fleet_of({CART: 0.0}))
        self.assertEqual(done.moves, ())
        self.assertAlmostEqual(done.stranded[0][2], 10.0)

    def test_a_merchant_with_no_fleet_ships_only_what_it_hires(self):
        wear = types.SimpleNamespace(units_per_tonne=lambda _source, _destination: {CART: WEAR_PER_TONNE})
        limit = carriage_fleet_book.limit_for(wear, {CART: 0.0}, {CART: 0.4})
        done = ship(limit)
        self.assertAlmostEqual(done.moves[0].quantity, 0.4 / WEAR_PER_TONNE)     # tonnes the hired wear bears

    def test_capacity_follows_the_carriers_held(self):
        small = ship(fleet_of(carriage_fleet.capacity_of({CART: 3.0}, {CART: CART_LIFE})), held=100.0)
        large = ship(fleet_of(carriage_fleet.capacity_of({CART: 6.0}, {CART: CART_LIFE})), held=100.0)
        self.assertAlmostEqual(small.moves[0].quantity, 3.0 / CART_LIFE / WEAR_PER_TONNE)
        self.assertAlmostEqual(large.moves[0].quantity, 2.0 * small.moves[0].quantity)

    def test_a_fleet_that_bears_more_than_the_stock_carries_it_all(self):
        done = ship(fleet_of({CART: 100.0}))
        self.assertAlmostEqual(done.moves[0].quantity, 10.0)
        self.assertAlmostEqual(done.fleet_wanted[CART], 10.0 * WEAR_PER_TONNE)

    def test_what_the_stock_called_for_is_reported_even_when_the_fleet_cut_it(self):
        done = ship(fleet_of({CART: 0.2}))
        self.assertAlmostEqual(done.fleet_wanted[CART], 10.0 * WEAR_PER_TONNE)
        self.assertAlmostEqual(done.moves[0].quantity, 2.0)

    def test_a_carrier_good_that_is_not_held_does_not_limit(self):
        limit = FleetLimit(lambda _source, _destination: {"feed": 5.0}, {CART: 0.0})
        self.assertAlmostEqual(ship(limit).moves[0].quantity, 10.0)


class FleetInTheBook(unittest.TestCase):
    def book_with(self, units):
        book = Book()
        book.move(GoodsMove(EDGE_PRODUCTION, carriage_wear.account("m1"), CART, "a", units, "test"))
        return book

    def test_own_capacity_is_the_wear_the_held_carriers_bear_a_year(self):
        capacity = carriage_fleet_book.own_capacity(self.book_with(30.0), "m1", {CART: CART_LIFE})
        self.assertAlmostEqual(capacity[CART], 3.0)

    def test_a_merchant_holding_none_has_zero_capacity_not_no_limit(self):
        self.assertEqual(carriage_fleet_book.own_capacity(Book(), "m1", {CART: CART_LIFE}), {CART: 0.0})

    def test_wear_by_service_life_reduces_the_fleet(self):
        specs = {CART: GoodSpec(CART, 200.0, 0.0, CART_LIFE, "carrier", capital_asset=True)}
        account = carriage_wear.account("m1")
        book = self.book_with(30.0)
        holdings = {(account, CART, "a"): 30.0}
        book.move_many(inventory.wear_moves(holdings, specs, {account}))
        self.assertAlmostEqual(carriage_fleet_book.held(book, "m1", [CART])[CART], 30.0 * (1.0 - 1.0 / CART_LIFE))

    def test_a_paying_haul_buys_a_carrier(self):
        setup = types.SimpleNamespace(
            specs={CART: GoodSpec(CART, 200.0, 0.0, CART_LIFE, "carrier", capital_asset=True)},
            carriage_carriers={"cart": (24.0, ((CART, WEAR_PER_TONNE),))})
        record = types.SimpleNamespace(book=self.book_with(5.0))
        who = merchant()
        who.agent_id = "m1"
        who.carrier_fleet_wanted = {CART: 1.0}      # the routes called for a wear of one a year: ten carts
        self.assertAlmostEqual(carriage_fleet_book.to_buy(setup, record, who)[CART], 1.0 * CART_LIFE - 5.0)
        who.carrier_fleet_wanted = {CART: 0.1}      # a fleet already larger than the routes need buys none
        self.assertAlmostEqual(carriage_fleet_book.to_buy(setup, record, who)[CART], 0.0)


class HiringIdleFleets(unittest.TestCase):
    def test_the_idle_capacity_of_one_merchant_is_hired_by_the_one_short_of_it(self):
        hired, lent = carriage_fleet_book.share_idle({"a": {CART: 5.0}, "b": {CART: 0.0}}, {"a": {CART: 2.0}, "b": {CART: 1.5}})
        self.assertAlmostEqual(hired["b"][CART], 1.5)
        self.assertAlmostEqual(lent[CART]["a"], 1.5)

    def test_hiring_is_limited_to_what_is_idle(self):
        hired, lent = carriage_fleet_book.share_idle({"a": {CART: 1.0}, "b": {CART: 0.0}}, {"a": {CART: 0.0}, "b": {CART: 4.0}})
        self.assertAlmostEqual(hired["b"][CART], 1.0)
        self.assertAlmostEqual(lent[CART]["a"], 1.0)

    def test_the_lessee_pays_the_lessor_for_the_wear_it_put_on_the_hired_carriers(self):
        pay = carriage_fleet_book.rent_transfers("b", {CART: 1.5}, {CART: 1.0}, {CART: 0.0}, {CART: {"a": 1.5}}, {CART: 100.0}, "coin", 1e9)
        self.assertEqual([(each.payer, each.payee) for each in pay], [("b", "a")])
        self.assertAlmostEqual(pay[0].amount, 100.0)       # one unit of wear used, not the hired 1.5

    def test_rent_is_never_above_the_lessees_cash(self):
        pay = carriage_fleet_book.rent_transfers("b", {CART: 1.5}, {CART: 1.0}, {CART: 0.0}, {CART: {"a": 1.5}}, {CART: 100.0}, "coin", 30.0)
        self.assertAlmostEqual(pay[0].amount, 30.0)


class OpeningEndowment(unittest.TestCase):
    def test_merchants_open_with_carriers_sized_to_their_capital(self):
        from sim.economy.opening import open_economy
        from sim.tests.test_carriage_wear import CART as GAME_CART, carrying_setup
        record, _areas, _carriage = open_economy(carrying_setup())
        held = [carriage_fleet_book.held(record.book, each, [GAME_CART])[GAME_CART] for each in record.merchants]
        self.assertTrue(held and all(units > 0.0 for units in held))


if __name__ == "__main__":
    unittest.main()
