"""Money regimes, minting and melting, issue, money demand and the price level (sim/economy/currency.py)."""
import dataclasses
import unittest

from sim.economy import currency, types

SILVER_COIN = {"material": "silver_kg", "kg_per_unit": 0.0027, "source": "test"}


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

    def test_explicit_regime_in_data_wins(self):
        spec = currency.currency_from_coin_standard(
            "x", {"material": "silver_kg", "kg_per_unit": 0.025, "regime": "weighed_metal"}, "eyrir")
        self.assertEqual(spec.regime, "weighed_metal")
        self.assertIsNone(spec.issuer)

    def test_non_metal_is_commodity_money(self):
        spec = currency.currency_from_coin_standard(
            "x", {"material": "cotton_fabric_kg", "kg_per_unit": 0.4}, "quachtli")
        self.assertEqual(spec.regime, "commodity")

    def test_fiat_when_data_says_or_no_backing(self):
        self.assertEqual(fiat_spec().regime, "fiat")
        spec = currency.currency_from_coin_standard("x", {}, "note")
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


class ArbitrageTests(unittest.TestCase):
    def test_cheap_bullion_goes_to_the_mint_and_seigniorage_to_issuer(self):
        spec = silver_spec(charge=0.1)
        transfers, moves = currency.arbitrage(spec, 0.5 * currency.mint_price(spec), {"a": 100.0}, {})
        self.assertTrue(moves and all(m.receiver == types.EDGE_MINT for m in moves))
        metal = sum(m.quantity for m in moves)
        paid = sum(t.amount for t in transfers if t.payee == "a")
        keep = sum(t.amount for t in transfers if t.payee == "state")
        self.assertAlmostEqual(paid, metal * 0.9 / 0.0027)
        self.assertAlmostEqual(keep, metal * 0.1 / 0.0027)
        self.assertTrue(all(t.payer == types.EDGE_MINT for t in transfers))

    def test_dear_bullion_melts_coin(self):
        spec = silver_spec()
        transfers, moves = currency.arbitrage(spec, 2 * currency.mint_parity(spec), {}, {"a": 1000.0})
        self.assertTrue(all(t.payee == types.EDGE_MINT and t.payer == "a" for t in transfers))
        coin = sum(t.amount for t in transfers)
        self.assertAlmostEqual(sum(m.quantity for m in moves), coin * 0.0027)
        self.assertTrue(all(m.giver == types.EDGE_MINT for m in moves))

    def test_inside_the_band_nothing_moves(self):
        spec = silver_spec(charge=0.1)
        price = 0.5 * (currency.mint_price(spec) + currency.mint_parity(spec))
        self.assertEqual(currency.arbitrage(spec, price, {"a": 5.0}, {"a": 5.0}), ([], []))

    def test_fiat_does_not_arbitrage(self):
        self.assertEqual(currency.arbitrage(fiat_spec(), 1.0, {"a": 5.0}, {"a": 5.0}), ([], []))

    def test_bullion_price_converges_to_parity_in_a_toy_loop(self):
        spec = silver_spec()
        parity = currency.mint_parity(spec)
        for start in (0.4 * parity, 2.5 * parity):
            metal, coin = 1000.0, 3000.0 / 0.0027
            # bullion's price in coin: the value of metal wanted for use, spread over the metal held
            demand_value = start * metal
            price = start
            for _ in range(80):
                transfers, moves = currency.arbitrage(spec, price, {"a": metal}, {"a": coin})
                for move in moves:
                    metal += -move.quantity if move.receiver == types.EDGE_MINT else move.quantity
                for transfer in transfers:
                    coin += transfer.amount if transfer.payee == "a" else -transfer.amount
                price = demand_value / metal
            self.assertLess(abs(price - parity) / parity, 0.05, (start, price, parity))


class MoneyDemandTests(unittest.TestCase):
    def test_target_falls_with_interest_and_inflation(self):
        base = currency.cash_balance_target(100.0, 0.0, 0.0)
        self.assertGreater(base, currency.cash_balance_target(100.0, 0.1, 0.0))
        self.assertGreater(currency.cash_balance_target(100.0, 0.1, 0.0),
                           currency.cash_balance_target(100.0, 0.1, 0.5))

    def test_hyperinflation_expectations_shrink_but_keep_positive(self):
        low = currency.cash_balance_target(100.0, 0.0, 0.05)
        high = currency.cash_balance_target(100.0, 0.0, 2.0)
        self.assertGreater(high, 0.0)
        self.assertLess(high, 0.2 * low)

    def test_expectations_adapt(self):
        value = 0.0
        for _ in range(20):
            value = currency.update_expected_inflation(value, 0.5)
        self.assertAlmostEqual(value, 0.5, places=3)
        self.assertLess(currency.update_expected_inflation(0.0, 0.5), 0.5)

    def test_spending_adjustment_signs(self):
        self.assertGreater(currency.spending_adjustment(120.0, 100.0, 500.0), 0.0)
        self.assertLess(currency.spending_adjustment(80.0, 100.0, 500.0), 0.0)
        self.assertEqual(currency.spending_adjustment(100.0, 100.0, 500.0), 0.0)
        self.assertGreaterEqual(currency.spending_adjustment(0.0, 1e9, 10.0), -10.0)


def quantity_loop(printing_share_by_year):
    """Toy economy: fixed output; each year spending is last year's nominal income plus the pull of cash
    above target; the price level is spending over goods; the issuer prints a share of the stock."""
    goods = 100.0
    cash, expected, level = currency.cash_balance_target(goods, 0.02, 0.0), 0.0, 1.0
    levels = [level]
    for printing in printing_share_by_year:
        cash += printing * cash
        spending = goods * level
        target = currency.cash_balance_target(spending, 0.02, expected)
        spending += currency.spending_adjustment(cash, target, spending)
        new_level = spending / goods
        expected = currency.update_expected_inflation(expected, new_level / level - 1)
        level = new_level
        levels.append(level)
    return levels


class QuantityLoopTests(unittest.TestCase):
    def test_no_printing_keeps_the_level_stable(self):
        levels = quantity_loop([0.0] * 30)
        self.assertLess(max(levels) / min(levels), 1.5)

    def test_rising_printing_accelerates_inflation(self):
        levels = quantity_loop([0.05 * (1.35 ** year) for year in range(14)])
        rises = [levels[i + 1] / levels[i] - 1 for i in range(len(levels) - 1)]
        self.assertGreater(rises[-1], rises[len(rises) // 2])
        self.assertGreater(rises[len(rises) // 2], rises[2])
        self.assertGreater(rises[-1], 1.0)          # beyond 100 percent a year: hyperinflation reached


class PriceLevelAndRateTests(unittest.TestCase):
    def test_fixed_basket(self):
        self.assertAlmostEqual(
            currency.price_level({"a": 2.0, "b": 3.0}, {"a": 1.0, "b": 3.0}, {"a": 1.0, "b": 1.0}), 5 / 4)

    def test_skips_missing_goods_and_empty_base(self):
        self.assertAlmostEqual(
            currency.price_level({"a": 2.0}, {"a": 1.0, "b": 1.0}, {"a": 1.0, "b": 1.0}), 2.0)
        self.assertEqual(currency.price_level({"a": 2.0}, {}, {}), 1.0)

    def test_exchange_rate_at_metal_parity(self):
        penny = currency.currency_from_coin_standard(
            "e", {"material": "silver_kg", "kg_per_unit": 0.00135}, "penny", issuer="king")
        self.assertAlmostEqual(currency.exchange_rate(silver_spec(), penny, {"silver_kg": 10.0}), 2.0)

    def test_exchange_rate_none_for_fiat(self):
        self.assertIsNone(currency.exchange_rate(fiat_spec(), silver_spec(), {"silver_kg": 10.0}))


if __name__ == "__main__":
    unittest.main()
