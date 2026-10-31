"""Money regimes, minting and melting, issue, money demand and the price level (sim/economy/currency.py)."""

QUICK_TOPIC = True

import dataclasses
import unittest

from sim.economy import currency, types

SILVER_COIN = {"regime": "struck_coin", "material": "silver_kg", "kg_per_unit": 0.0027, "source": "test"}


def silver_spec(charge=0.0):
    spec = currency.currency_from_coin_standard("realm", SILVER_COIN, "denarius", issuer="state")
    return dataclasses.replace(spec, mint_charge_share=charge)


def fiat_spec():
    return currency.currency_from_coin_standard("x", {"regime": "fiat"}, "note", issuer="state")


class RegimeTests(unittest.TestCase):
    def test_struck_silver_coin(self):
        spec = silver_spec()
        self.assertEqual(spec.regime, "struck_coin")
        self.assertEqual(spec.backing_good, "silver_kg")
        self.assertAlmostEqual(spec.backing_per_unit, 0.0027)
        self.assertEqual(spec.currency_id, "denarius")

    def test_weighed_metal_has_no_issuer_and_no_mint(self):
        spec = currency.currency_from_coin_standard(
            "x", {"material": "silver_kg", "kg_per_unit": 0.025, "regime": "weighed_metal"}, "eyrir")
        self.assertEqual(spec.regime, "weighed_metal")
        self.assertIsNone(spec.issuer)
        self.assertFalse(currency.has_mint(spec))

    def test_commodity_money_is_the_good_itself(self):
        spec = currency.currency_from_coin_standard(
            "x", {"material": "cacao_kg", "kg_per_unit": 0.001, "regime": "commodity"}, "bean", issuer="state")
        self.assertEqual((spec.regime, spec.backing_good, spec.issuer), ("commodity", "cacao_kg", None))

    def test_data_must_name_a_regime(self):
        with self.assertRaises(ValueError):
            currency.currency_from_coin_standard("x", {"material": "silver_kg", "kg_per_unit": 0.01}, "coin")

    def test_only_a_struck_coin_has_a_mint_charge(self):
        data = {"material": "silver_kg", "kg_per_unit": 0.01, "mint_charge_share": 0.02}
        spec = currency.currency_from_coin_standard("x", dict(data, regime="struck_coin"), "coin", issuer="state")
        self.assertEqual(spec.mint_charge_share, 0.02)
        with self.assertRaises(ValueError):
            currency.currency_from_coin_standard("x", dict(data, regime="weighed_metal"), "coin")

    def test_fiat_needs_no_backing(self):
        self.assertEqual(fiat_spec().regime, "fiat")
        spec = currency.currency_from_coin_standard("x", {"regime": "fiat"}, "note")
        self.assertEqual((spec.regime, spec.backing_good, spec.backing_per_unit), ("fiat", None, 0.0))


class ParityTests(unittest.TestCase):
    def test_parity_is_inverse_of_backing(self):
        self.assertAlmostEqual(currency.mint_parity(silver_spec()), 1 / 0.0027)

    def test_mint_charge_lowers_what_the_mint_pays(self):
        spec = silver_spec(charge=0.1)
        self.assertAlmostEqual(currency.mint_price(spec), 0.9 * currency.mint_parity(spec))

    def test_debasement_lowers_metal_per_coin_and_raises_bullion_parity(self):
        spec = silver_spec()
        worse = currency.debase(spec, spec.backing_per_unit * 0.5)
        self.assertLess(worse.backing_per_unit, spec.backing_per_unit)
        self.assertGreater(currency.mint_parity(worse), currency.mint_parity(spec))

    def test_fiat_cannot_be_debased(self):
        with self.assertRaises(ValueError):
            currency.debase(fiat_spec(), 0.1)


class IssueTests(unittest.TestCase):
    def test_issue_and_retire(self):
        [made] = currency.issue(fiat_spec(), 50.0, "deficit")
        self.assertEqual((made.payer, made.payee, made.amount), (types.EDGE_ISSUE, "state", 50.0))
        [gone] = currency.retire(fiat_spec(), 20.0, "tax")
        self.assertEqual((gone.payer, gone.payee, gone.amount), ("state", types.EDGE_ISSUE, 20.0))

    def test_no_issuer_cannot_issue(self):
        spec = currency.currency_from_coin_standard(
            "x", {"material": "silver_kg", "kg_per_unit": 0.025, "regime": "weighed_metal"}, "eyrir")
        with self.assertRaises(ValueError):
            currency.issue(spec, 1.0, "x")


class MoneyDemandTests(unittest.TestCase):
    def test_expectations_adapt(self):
        value = 0.0
        for _ in range(20):
            value = currency.update_expected_inflation(value, 0.5)
        self.assertAlmostEqual(value, 0.5, places=3)
        self.assertLess(currency.update_expected_inflation(0.0, 0.5), 0.5)


class PriceLevelAndRateTests(unittest.TestCase):
    def test_fixed_basket(self):
        self.assertAlmostEqual(
            currency.basket_price_level({"a": 2.0, "b": 3.0}, {"a": 1.0, "b": 3.0}, {"a": 1.0, "b": 1.0}), 5 / 4)

    def test_skips_missing_goods_and_empty_base(self):
        self.assertAlmostEqual(
            currency.basket_price_level({"a": 2.0}, {"a": 1.0, "b": 1.0}, {"a": 1.0, "b": 1.0}), 2.0)
        self.assertEqual(currency.basket_price_level({"a": 2.0}, {}, {}), 1.0)

    def test_exchange_rate_at_metal_parity(self):
        penny = currency.currency_from_coin_standard(
            "e", {"regime": "struck_coin", "material": "silver_kg", "kg_per_unit": 0.00135}, "penny", issuer="king")
        self.assertAlmostEqual(currency.exchange_rate(silver_spec(), penny, {"silver_kg": 10.0}), 2.0)

    def test_exchange_rate_none_for_fiat(self):
        self.assertIsNone(currency.exchange_rate(fiat_spec(), silver_spec(), {"silver_kg": 10.0}))


if __name__ == "__main__":
    unittest.main()
