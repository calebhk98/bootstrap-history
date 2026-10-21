"""SCENARIO: a Rome game past its credit line defaults and settles through the real purse, ledger and credit line.
The rules (what is owed after a write-off, when a default acts, the order of its answers) are in `test_insolvency_rules`."""

import unittest

from .harness import *  # noqa: F401,F403


def ruined(depth_in_limits):
    game = unopened_sim(civ="rome_100ad", capital=1000000.0)
    game.capital = -depth_in_limits * game.credit_limit()
    return game


def settled_lines(game):
    return [line for _year, line in game.state.household.log if getattr(line, "kind", "") == "insolvency_settled"]


class DefaultOnDebtInAGame(unittest.TestCase):
    def test_a_default_with_no_bondage_writes_most_of_the_debt_off(self):
        # Rome carries no debt bondage, so default ends in the settlement
        game = ruined(2.0)
        limit = game.credit_limit()
        game.default_on_debt(game.state.scenario.year)
        self.assertTrue(settled_lines(game))
        self.assertGreaterEqual(game.capital, -limit)    # inside the credit line once settled
        self.assertLess(game.capital, 0.0)               # but a part is still owed

    def test_a_settlement_never_abandons_a_persona_or_institution(self):
        game = ruined(2.0)
        game.done = set(game.done) | {"identity_cover"}
        before = set(game.done)
        game.default_on_debt(game.state.scenario.year)
        self.assertEqual(set(game.done), before)

    def test_the_settlement_freezes_credit(self):
        game = ruined(2.0)
        year = game.state.scenario.year
        game.default_on_debt(year)
        self.assertEqual(game.state.household.credit_frozen_until, year + game.SETTLEMENT_CREDIT_FREEZE_YEARS)


if __name__ == "__main__":
    unittest.main()
