"""Wear and loss of money and metal goods, and the opening money stock (sim/economy/metal_stock.py)."""
import unittest

from sim.economy import currency, metal_stock, types


class WearTests(unittest.TestCase):
    def setUp(self):
        self.coin = currency.currency_from_coin_standard(
            "x", {"material": "silver_kg", "kg_per_unit": 0.0027}, "denarius", issuer="state")
        self.fiat = currency.currency_from_coin_standard("x", {"regime": "fiat"}, "note", issuer="state")

    def test_coin_wears_to_the_wear_edge(self):
        transfers = metal_stock.yearly_wear({"a": 1000.0, "b": 0.0, types.EDGE_MINT: 50.0}, self.coin)
        self.assertEqual([t.payer for t in transfers], ["a"])
        self.assertEqual(transfers[0].payee, types.EDGE_WEAR)
        self.assertGreater(transfers[0].amount, 0.0)
        self.assertLess(transfers[0].amount, 1000.0)

    def test_fiat_does_not_wear(self):
        self.assertEqual(metal_stock.yearly_wear({"a": 1000.0}, self.fiat), [])

    def test_metal_goods_are_lost(self):
        moves = metal_stock.metal_loss({("a", "silver_plate_kg", "t1"): 10.0, ("a", "x", "t2"): 0.0})
        self.assertEqual(len(moves), 1)
        self.assertEqual((moves[0].giver, moves[0].receiver, moves[0].tile), ("a", types.EDGE_WEAR, "t1"))
        self.assertLess(moves[0].quantity, 10.0)


class OpeningStockTests(unittest.TestCase):
    def test_opening_stock_is_the_sum_of_targets(self):
        self.assertAlmostEqual(metal_stock.opening_money_stock({"a": 10.0, "b": 2.5}), 12.5)
        self.assertEqual(metal_stock.opening_money_stock({}), 0.0)


if __name__ == "__main__":
    unittest.main()
