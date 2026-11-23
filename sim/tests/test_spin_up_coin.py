"""Coin wear and the hidden spin-up: the search rules wear coin at its declared share in every year, the clearing rules
let it wear in a hidden year only as far as the mint struck coin that year."""

QUICK_TOPIC = True

import unittest

from sim.economy import rule_sets, spin_up_coin


class AsDeclared(unittest.TestCase):
    def test_the_declared_share_in_a_hidden_year_too(self):
        self.assertEqual(spin_up_coin.as_declared(0.01, True, 1000.0, 2.0), 0.01)


class NoMoreThanStruckWhileSettling(unittest.TestCase):
    def test_a_year_of_play_wears_the_declared_share(self):
        self.assertEqual(spin_up_coin.no_more_than_struck_while_settling(0.01, False, 1000.0, 2.0), 0.01)

    def test_a_hidden_year_wears_what_the_mint_struck_over_the_stock(self):
        self.assertAlmostEqual(spin_up_coin.no_more_than_struck_while_settling(0.01, True, 1000.0, 4.0), 0.004)

    def test_a_mint_that_struck_more_than_the_declared_wear_leaves_the_declared_share(self):
        self.assertEqual(spin_up_coin.no_more_than_struck_while_settling(0.01, True, 1000.0, 25.0), 0.01)

    def test_a_mint_that_struck_nothing_or_melted_coin_wears_none(self):
        self.assertEqual(spin_up_coin.no_more_than_struck_while_settling(0.01, True, 1000.0, 0.0), 0.0)
        self.assertEqual(spin_up_coin.no_more_than_struck_while_settling(0.01, True, 1000.0, -3.0), 0.0)

    def test_no_coin_at_all_keeps_the_declared_share(self):
        self.assertEqual(spin_up_coin.no_more_than_struck_while_settling(0.01, True, 0.0, 4.0), 0.01)


class Rules(unittest.TestCase):
    def test_which_rule_each_set_runs(self):
        self.assertIs(rule_sets.RULE_SETS["search"].spin_up_coin_wear, spin_up_coin.as_declared)
        self.assertIs(rule_sets.RULE_SETS["clearing"].spin_up_coin_wear, spin_up_coin.no_more_than_struck_while_settling)


if __name__ == "__main__":
    unittest.main()
