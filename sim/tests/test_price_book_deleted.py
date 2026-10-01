"""The book price file is gone and prices in play are the solver's.

Every material a technology needs has a price from the solver under the loader's
defaults, a gated material is priced as if the technology were held (labelled
transitional), and nothing in the engine opens a price file.
"""
import os
import unittest

from sim.engine import data, prices as engine_prices

BASE_CIVS = ["rome_100ad", "han_china_100ad", "norse_900ad", "mexica_1500", "england_1300"]


class PriceBookIsGone(unittest.TestCase):

    def test_the_file_does_not_exist(self):
        self.assertFalse(os.path.exists(os.path.join(data.ROOT, "data", "prices.json")))
        self.assertFalse(hasattr(data, "PRICES"))

    def test_default_load_prices_every_required_material(self):
        _tree, _document, nodes, _wages, goods = data.load()
        required = {material for node in nodes.values() for material in (node.get("mat") or {})}
        self.assertEqual(sorted(required - set(goods)), [])
        self.assertTrue(all(price > 0.0 for material, price in goods.items()
                            if material in required), "a required material is free")

    def test_load_returns_the_wage_document_not_a_price_book(self):
        _tree, document, _nodes, wages, _goods = data.load()
        self.assertEqual(set(document["wage_rates_denarii_per_hour"]), set(wages))
        self.assertNotIn("purchase_prices_denarii", document)

    def test_goods_do_not_depend_on_a_book_table(self):
        goods, provenance = engine_prices.priced_goods_table(
            [], data.starting_schedule().document())
        self.assertGreater(len(goods), 100)
        self.assertTrue(set(provenance.values()) <= {"solved", "gated"})
        self.assertTrue(all(price > 0.0 for price in goods.values()))

    def test_gated_material_is_priced_as_if_the_technology_were_held(self):
        for civilization in BASE_CIVS:
            rate = data.starting_schedule(civilization).money_per_labour_hour
            goods = data.calculated_goods_prices([], civilization, rate)
            self.assertGreater(goods["aluminium_kg"], 0.0, civilization)
            self.assertEqual(data.goods_provenance([], civilization)["aluminium_kg"], "gated")


if __name__ == "__main__":
    unittest.main()
