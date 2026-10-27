"""A good with no price has no sale proceeds: `sale_proceeds` answers None, never a sale of nothing, and each caller
(`quote`, `quote_sell`, the `sell` command) refuses or reports no quote. Each rule runs on a stand-in self."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

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
            price_at_tile_per_tonne=lambda material: 10.0, sale_proceeds=lambda *args: None,
            sold_tonnes=lambda key, party: 0.0, acting_party_id="founder",
            import_tonnes_available=lambda material: None, _carriage_per_tonne=lambda material, price: 1.0)
        self.assertIsNone(GoodsMarket.quote(stand_in, "iron"))

    def test_quote_sell_with_no_proceeds_sells_nothing_and_names_no_stock_key(self):
        recorded = []
        stand_in = Game(
            quote=lambda material: {"stock_key": "iron"}, sold_tonnes=lambda key, party: 0.0,
            _with_buyers=lambda material, quote: {**quote, "market_available_tonnes_per_year": 100.0},
            sale_room_tonnes=lambda quote, sold: 100.0,
            sale_proceeds=lambda *args: recorded.append(args),
            acting=Game(party_id="founder", held=lambda key: 10.0))
        self.assertEqual(GoodsMarket.quote_sell(stand_in, "iron", 5.0), (None, 0.0, 0.0))
        self.assertEqual(len(recorded), 1)

    def test_the_sell_command_refuses_an_unpriced_good_with_a_cause(self):
        sold = []
        sim = Game(
            goods_market=Game(quote=lambda material: None,
                                         sale_limits=lambda material: (0.0, 0.0)),
            sell_material_stock=lambda material, quantity: sold.append((material, quantity)) or quantity,
            capital=0.0)
        reply = dispatch_money._cmd_sell(sim, {}, {"what": "material", "material": "cobalt", "n": 5}, None)
        self.assertFalse(reply["ok"])
        self.assertEqual(reply["error"].cause, "no_price")
        self.assertEqual(sold, [])


if __name__ == "__main__":
    unittest.main()
