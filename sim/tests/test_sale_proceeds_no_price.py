"""A good with no price has no sale proceeds: `sale_proceeds` answers None, never a sale of nothing, and each caller
(`quote`, `quote_sell`, the `sell` command) refuses or reports no quote. Each rule runs on a stand-in self."""
QUICK_TOPIC = True

import unittest

from sim.markets.goods_market import GoodsMarket
from sim.markets.goods_pricing import GoodsPricing
from sim.ui.proto import dispatch_money
from sim.tests.ui_stand_in import Game


class SaleProceedsTests(unittest.TestCase):
    def test_an_unpriced_good_has_no_proceeds(self):
        stand_in = Game(price_at_tile_per_tonne=lambda material: None)
        self.assertIsNone(GoodsPricing.sale_proceeds(stand_in, "cobalt", 5.0))

    def test_a_priced_good_still_pays(self):
        stand_in = Game(price_at_tile_per_tonne=lambda material: 100.0,
                                   _climb=lambda material, already, tonnes, selling=False: 0.5)
        self.assertEqual(GoodsPricing.sale_proceeds(stand_in, "iron", 4.0), (200.0, 50.0))


class CallerTests(unittest.TestCase):
    def test_quote_is_none_when_the_sale_has_no_proceeds(self):
        stand_in = Game(
            _sim=Game(_material_tag=lambda material: ("iron",),
                             economy=Game(agent_offered_tonnes=lambda material: None)),
            pricing=Game(price_at_tile_per_tonne=lambda material: 10.0, sale_proceeds=lambda *args: None,
                         carriage_per_tonne=lambda material, price: 1.0),
            posted_tonnes=lambda side, key: 0.0, acting_party_id="founder",
            import_tonnes_available=lambda material: None)
        self.assertIsNone(GoodsMarket.quote(stand_in, "iron"))

    def test_quote_sell_with_no_proceeds_sells_nothing_and_names_no_stock_key(self):
        recorded = []
        stand_in = Game(
            quote=lambda material: {"stock_key": "iron"}, posted_tonnes=lambda side, key: 0.0,
            sale_limits=lambda material: (10.0, 100.0),
            pricing=Game(sale_proceeds=lambda *args: recorded.append(args)))
        self.assertEqual(GoodsMarket.quote_sell(stand_in, "iron", 5.0), (None, 0.0, 0.0))
        self.assertEqual(len(recorded), 1)

    def test_the_sell_command_refuses_an_unpriced_good_with_a_cause(self):
        sim = Game(
            goods_quote=lambda material: None, sale_limits=lambda material: (0.0, 0.0), capital=0.0)
        reply = dispatch_money._cmd_sell(sim, {}, {"what": "material", "material": "cobalt", "n": 5}, None)
        self.assertFalse(reply["ok"])
        self.assertEqual(reply["error"].cause, "no_price")
        self.assertEqual(sim.sent, [])


if __name__ == "__main__":
    unittest.main()
