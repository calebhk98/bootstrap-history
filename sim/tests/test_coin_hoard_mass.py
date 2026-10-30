"""Complaint 273: a treasury of coin has a mass from its coin metal and a guard-and-vault cost from that mass. The
rules are `coin_metal` (plain arithmetic) and the coin module's `coin_hoard` view over plain values. The screens that show
the hoard have it rounded by `rules.hoard_report`; the step's charge is `rules.keeping_due` (and the module's quote)."""
QUICK_TOPIC = True

import unittest

import sim.engine.core  # noqa: F401  (loads the engine in its import order)
from sim.coin import rules
from sim.coin.constants import KEEPING_BASIS
from sim.coin.module import Coin
from sim.engine.data import load_civ
from sim.tests import module_harness
from sim.world import coin_metal

KG_PER_UNIT = 4.0
GUARD_HOURS = 60.0
MONEY_PER_HOUR = 2.0


def coin_module(civ_id, capital, credit_limit=0.0):
    """The coin module over a civilisation, a purse and a credit line."""
    return module_harness.build(Coin, views={"civilisation": load_civ(civ_id), "acting_balance": capital,
                                             "money_per_labour_hour": MONEY_PER_HOUR, "credit_limit": credit_limit})


class HoardMass(unittest.TestCase):

    def test_the_mass_is_the_coin_held_times_the_metal_in_one_coin(self):
        self.assertAlmostEqual(coin_metal.coin_tonnes(1.0e6, KG_PER_UNIT), 1.0e6 * KG_PER_UNIT / 1000.0)

    def test_a_purse_in_debt_holds_no_coin(self):
        self.assertEqual(coin_metal.coin_tonnes(-5.0, KG_PER_UNIT), 0.0)
        self.assertEqual(coin_metal.keeping_cost_per_year(-5.0, KG_PER_UNIT, GUARD_HOURS, MONEY_PER_HOUR), 0.0)

    def test_twice_the_money_is_twice_the_mass_and_twice_the_keeping_cost(self):
        once = coin_metal.keeping_cost_per_year(1.0e6, KG_PER_UNIT, GUARD_HOURS, MONEY_PER_HOUR)
        twice = coin_metal.keeping_cost_per_year(2.0e6, KG_PER_UNIT, GUARD_HOURS, MONEY_PER_HOUR)
        self.assertGreater(once, 0.0)
        self.assertAlmostEqual(twice, 2.0 * once)
        self.assertAlmostEqual(coin_metal.coin_tonnes(2.0e6, KG_PER_UNIT), 2.0 * coin_metal.coin_tonnes(1.0e6, KG_PER_UNIT))

    def test_keeping_costs_the_guards_hours_by_the_tonne_at_the_unskilled_hour(self):
        tonnes = coin_metal.coin_tonnes(1.0e6, KG_PER_UNIT)
        self.assertAlmostEqual(coin_metal.keeping_cost_per_year(1.0e6, KG_PER_UNIT, GUARD_HOURS, MONEY_PER_HOUR),
                               tonnes * GUARD_HOURS * MONEY_PER_HOUR)


class HoardOfACivilisation(unittest.TestCase):

    def test_the_hoard_names_the_civilisations_own_coin_metal(self):
        rome, han = coin_module("rome_100ad", 1.0e6).coin_hoard(), coin_module("han_china_100ad", 1.0e6).coin_hoard()
        self.assertEqual(rome["metal"], load_civ("rome_100ad")["coin_standard"]["material"])
        self.assertEqual(han["metal"], load_civ("han_china_100ad")["coin_standard"]["material"])
        self.assertNotEqual(rome["metal"], han["metal"])

    def test_the_hoard_mass_uses_the_civilisations_metal_in_one_coin(self):
        module = coin_module("rome_100ad", 1.0e6)
        self.assertAlmostEqual(module.coin_hoard()["tonnes"], 1.0e6 * load_civ("rome_100ad")["coin_standard"]["kg_per_unit"] / 1000.0)

    def test_the_hoard_states_its_basis_and_costs_money_to_keep(self):
        hoard = coin_module("han_china_100ad", 1.0e6).coin_hoard()
        self.assertGreater(hoard["keeping_cost_per_year"], 0.0)
        self.assertEqual(hoard["basis"], KEEPING_BASIS)

    def test_a_purse_in_debt_holds_no_coin_and_owes_nothing(self):
        hoard = coin_module("han_china_100ad", -5.0).coin_hoard()
        self.assertEqual((hoard["tonnes"], hoard["keeping_cost_per_year"]), (0.0, 0.0))

    def test_twice_the_money_is_twice_the_hoard(self):
        once, twice = coin_module("han_china_100ad", 1.0e6).coin_hoard(), coin_module("han_china_100ad", 2.0e6).coin_hoard()
        self.assertAlmostEqual(twice["tonnes"], 2.0 * once["tonnes"])
        self.assertAlmostEqual(twice["keeping_cost_per_year"], 2.0 * once["keeping_cost_per_year"])


class KeepingPaidFromWhatTheHouseholdCanBear(unittest.TestCase):

    def test_a_household_with_room_pays_what_the_hoard_owes(self):
        self.assertEqual(rules.keeping_due(250.0, 1.0e6, 0.0, 0.0, 0.0, 0.0, 0.0), (250.0, 250.0))

    def test_the_guard_is_paid_from_what_is_left_after_the_years_other_costs(self):
        # room = capital 1000 + credit line 500 + revenue 100 - upkeep 20 - living 1560 - mines 10 = 10
        self.assertEqual(rules.keeping_due(250.0, 1000.0, 500.0, 100.0, 20.0, 1560.0, 10.0), (250.0, 10.0))

    def test_a_household_with_no_room_pays_nothing_never_a_negative_sum(self):
        self.assertEqual(rules.keeping_due(250.0, 10.0, 0.0, 0.0, 0.0, 1.0e9, 0.0), (250.0, 0.0))

    def test_the_module_owes_the_hoards_keeping_cost_and_pays_it_from_a_purse_with_room(self):
        module = coin_module("han_china_100ad", 1.0e6)
        owed, paid = module.coin_keeping_due(0.0, 0.0, 0.0, 0.0)
        self.assertEqual(owed, module.coin_hoard()["keeping_cost_per_year"])
        self.assertEqual(paid, owed)

    def test_the_module_pays_only_the_room_a_purse_in_the_red_leaves(self):
        module = coin_module("han_china_100ad", 1000.0, credit_limit=500.0)
        owed, paid = module.coin_keeping_due(100.0, 20.0, 1.0e9, 10.0)
        self.assertGreater(owed, 0.0)
        self.assertEqual(paid, 0.0)


class HoardReportForTheScreens(unittest.TestCase):

    def test_the_report_is_the_hoard_rounded_with_its_metal_and_basis(self):
        held = {"metal": "silver", "tonnes": 1.23456, "keeping_cost_per_year": 98.7654, "basis": "guards"}
        self.assertEqual(rules.hoard_report(held),
                         {"metal": "silver", "tonnes": 1.235, "keeping_cost_per_year": 98.8, "basis": "guards"})


if __name__ == "__main__":
    unittest.main()
