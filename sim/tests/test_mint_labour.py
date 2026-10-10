"""The mint strikes coin by the minting recipe's labour and the coin standard's fineness; its charge is the
standard's mint_charge_share (sim/economy/mint.py, mint_labour.py; Complaint 374)."""

QUICK_TOPIC = True

import json
import os
import types as pytypes
import unittest

from sim.economy import currency, mint, mint_labour
from sim.economy.accounts import Book
from sim.economy.recipes import recipe_from_entry
from sim.economy.types import EDGE_ISSUE, EDGE_MINT, EDGE_PRODUCTION, GoodsMove, Transfer

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "data")
METAL = "silver_kg"
PER_UNIT = 0.01


def _recipe():
    with open(os.path.join(DATA, "production", "98_minting.json")) as handle:
        return recipe_from_entry("struck_silver_coin_kg", json.load(handle)["materials"]["struck_silver_coin_kg"])


def spec_of(fineness=None, charge=0.0):
    data = {"regime": "struck_coin", "material": METAL, "kg_per_unit": PER_UNIT}
    if fineness is not None:
        data["fineness"] = fineness
    if charge:
        data["mint_charge_share"] = charge
    return currency.currency_from_coin_standard("realm", data, "coin", issuer="state")


class FakeAreaMap:
    AREA = pytypes.SimpleNamespace(area_id="area", anchor_tile="t1", tiles=("t1", "t2"))

    def goods(self):
        return (METAL,)

    def area_of(self, good, tile):
        return "area"

    def areas(self, good):
        return (self.AREA,)


class FakeView:
    def wage(self, trade, area):
        return 2.0

    def basket_price_level(self, money):
        return 1.0


def world(spec, recipe="default"):
    book = Book()
    book.transfer(Transfer(EDGE_ISSUE, "a", "coin", 600.0, "opening"))
    book.transfer(Transfer(EDGE_ISSUE, "b", "coin", 400.0, "opening"))
    book.transfer(Transfer(EDGE_ISSUE, "state", "coin", 100000.0, "opening"))
    setup = pytypes.SimpleNamespace(
        civ_id="realm", state_agent="state", currency_id="coin", capital_tile="t1",
        opening_population_by_tile={"t1": 3.0, "t2": 1.0}, tiles={"t1": 0, "t2": 0},
        opening_wages={}, mint_recipe=_recipe() if recipe == "default" else recipe)
    record = pytypes.SimpleNamespace(book=book, currency=spec)
    mint.seed_opening_metal(setup, record)
    return setup, record


class Fineness(unittest.TestCase):
    def test_the_standard_states_fineness_and_it_defaults_to_pure_metal(self):
        self.assertEqual(spec_of().fineness, 1.0)
        self.assertEqual(spec_of(fineness=0.8).fineness, 0.8)

    def test_a_debased_coin_keeps_its_weight_and_loses_fineness(self):
        lighter = currency.debase(spec_of(fineness=0.8), PER_UNIT * 0.5)
        self.assertAlmostEqual(lighter.fineness, 0.4)

    def test_hours_per_kilogram_of_fine_metal_follow_the_standards_fineness_not_the_recipes(self):
        recipe = _recipe()
        pure = mint_labour.hours_per_fine_kilogram(recipe, spec_of())
        alloyed = mint_labour.hours_per_fine_kilogram(recipe, spec_of(fineness=0.5))
        for trade, hours in pure.items():
            self.assertAlmostEqual(alloyed[trade], 2.0 * hours)
            self.assertAlmostEqual(hours, recipe.labour_hours[trade] / recipe.outputs[recipe.recipe_id])


class Staffing(unittest.TestCase):
    def test_the_mint_bids_for_the_recipes_trades_and_is_funded_by_the_issuer(self):
        spec = spec_of(fineness=0.8)
        setup, record = world(spec)
        bids = []
        mint_labour.staff(setup, record, FakeView(), bids, capacity_fine_kilograms=10.0)
        self.assertEqual({bid.trade for bid in bids}, set(setup.mint_recipe.labour_hours))
        self.assertTrue(all(bid.employer == mint_labour.mint_agent(setup) for bid in bids))
        hours = mint_labour.hours_per_fine_kilogram(setup.mint_recipe, spec)
        for bid in bids:
            self.assertAlmostEqual(bid.hours, 10.0 * hours[bid.trade])
        self.assertGreater(record.book.balance(mint_labour.mint_agent(setup), "coin"), 0.0)
        self.assertTrue(record.book.check_conservation(1e-9).ok)

    def test_no_recipe_means_no_staff_and_no_limit(self):
        setup, record = world(spec_of(), recipe=None)
        bids = []
        mint_labour.staff(setup, record, FakeView(), bids, capacity_fine_kilograms=10.0)
        self.assertEqual(bids, [])
        self.assertEqual(mint_labour.strike_limit_fine_kilograms(setup, record.currency, {}), float("inf"))

    def test_strike_is_limited_by_the_hours_hired_in_the_scarcest_trade(self):
        spec = spec_of()
        setup, _record = world(spec)
        per_kilogram = mint_labour.hours_per_fine_kilogram(setup.mint_recipe, spec)
        hired = {trade: 4.0 * hours for trade, hours in per_kilogram.items()}
        scarce = next(iter(per_kilogram))
        hired[scarce] = 1.5 * per_kilogram[scarce]
        self.assertAlmostEqual(mint_labour.strike_limit_fine_kilograms(setup, spec, hired), 1.5)
        self.assertEqual(mint_labour.strike_limit_fine_kilograms(setup, spec, {}), 0.0)

    def test_unspent_wage_money_goes_back_to_the_issuer(self):
        setup, record = world(spec_of())
        mint_labour.staff(setup, record, FakeView(), [], capacity_fine_kilograms=10.0)
        before = record.book.balance("state", "coin")
        funded = record.book.balance(mint_labour.mint_agent(setup), "coin")
        mint_labour.close_year(setup, record)
        self.assertEqual(record.book.balance(mint_labour.mint_agent(setup), "coin"), 0.0)
        self.assertAlmostEqual(record.book.balance("state", "coin"), before + funded)


class StrikeCapacity(unittest.TestCase):
    def capacity(self, hours_hired):
        spec = spec_of(fineness=0.8)
        setup, record = world(spec)
        order_book = {}
        mint.mint_orders(setup, record, FakeAreaMap(), order_book, hours_hired=hours_hired)
        bids, _offers = order_book[(METAL, "area")]
        return sum(bid.flexible_quantity for bid in bids), setup, spec

    def test_without_hired_labour_the_mint_buys_no_metal(self):
        quantity, _setup, _spec = self.capacity({})
        self.assertEqual(quantity, 0.0)

    def test_hired_hours_set_how_much_metal_it_strikes(self):
        spec = spec_of(fineness=0.8)
        setup, _record = world(spec)
        per_kilogram = mint_labour.hours_per_fine_kilogram(setup.mint_recipe, spec)
        quantity, _setup, _spec = self.capacity({trade: 2.0 * hours for trade, hours in per_kilogram.items()})
        self.assertAlmostEqual(quantity, 2.0)

    def test_the_charge_stays_the_standards_mint_charge_share(self):
        charged = spec_of(fineness=0.8, charge=0.02)
        self.assertAlmostEqual(currency.mint_price(charged), 0.98 * currency.mint_parity(charged))


class InTheYearLoop(unittest.TestCase):
    """The small fixture economy steps with and without a minting recipe."""

    def run_years(self, recipe):
        from sim.tests import economy_fixture
        setup = economy_fixture.small_setup(mint_recipe=recipe)
        economy, outcomes = economy_fixture.run(setup, years=2)
        return setup, economy, outcomes

    def test_a_mint_with_a_recipe_hires_its_trade_and_leaves_no_wage_money_behind(self):
        from sim.tests import economy_fixture
        from sim.economy.types import Recipe
        recipe = Recipe("strike_coin", {"strike_coin": 100.0}, {}, {economy_fixture.SMITH: 50.0})
        _setup, economy_without, _without = self.run_years(None)
        setup, economy, with_mint = self.run_years(recipe)
        # the opening workforce already holds the mint's staff, so its hiring shows in hours, not in a scarcer wage
        def smith_hours(held):
            return sum(hours for key, hours in held.record.hours_hired.items()
                       if key.startswith(economy_fixture.SMITH + "|"))
        self.assertGreater(smith_hours(economy), smith_hours(economy_without))
        self.assertEqual(economy.record.book.balance(mint_labour.mint_agent(setup), "coin"), 0.0)
        self.assertTrue(economy.record.book.check_conservation(1e-6).ok)


class ShippedData(unittest.TestCase):
    def production(self):
        entries = {}
        directory = os.path.join(DATA, "production")
        for name in sorted(os.listdir(directory)):
            if name.endswith(".json"):
                with open(os.path.join(directory, name)) as handle:
                    entries.update(json.load(handle).get("materials", {}))
        return entries

    def test_every_struck_coin_civilisation_names_a_mint_recipe_run_by_the_mint(self):
        production = self.production()
        directory = os.path.join(DATA, "civilizations")
        seen = 0
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".json") or name.startswith("_"):
                continue
            with open(os.path.join(directory, name)) as handle:
                standard = json.load(handle).get("coin_standard", {})
            if standard.get("regime") != "struck_coin":
                continue
            seen += 1
            entry = production.get(standard.get("mint_recipe"))
            self.assertTrue(entry, name)
            self.assertEqual(entry.get("actor"), "mint", name)
            self.assertIn("labour_hours", entry, name)
        self.assertGreater(seen, 0)

    def test_firms_do_not_run_the_mint_recipe(self):
        from sim.engine import economy_port_setup
        production = self.production()
        allowed = economy_port_setup.allowed_entries(production, {"fin_coined_money"})
        self.assertNotIn("struck_silver_coin_kg", allowed)
        civ = {"coin_standard": {"mint_recipe": "struck_silver_coin_kg"}}
        self.assertEqual(economy_port_setup.mint_recipe_id(civ, production, {"fin_coined_money"}), "struck_silver_coin_kg")
        self.assertIsNone(economy_port_setup.mint_recipe_id(civ, production, set()))

    def test_england_states_its_fineness(self):
        with open(os.path.join(DATA, "civilizations", "england_1300.json")) as handle:
            self.assertEqual(json.load(handle)["coin_standard"]["fineness"], 0.925)


if __name__ == "__main__":
    unittest.main()
