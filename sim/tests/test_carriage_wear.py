"""Complaint 629: carriers are durable goods. Carts, pack saddles, barges, ships and the animals that pull them have
recipes and service lives, a tonne-km wears the carrier stock of the mode that carried it, and carriage buys carriers
through the goods market."""
import dataclasses
import json
import os
import unittest
from unittest import mock

from sim.economy import carriage_wear, economy
from sim.economy.accounts import DeliveredMove
from sim.economy.merchants import Merchant
from sim.economy.types import GoodSpec, Recipe
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


def carrying_setup():
    specs = dict(fixture.specs())
    specs[CART] = GoodSpec(CART, 200.0, 0.0, 10.0, "carrier", capital_asset=True)
    recipes = dict(fixture.recipes())
    recipes["make_cart"] = Recipe("make_cart", {CART: 1.0}, {fixture.METAL: 2.0}, {fixture.SMITH: 50.0})
    base = trading_setup()
    return dataclasses.replace(
        base, specs=specs, recipes=recipes, opening_prices=dict(base.opening_prices, **{CART: 400.0}),
        carriage_carriers={"cart": (20.0, ((CART, WEAR_PER_TONNE_KM),))})


class CarriageWearsCarriers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = carrying_setup()
        cls.years = []
        real = economy.dispatch_merchants

        def watch(setup, record, carriage, ledger):
            held_before = {each.agent_id: sum(record.book.holdings(carriage_wear.account(each.agent_id))["goods"].get(CART, {}).values())
                           for each in record.merchants.values()}
            bought = {each.agent_id: sum(record.book.holdings(each.agent_id)["goods"].get(CART, {}).values())
                      for each in record.merchants.values()}
            real(setup, record, carriage, ledger)
            cls.years.append({
                "held_before": held_before, "bought": bought,
                "wear": {each.agent_id: dict(each.carrier_wear) for each in record.merchants.values()},
                "held_after": {each.agent_id: sum(record.book.holdings(carriage_wear.account(each.agent_id))["goods"].get(CART, {}).values())
                               for each in record.merchants.values()},
                "tonne_km": dict(record.carried)})
        with mock.patch.object(economy, "dispatch_merchants", watch):
            cls.economy, cls.outcomes = fixture.run(cls.setup, 25)

    def test_carrying_goods_wears_the_carrier_stock_by_the_tonne_km(self):
        shipped = [year for year in self.years if any(year["wear"][agent].get(CART, 0.0) > 0.0 for agent in year["wear"])]
        self.assertTrue(shipped, "no merchant shipped, so the scenario shows nothing")

    def test_wear_is_booked_even_where_the_merchant_held_no_carrier(self):
        first = next(year for year in self.years if any(year["wear"][agent].get(CART, 0.0) > 0.0 for agent in year["wear"]))
        agent = next(agent for agent, wear in first["wear"].items() if wear.get(CART, 0.0) > 0.0)
        self.assertGreater(first["wear"][agent][CART], 0.0)
        self.assertGreaterEqual(first["held_after"][agent], 0.0)

    def test_carriers_held_lose_the_units_worn_up_to_what_they_hold(self):
        for year in self.years:
            for agent, wear in year["wear"].items():
                arrived = year["held_before"][agent] + year["bought"][agent]
                self.assertAlmostEqual(year["held_after"][agent], max(0.0, arrived - wear.get(CART, 0.0)), places=9)

    def test_carriage_creates_demand_for_the_carrier_good(self):
        bought = [year for year in self.years if any(units > 0.0 for units in year["bought"].values())]
        self.assertTrue(bought, "merchants never bought a cart")
        self.assertGreater(sum(outcome.output.get(CART, 0.0) for outcome in self.outcomes), 0.0)

    def test_a_merchant_bids_for_the_units_last_year_wore(self):
        record = self.economy.record
        merchant = next(each for each in record.merchants.values())
        merchant.carrier_wear = {CART: 0.5}
        view = self.economy.view()
        bids, budget = carriage_wear.bids(self.setup, record, view, self.economy.area_map)
        mine = [bid for bid in bids if bid.buyer == merchant.agent_id and bid.good == CART]
        self.assertEqual(len(mine), 1)
        self.assertAlmostEqual(mine[0].floor_quantity, 0.5)
        self.assertEqual(mine[0].tile, merchant.home_tile)
        self.assertGreater(budget[merchant.agent_id], 0.0)

    def test_money_is_still_conserved(self):
        from sim.economy import money_audit
        report = money_audit.year_report(self.economy.record)
        self.assertTrue(report.ok, report.unexpected)


class ExposureOfShipments(unittest.TestCase):
    def test_n_tonne_km_wear_n_times_the_rate(self):
        setup = carrying_setup()
        carriage = setup.carriage_table()
        wear = carriage_wear.Wear(setup, carriage, 0.0)
        cost = carriage.cost_per_tonne(fixture.TOWN, fixture.FARMS)
        rate = setup.carriage_rates_at(0.0)["cart"]
        tonne_km = cost / rate
        spec = setup.specs[fixture.ORE]
        tonnes = 10.0
        move = DeliveredMove("m1", "m1", fixture.ORE, fixture.TOWN, tonnes * 1000.0 / spec.unit_mass_kg, "x", fixture.FARMS)
        units, days = carriage_wear.exposure(wear, [move], setup.specs)
        self.assertAlmostEqual(units[CART], tonnes * tonne_km * WEAR_PER_TONNE_KM, places=9)
        self.assertAlmostEqual(days["cart"], tonnes * tonne_km / 20.0, places=9)


if __name__ == "__main__":
    unittest.main()
