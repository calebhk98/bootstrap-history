"""Complaints/577: a concern's quoted earnings and its takings once open read one set of arithmetic, at the same prices
(sim/engine/concern_earnings.py), called here on built numbers. (That the screens, `revenue` and the ledger call it:
test_scenarios_batch3.)"""
QUICK_TOPIC = True

import unittest

from sim.agents.api import business_books
from sim.engine import concern_earnings as earnings

takings_of_size = business_books.takings_of_size

TREE_REVENUE = 1000.0
PRICE_INDEX = 1.7
VALUE_RATIO = 1.2
LEARNING_RATIO = 0.9


def takings(ramp=1.0, output_factor=1.0):
    return earnings.takings_at(TREE_REVENUE, ramp, output_factor, PRICE_INDEX, VALUE_RATIO, LEARNING_RATIO)


class TakingsTests(unittest.TestCase):
    def test_takings_carry_the_trees_figure_to_the_price_level_and_held_techniques(self):
        self.assertAlmostEqual(takings(), TREE_REVENUE * PRICE_INDEX * VALUE_RATIO * LEARNING_RATIO)

    def test_takings_follow_the_ramp_and_the_output_factor_linearly(self):
        self.assertAlmostEqual(takings(ramp=0.5), 0.5 * takings())
        self.assertAlmostEqual(takings(output_factor=0.9), 0.9 * takings())

    def test_leaving_out_the_output_factor_is_an_output_factor_of_one(self):
        self.assertAlmostEqual(takings(output_factor=1.0), takings())


class QuotedRampTests(unittest.TestCase):
    def test_a_concern_not_yet_open_is_quoted_at_its_full_ramp_without_asking_for_a_ramp(self):
        self.assertEqual(earnings.quoted_ramp(False, False, lambda: self.fail("a closed concern has no ramp")), 1.0)

    def test_an_open_concern_is_quoted_at_its_own_ramp(self):
        self.assertEqual(earnings.quoted_ramp(True, False, lambda: 0.4), 0.4)

    def test_a_fully_ramped_quote_does_not_move_with_the_ramp(self):
        first = earnings.quoted_ramp(True, True, lambda: 0.2)
        second = earnings.quoted_ramp(True, True, lambda: 0.9)
        self.assertEqual((first, second), (1.0, 1.0))
        self.assertAlmostEqual(takings(ramp=first), takings(ramp=second))


class QuotedUnitsTests(unittest.TestCase):
    def test_units_asked_for_win(self):
        self.assertEqual(earnings.quoted_units(True, True, lambda: 3.0, 5.0), 5.0)

    def test_an_open_scalable_concern_is_quoted_at_the_units_it_runs(self):
        self.assertEqual(earnings.quoted_units(True, True, lambda: 3.0), 3.0)

    def test_any_other_concern_is_quoted_at_one_unit(self):
        self.assertEqual(earnings.quoted_units(False, True, lambda: self.fail("not running")), 1.0)
        self.assertEqual(earnings.quoted_units(True, False, lambda: self.fail("not scalable")), 1.0)


class RealEarningsTests(unittest.TestCase):
    def test_the_goods_markets_price_multiplies_the_takings(self):
        self.assertAlmostEqual(takings_of_size(takings(), 1.0, 0.8), 0.8 * takings())

    def test_a_quote_before_opening_applies_the_market_factor_to_the_full_ramp_takings(self):
        quote = takings_of_size(takings(ramp=earnings.quoted_ramp(False, False, lambda: 0.3)), 1.0, 0.8)
        self.assertAlmostEqual(quote, takings(ramp=1.0) * 0.8)

    def test_units_scale_the_earnings(self):
        self.assertAlmostEqual(takings_of_size(takings(), 4.0, 0.8), 4.0 * 0.8 * takings())

    def test_earnings_with_the_output_factor_are_the_earnings_without_it_times_the_factor(self):
        market = 0.85
        with_factor = takings_of_size(takings(output_factor=0.9), 2.0, market)
        without = takings_of_size(takings(output_factor=1.0), 2.0, market)
        self.assertAlmostEqual(with_factor, without * 0.9)


class LedgerRowTests(unittest.TestCase):
    def test_a_row_is_the_earnings_to_a_tenth(self):
        self.assertEqual(earnings.ledger_row(123.456), 123.5)

    def test_a_concern_earning_half_a_coin_or_less_is_not_listed(self):
        self.assertIsNone(earnings.ledger_row(0.5))
        self.assertIsNone(earnings.ledger_row(0.0))
        self.assertIsNone(earnings.ledger_row(-12.0))

    def test_a_row_is_within_a_twentieth_of_the_figure_the_screens_quote(self):
        quote = takings_of_size(takings(), 1.0, 0.77)
        self.assertLess(abs(earnings.ledger_row(quote) - quote), 0.051)


if __name__ == "__main__":
    unittest.main()
