"""Complaint 640: the rules behind the old whole-game insolvency checks, each called on a built game. The default
rule (`default_on_debt`) and the write-off (`settle_insolvency`) are Sim methods that read only the household's purse,
the credit limit and the civilisation, so an unopened game (no hidden years) holds them."""

import unittest

from .harness import *  # noqa: F401,F403


def ruined(depth_in_limits):
    game = unopened_sim(civ="rome_100ad", capital=1000000.0)
    game.capital = -depth_in_limits * game.credit_limit()
    return game


def settled_lines(game):
    return [line for _year, line in game.state.household.log if getattr(line, "kind", "") == "insolvency_settled"]


class DefaultOnDebt(unittest.TestCase):
    def test_a_default_with_no_bondage_writes_most_of_the_debt_off(self):
        # Rome carries no debt bondage, so default ends in the settlement
        game = ruined(2.0)
        limit = game.credit_limit()
        game.default_on_debt(game.state.scenario.year)
        self.assertTrue(settled_lines(game))
        self.assertGreaterEqual(game.capital, -limit)    # inside the credit line once settled
        self.assertLess(game.capital, 0.0)               # but a part is still owed

    def test_the_settlement_leaves_a_share_of_the_marked_down_line_owed(self):
        # the balance left is measured against the line that stands once the name has been marked down
        game = ruined(3.0)
        household = game.state.household
        reputation = household.reputation
        household.reputation = max(0.0, reputation - game.SETTLEMENT_REPUTATION_HIT)
        marked_down_line = game.credit_limit()
        household.reputation = reputation
        game.settle_insolvency(game.state.scenario.year, game.credit_limit())
        self.assertAlmostEqual(game.capital, -marked_down_line * game.SETTLEMENT_CAPITAL_RETAINED_FRACTION,
                               delta=0.02 * marked_down_line)

    def test_a_settlement_never_abandons_a_persona_or_institution(self):
        game = ruined(2.0)
        game.done = set(game.done) | {"identity_cover"}
        before = set(game.done)
        game.default_on_debt(game.state.scenario.year)
        self.assertEqual(set(game.done), before)

    def test_a_default_inside_the_line_does_nothing(self):
        game = ruined(0.5)
        before = game.capital
        game.default_on_debt(game.state.scenario.year)
        self.assertEqual(game.capital, before)
        self.assertFalse(settled_lines(game))

    def test_the_settlement_freezes_credit(self):
        game = ruined(2.0)
        year = game.state.scenario.year
        game.default_on_debt(year)
        self.assertEqual(game.state.household.credit_frozen_until, year + game.SETTLEMENT_CREDIT_FREEZE_YEARS)


if __name__ == "__main__":
    unittest.main()
