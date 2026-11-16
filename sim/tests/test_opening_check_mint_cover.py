"""Complaint 473 (owner question 4), Complaint 519: the coin-metal check of a money paid in metal at a stated price
(`opening_checks.mint_price_over_cost`). The mint's price must cover what the metal costs to make; how far above cost it
stands is the makers' rent and is not bounded."""

QUICK_TOPIC = True

import unittest

from sim.engine import opening_checks

NAME = "price_over_cost_coin_metal"


class MintPriceCoversTheMakingCost(unittest.TestCase):
    def test_a_mint_price_above_the_making_cost_passes_and_reports_the_cover(self):
        result = opening_checks.mint_price_over_cost(NAME, 10.0, 4.0)
        self.assertTrue(result.passed)
        self.assertAlmostEqual(result.value, 2.5)
        self.assertEqual((result.bound, result.bound_kind), (opening_checks.MINT_COVER_LOWEST, "at least"))

    def test_a_mint_price_below_the_making_cost_fails(self):
        result = opening_checks.mint_price_over_cost(NAME, 3.0, 4.0)
        self.assertFalse(result.passed)
        self.assertAlmostEqual(result.value, 0.75)

    def test_a_mint_price_many_times_the_making_cost_still_passes(self):
        self.assertTrue(opening_checks.mint_price_over_cost(NAME, 4000.0, 4.0).passed)

    def test_no_making_cost_is_no_value_and_fails_with_its_cause(self):
        for cost in (None, 0.0):
            result = opening_checks.mint_price_over_cost(NAME, 10.0, cost)
            self.assertIsNone(result.value)
            self.assertFalse(result.passed)
            self.assertEqual(result.detail["cause"], "no_making_cost")

    def test_no_mint_price_is_no_value_and_fails_with_its_cause(self):
        result = opening_checks.mint_price_over_cost(NAME, None, 4.0)
        self.assertIsNone(result.value)
        self.assertFalse(result.passed)
        self.assertEqual(result.detail["cause"], "no_mint_price")

    def test_the_market_price_over_cost_is_kept_in_the_detail_and_decides_nothing(self):
        result = opening_checks.mint_price_over_cost(NAME, 10.0, 4.0, market_ratio=40.0, unmeasured={"silver_kg": "price_not_a_trade"})
        self.assertTrue(result.passed)
        self.assertEqual(result.detail["market_price_over_cost"], 40.0)
        self.assertEqual(result.detail["unmeasured"], {"silver_kg": "price_not_a_trade"})


class TheCoinMetalCheckFollowsTheRegime(unittest.TestCase):
    def test_a_money_paid_in_metal_is_held_to_the_mint_cover(self):
        group = {"ratios": {"silver_kg": 30.0}, "unmeasured": {}}
        result = opening_checks.coin_metal_check(NAME, group, paid_price=12.0, making_cost=4.0)
        self.assertTrue(result.passed)
        self.assertEqual(result.bound_kind, "at least")
        self.assertAlmostEqual(result.value, 3.0)

    def test_a_money_with_no_stated_metal_price_keeps_the_band(self):
        group = {"ratios": {"cacao_kg": 30.0}, "unmeasured": {}}
        result = opening_checks.coin_metal_check(NAME, group, paid_price=None, making_cost=4.0)
        self.assertFalse(result.passed)
        self.assertEqual(result.bound_kind, "within")


if __name__ == "__main__":
    unittest.main()
