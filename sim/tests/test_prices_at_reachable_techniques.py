"""A good nothing held can make is priced through the techniques the civilisation holds, not a later route.

Complaints/302: steel plate was priced at the mature technique (cheap iron bar from a later route) while the
iron bar its own cementation works buys was priced at the civilisation's route, so the concern bought dearer
than it sold and earned nothing."""
import json
import os
import unittest

from sim.engine import data

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def starting_techs(civilization_id):
    with open(os.path.join(ROOT, "data", "civilizations", civilization_id + ".json")) as source:
        return json.load(source)["starting_techs"]


class PricesAtReachableTechniques(unittest.TestCase):

    def test_a_concern_revenue_never_prices_its_own_output_at_a_technique_the_civilisation_lacks(self):
        for civilization_id in ("rome_100ad", "england_1300"):
            held = starting_techs(civilization_id)
            self.assertNotIn("cementation_steel", held)
            _tree, _document, nodes, _wages, goods = data.load(held, civilization_id=civilization_id)
            node = nodes["cementation_steel"]
            self.assertEqual(node["_revenue_basis"], "output")
            sold = sum(quantity * goods[material] for material, quantity in node["_output_per_year"].items())
            bought = sum(quantity * goods[material] for material, quantity in node["_purchases_per_year"].items())
            self.assertGreater(sold, bought, civilization_id)
            self.assertGreater(node["rev_hours"], 0.0, civilization_id)

    def test_the_default_load_prices_steel_plate_above_the_bar_it_is_made_from(self):
        _tree, _document, _nodes, _wages, goods = data.load()
        self.assertGreater(goods["steel_plate_kg"], 1.1 * goods["iron_bar_kg"])

    def test_provenance_says_which_technique_a_price_is_at(self):
        held = starting_techs("rome_100ad")
        provenance = data.goods_provenance(held, civilization_id="rome_100ad")
        self.assertEqual(provenance["steel_plate_kg"], "gated")
        self.assertEqual(provenance["iron_bar_kg"], "solved")
        self.assertTrue(set(provenance.values()) <= {"solved", "gated", "mature"})


if __name__ == "__main__":
    unittest.main()
