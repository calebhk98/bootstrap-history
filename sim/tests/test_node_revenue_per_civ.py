"""Derived revenue and upkeep are priced for the civilisation playing, from what it can make and buy.

Complaints/310: the baskets were solved once at the reference civilisation's techniques and shared. Called on the tree
and the civilisation through `node_revenue.for_civilisation`; the Sim carrying them is in test_node_revenue_per_civ_scenario."""
import unittest

from sim.engine import data, node_revenue
from sim.engine.wage_schedule import build_schedule


def derived_for(civilization_id):
    _tree, _document, nodes, _wages, _goods = data.load(civilization_id=civilization_id)
    civ = data.load_civ(civilization_id)
    return nodes, node_revenue.for_civilisation(nodes, civ, build_schedule(data.TRADE_REGISTRY, civ))


class PerCivilisation(unittest.TestCase):

    def test_two_civilisations_do_not_share_a_derived_figure_when_their_prices_differ(self):
        _rome_nodes, rome = derived_for("rome_100ad")
        _han_nodes, han = derived_for("han_china_100ad")
        output_nodes = [node_id for node_id, node in rome.items() if node.get("_revenue_basis") == "output"]
        self.assertTrue(output_nodes)
        self.assertTrue(any(abs(rome[node_id]["rev_hours"] - han[node_id]["rev_hours"])
                            > 1e-6 * max(1.0, rome[node_id]["rev_hours"]) for node_id in output_nodes))

    def test_the_derivation_is_tagged_with_the_civilisation_it_was_made_for(self):
        _nodes, han = derived_for("han_china_100ad")
        self.assertEqual({node["_derived_for"] for node in han.values()}, {"han_china_100ad"})

    def test_the_derivation_is_cached_on_what_it_depends_on(self):
        derived_for("han_china_100ad")
        node_revenue.derivation_calls.clear()
        derived_for("han_china_100ad")
        self.assertEqual(node_revenue.derivation_calls, [], "a second derivation of the same civilisation re-derived")

    def test_a_node_the_civilisation_cannot_derive_keeps_its_authored_basis(self):
        _nodes, han = derived_for("han_china_100ad")
        for node_id, node in han.items():
            self.assertIn(node.get("_revenue_basis", "authored"), ("output", "authored", "knowledge"), node_id)

    def test_an_authored_node_earns_nothing_whatever_the_civilisation(self):
        _nodes, han = derived_for("han_china_100ad")
        for node_id, node in han.items():
            if node.get("_revenue_basis") != "output":
                self.assertEqual(node["rev_hours"], 0.0, node_id)


if __name__ == "__main__":
    unittest.main()
