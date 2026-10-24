"""Complaint 629: carriers are durable goods. Carts, pack saddles, barges, ships and the animals that pull them have
recipes and service lives, a tonne-km wears the carrier stock of the mode that carried it, and carriage buys carriers
through the goods market."""

QUICK_TOPIC = True

import dataclasses
import json
import os
import types
import unittest

from sim.economy import carriage_fleet_book, carriage_wear
from sim.economy.accounts import Book, DeliveredMove
from sim.economy.merchants import Merchant
from sim.economy.types import EDGE_PRODUCTION, GoodsMove, GoodSpec, Recipe
from sim.geography.api import carriage_rates
from sim.tests import economy_fixture as fixture
from sim.tests.test_economy_carriage_hours import trading_setup
from sim.world import demand

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
CARRIERS = ("cart", "pack_saddle", "river_barge", "merchant_ship", "ox", "mule")


def service_lives():
    with open(os.path.join(DATA, "world", "service_lives.json"), encoding="utf-8") as handle:
        return json.load(handle)["years"]


class CarrierData(unittest.TestCase):
    def test_every_carrier_has_a_recipe_that_marks_what_it_serves(self):
        production = demand.production_data()
        for good in CARRIERS:
            self.assertIn("carrier_use", production[good], good)
            self.assertGreater(production[good]["carrier_use"]["days_per_year"], 0.0)
        for good in ("cart", "pack_saddle", "river_barge"):
            self.assertTrue(production[good]["labour_hours"], good)
            self.assertTrue(production[good]["capital_asset"], good)
            self.assertGreater(production[good]["unit_mass_kg"], 0.0)

    def test_every_carrier_has_a_sourced_service_life(self):
        lives = service_lives()
        for good in CARRIERS:
            self.assertGreater(lives[good]["years"], 0.0, good)
            self.assertIn(lives[good]["confidence"], "ABCD", good)
            self.assertGreater(len(lives[good]["source"]), 40, good)

    def test_every_worn_carrier_of_a_geography_mode_is_a_good_with_a_life(self):
        production = demand.production_data()
        uses = {good: entry["carrier_use"] for good, entry in production.items() if entry.get("carrier_use")}
        lives = {good: entry["years"] for good, entry in service_lives().items()}
        rates = carriage_rates(["pack", "cart", "road", "river_boat", "canal", "sail"])
        worn = carriage_wear.table(rates, uses, lives)
        self.assertEqual(sorted(worn), sorted(rates))
        for mode, (_per_day, rows) in worn.items():
            self.assertEqual(len(rows), len(rates[mode]["carriers"]), mode)
            for good, units in rows:
                self.assertGreater(units, 0.0, (mode, good))
        self.assertEqual({good for _day, rows in worn.values() for good, _units in rows},
                         {"cart", "pack_saddle", "river_barge", "merchant_ship", "ox", "mule"})


class WearRule(unittest.TestCase):
    def test_a_tonne_km_wears_the_teams_count_over_its_lifetime_tonne_km(self):
        # two oxen live 5 years working 150 days a year, a team moving 20 tonne-km a day: 2 / 15000
        self.assertAlmostEqual(carriage_wear.units_per_tonne_km(2.0, 5.0, 150.0, 20.0), 2.0 / 15000.0)

    def test_a_cart_wears_by_its_own_life_and_the_tonne_km_a_team_moves(self):
        rates = {"cart": {"carriers": [["vehicle", "cart", 1.0]], "tonne_km_per_team_day": 24.0, "team_payload_tonnes": 1.0}}
        worn = carriage_wear.table(rates, {"cart": {"serves": {"vehicle": "cart"}, "days_per_year": 150.0}}, {"cart": 10.0})
        self.assertAlmostEqual(worn["cart"][1][0][1], 1.0 / (10.0 * 150.0 * 24.0))

    def test_a_hull_payload_replaces_geographys(self):
        rates = {"sail": {"carriers": [["model", "sailing", 1.0]], "tonne_km_per_team_day": 1200.0, "team_payload_tonnes": 120.0}}
        use = {"serves": {"model": "sailing"}, "days_per_year": 150.0, "payload_tonnes": 24.0}
        worn = carriage_wear.table(rates, {"ship": use}, {"ship": 30.0})
        self.assertAlmostEqual(worn["sail"][1][0][1], 1.0 / (30.0 * 150.0 * 240.0))

    def test_a_good_with_no_life_wears_nothing(self):
        rates = {"cart": {"carriers": [["vehicle", "cart", 1.0]], "tonne_km_per_team_day": 24.0, "team_payload_tonnes": 1.0}}
        self.assertEqual(carriage_wear.table(rates, {"cart": {"serves": {"vehicle": "cart"}, "days_per_year": 150.0}}, {}), {})


CART = "cart"
WEAR_PER_TONNE_KM = 0.0005
CART_TONNE_KM_PER_TEAM_DAY = carriage_rates(["cart"])["cart"]["tonne_km_per_team_day"]


def basic_merchant():
    return Merchant("m1", "town", "owner", 100.0, {}, {})


def carrying_setup():
    specs = dict(fixture.specs())
    specs[CART] = GoodSpec(CART, 200.0, 0.0, 10.0, "carrier", capital_asset=True)
    recipes = dict(fixture.recipes())
    recipes["make_cart"] = Recipe("make_cart", {CART: 1.0}, {fixture.METAL: 2.0}, {fixture.SMITH: 50.0})
    base = trading_setup()
    return dataclasses.replace(
        base, specs=specs, recipes=recipes, opening_prices=dict(base.opening_prices, **{CART: 400.0}),
        carriage_carriers={"cart": (CART_TONNE_KM_PER_TEAM_DAY, ((CART, WEAR_PER_TONNE_KM),))})


class CarriersInTheBook(unittest.TestCase):
    """What a merchant holds and wears of its carriers, `carriage_wear.settle` and `carriage_fleet_book.bids` on built inputs."""

    def book_holding(self, bought=0.0, kept=0.0):
        book = Book()
        if bought:
            book.move(GoodsMove(EDGE_PRODUCTION, "m1", CART, "town", bought, "test"))
        if kept:
            book.move(GoodsMove(EDGE_PRODUCTION, carriage_wear.account("m1"), CART, "town", kept, "test"))
        return book

    def kept(self, book):
        return carriage_fleet_book.held(book, "m1", [CART])[CART]

    def test_the_carriers_a_merchant_bought_go_into_its_carrier_account_and_nothing_is_used_up(self):
        book = self.book_holding(bought=3.0, kept=2.0)
        carriage_wear.settle(basic_merchant(), book, [CART], {})
        self.assertAlmostEqual(self.kept(book), 5.0)
        self.assertEqual(book.holdings("m1")["goods"].get(CART, {}).get("town", 0.0), 0.0)

    def test_wear_asked_of_a_good_is_taken_off_the_stock_held(self):
        book = self.book_holding(kept=5.0)
        carriage_wear.settle(basic_merchant(), book, [CART], {CART: 2.0})
        self.assertAlmostEqual(self.kept(book), 3.0)

    def test_wear_beyond_what_is_held_takes_only_what_is_held(self):
        book = self.book_holding()
        moves = carriage_wear.settle(basic_merchant(), book, [CART], {CART: 2.0})
        self.assertEqual(moves, [])
        self.assertEqual(self.kept(book), 0.0)

    def test_a_merchant_bids_for_the_fleet_its_routes_call_for_less_what_it_holds(self):
        setup = types.SimpleNamespace(specs={CART: GoodSpec(CART, 200.0, 0.0, 10.0, "carrier", capital_asset=True)},
                                      carriage_carriers={"cart": (24.0, ((CART, WEAR_PER_TONNE_KM),))}, opening_prices={CART: 400.0})
        merchant = basic_merchant()
        merchant.carrier_wear = {}
        merchant.carrier_fleet_wanted = {CART: 5.5 / 10.0}
        record = types.SimpleNamespace(book=self.book_holding(kept=5.0), merchants={"m1": merchant})
        view = types.SimpleNamespace(price=lambda good, area: 400.0)
        area_map = types.SimpleNamespace(goods=lambda: [CART], area_of=lambda good, tile: "area:" + tile)
        bids, budget = carriage_fleet_book.bids(setup, record, view, area_map)
        self.assertEqual([(bid.buyer, bid.good, bid.tile) for bid in bids], [("m1", CART, merchant.home_tile)])
        self.assertAlmostEqual(bids[0].floor_quantity, 0.5)
        self.assertAlmostEqual(budget["m1"], 0.5 * 400.0)


class ExposureOfShipments(unittest.TestCase):
    def test_n_tonne_km_wear_n_times_the_rate(self):
        setup = carrying_setup()
        carriage = setup.carriage_table()
        wear = carriage_wear.Wear(setup, carriage, 0.0)
        tonne_km = sum(dict(carriage.haul(fixture.TOWN, fixture.FARMS).km_by_mode).values())
        spec = setup.specs[fixture.ORE]
        tonnes = 10.0
        move = DeliveredMove("m1", "m1", fixture.ORE, fixture.TOWN, tonnes * 1000.0 / spec.unit_mass_kg, "x", fixture.FARMS)
        units, days = carriage_wear.exposure(wear, [move], setup.specs)
        team_days = dict(carriage.haul(fixture.TOWN, fixture.FARMS).team_days_by_mode)["cart"]
        # the team works the days geography's rate says on the ground crossed, and wears its units by the day
        self.assertAlmostEqual(units[CART], tonnes * team_days * CART_TONNE_KM_PER_TEAM_DAY * WEAR_PER_TONNE_KM, places=9)
        # the days follow geography's rate on the ground the haul crosses (its class pace), not a typed figure
        self.assertAlmostEqual(days["cart"], tonnes * dict(carriage.haul(fixture.TOWN, fixture.FARMS).team_days_by_mode)["cart"], places=9)
        self.assertGreater(days["cart"], tonnes * tonne_km / CART_TONNE_KM_PER_TEAM_DAY)


if __name__ == "__main__":
    unittest.main()
