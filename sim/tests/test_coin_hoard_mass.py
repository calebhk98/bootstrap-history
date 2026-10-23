"""Complaint 273: a treasury of coin has a mass from its coin metal and a guard-and-vault cost from that mass. The
rules are `coin_metal` (plain arithmetic) and `CoinHoardMixin.coin_hoard` on a stub game. The screens that show the hoard
is rounded for them by `coin_hoard_report`; the step's charge is `coin_keeping_due`, both on a stub game."""
QUICK_TOPIC = True

import types
import unittest

import sim.engine.core  # noqa: F401  (loads the engine in its import order)
from sim.engine.coin_hoard import KEEPING_BASIS, CoinHoardMixin
from sim.engine.data import load_civ
from sim.world import coin_metal

KG_PER_UNIT = 4.0
GUARD_HOURS = 60.0
MONEY_PER_HOUR = 2.0


def stub_game(civ_id, capital):
    game = types.SimpleNamespace(civ=load_civ(civ_id), capital=capital,
                                 labour=types.SimpleNamespace(money_per_labour_hour=lambda: MONEY_PER_HOUR))
    game.coin_kg_per_unit = lambda: CoinHoardMixin.coin_kg_per_unit(game)
    game.coin_keeping_cost_per_year = lambda money: CoinHoardMixin.coin_keeping_cost_per_year(game, money)
    game.coin_hoard = lambda: CoinHoardMixin.coin_hoard(game)
    return game


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
        rome, han = stub_game("rome_100ad", 1.0e6).coin_hoard(), stub_game("han_china_100ad", 1.0e6).coin_hoard()
        self.assertEqual(rome["metal"], load_civ("rome_100ad")["coin_standard"]["material"])
        self.assertEqual(han["metal"], load_civ("han_china_100ad")["coin_standard"]["material"])
        self.assertNotEqual(rome["metal"], han["metal"])

    def test_the_hoard_mass_uses_the_civilisations_metal_in_one_coin(self):
        game = stub_game("rome_100ad", 1.0e6)
        self.assertAlmostEqual(game.coin_hoard()["tonnes"], 1.0e6 * load_civ("rome_100ad")["coin_standard"]["kg_per_unit"] / 1000.0)

    def test_the_hoard_states_its_basis_and_costs_money_to_keep(self):
        hoard = stub_game("han_china_100ad", 1.0e6).coin_hoard()
        self.assertGreater(hoard["keeping_cost_per_year"], 0.0)
        self.assertEqual(hoard["basis"], KEEPING_BASIS)

    def test_a_purse_in_debt_holds_no_coin_and_owes_nothing(self):
        hoard = stub_game("han_china_100ad", -5.0).coin_hoard()
        self.assertEqual((hoard["tonnes"], hoard["keeping_cost_per_year"]), (0.0, 0.0))

    def test_twice_the_money_is_twice_the_hoard(self):
        once, twice = stub_game("han_china_100ad", 1.0e6).coin_hoard(), stub_game("han_china_100ad", 2.0e6).coin_hoard()
        self.assertAlmostEqual(twice["tonnes"], 2.0 * once["tonnes"])
        self.assertAlmostEqual(twice["keeping_cost_per_year"], 2.0 * once["keeping_cost_per_year"])


def keeping_game(capital, credit_limit):
    game = stub_game("han_china_100ad", capital)
    game.state = types.SimpleNamespace(household=types.SimpleNamespace(capital=capital))
    game.credit_limit = lambda: credit_limit
    return game


class KeepingPaidFromWhatTheHouseholdCanBear(unittest.TestCase):

    def test_a_household_with_room_pays_what_the_hoard_owes(self):
        game = keeping_game(1.0e6, 0.0)
        owed, paid = CoinHoardMixin.coin_keeping_due(game, 0.0, 0.0, 0.0, 0.0)
        self.assertGreater(owed, 0.0)
        self.assertEqual(paid, owed)
        self.assertEqual(owed, game.coin_hoard()["keeping_cost_per_year"])

    def test_the_guard_is_paid_from_what_is_left_after_the_years_other_costs(self):
        game = keeping_game(1000.0, 500.0)
        owed = CoinHoardMixin.coin_keeping_due(game, 0.0, 0.0, 0.0, 0.0)[0]
        # room = capital 1000 + credit line 500 + revenue 100 - upkeep 20 - living 1560 - mines 10
        owed_again, paid = CoinHoardMixin.coin_keeping_due(game, 100.0, 20.0, 1560.0, 10.0)
        self.assertGreater(owed, 10.0)
        self.assertEqual((owed_again, paid), (owed, 10.0))

    def test_a_household_with_no_room_pays_nothing_never_a_negative_sum(self):
        game = keeping_game(10.0, 0.0)
        owed, paid = CoinHoardMixin.coin_keeping_due(game, 0.0, 0.0, 1.0e9, 0.0)
        self.assertEqual(paid, 0.0)
        self.assertGreaterEqual(owed, 0.0)


class HoardReportForTheScreens(unittest.TestCase):

    def test_the_report_is_the_hoard_rounded_with_its_metal_and_basis(self):
        game = stub_game("han_china_100ad", 123456.789)
        game.coin_hoard_report = lambda: CoinHoardMixin.coin_hoard_report(game)
        hoard, report = game.coin_hoard(), game.coin_hoard_report()
        self.assertEqual((report["metal"], report["basis"]), (hoard["metal"], hoard["basis"]))
        self.assertEqual(report["tonnes"], round(hoard["tonnes"], 3))
        self.assertEqual(report["keeping_cost_per_year"], round(hoard["keeping_cost_per_year"], 1))


if __name__ == "__main__":
    unittest.main()
