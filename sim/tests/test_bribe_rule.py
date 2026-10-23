"""Complaint 640: `bribe` buys down scandal and feeds the year's bribes into protection, takes no more than both can use, and
refuses a sum that is too small to move anything or more than the purse holds, changing nothing. Called on a stand-in `self`
carrying the household, the income and the unskilled hour's money; `update_protection` is recorded, not run."""
QUICK_TOPIC = True

import types
import unittest
from unittest import mock

from sim.engine import projects_starting
from sim.engine.projects_starting import StartingMixin

HOUR_MONEY = 2.0
INCOME = 1000.0


class Briber(StartingMixin):
    def __init__(self, scandal=2.0, capital=1.0e9, bribes_ytd=0.0, bribability=1.0):
        self.household = types.SimpleNamespace(scandal=scandal, capital=capital, bribes_ytd=bribes_ytd, protection=0.0)
        self.state = types.SimpleNamespace(household=self.household)
        self.value_weights = {"bribability": bribability}
        self.labour = types.SimpleNamespace(money_per_labour_hour=lambda: HOUR_MONEY)
        self.paid, self.protection_updates = [], 0

    def revenue(self):
        return INCOME

    def pay_edge(self, edge, money, text):
        self.paid.append(money)

    def update_protection(self):
        self.protection_updates += 1


def bribe(game, amount):
    with mock.patch.object(projects_starting, "money_text", lambda money, sim, grouped=False: "%g" % money):
        return game.bribe(amount)


class BribeTests(unittest.TestCase):
    def test_a_bribe_lowers_scandal_by_the_sum_over_the_price_of_a_point(self):
        game = Briber(scandal=2.0)
        price_of_a_point = game.BRIBE_PER_SCANDAL_POINT
        ok, _note = bribe(game, price_of_a_point)
        self.assertTrue(ok)
        self.assertAlmostEqual(game.household.scandal, 1.0)

    def test_the_sum_is_paid_to_officials_kept_in_the_years_bribes_and_protection_is_recalculated(self):
        game = Briber(scandal=2.0, bribes_ytd=100.0)
        amount = game.BRIBE_PER_SCANDAL_POINT
        bribe(game, amount)
        self.assertEqual(game.paid, [amount])
        self.assertAlmostEqual(game.household.bribes_ytd, game.BRIBE_MEMORY_DECAY * 100.0 + amount)
        self.assertEqual(game.protection_updates, 1)

    def test_a_sum_beyond_what_scandal_and_protection_can_use_is_not_all_taken(self):
        game = Briber(scandal=0.5)
        useful_ceiling = max(0.5 * game.BRIBE_PER_SCANDAL_POINT,
                             game.BRIBE_PROTECTION_CAP * INCOME * game.BRIBE_INCOME_SHARE)
        bribe(game, 100.0 * useful_ceiling)
        self.assertAlmostEqual(game.paid[0], useful_ceiling)
        self.assertEqual(game.household.scandal, 0.0)

    def test_a_zero_sum_is_refused_and_nothing_is_paid(self):
        game = Briber()
        ok, _note = bribe(game, 0.0)
        self.assertFalse(ok)
        self.assertEqual((game.paid, game.household.scandal, game.protection_updates), ([], 2.0, 0))

    def test_more_than_the_purse_holds_is_refused(self):
        game = Briber(capital=50.0)
        ok, _note = bribe(game, 60.0)
        self.assertFalse(ok)
        self.assertEqual((game.paid, game.household.capital), ([], 50.0))

    def test_with_no_scandal_too_little_to_move_protection_is_refused_and_nothing_changes(self):
        game = Briber(scandal=0.0)
        ok, _note = bribe(game, 1.0)
        self.assertFalse(ok)
        self.assertEqual((game.paid, game.household.bribes_ytd, game.protection_updates), ([], 0.0, 0))

    def test_with_no_scandal_a_serious_sum_still_buys_protection(self):
        game = Briber(scandal=0.0)
        ok, _note = bribe(game, 100.0)
        self.assertTrue(ok)
        self.assertEqual((game.paid, game.protection_updates), ([100.0], 1))
        self.assertEqual(game.household.bribes_ytd, 100.0)


if __name__ == "__main__":
    unittest.main()
