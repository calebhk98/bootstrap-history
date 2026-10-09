"""A node that makes a good names the production entries it runs, and its revenue follows them.

An entry's `operated_by` lists the nodes whose concern runs it, apart from `requires_node`, which says
when anyone may. `node_output` reads both, so a maker whose technique is open to all (charcoal burning, a
mortar mix) earns from what its staff turn out rather than from a typed revenue. The census counts how
many nodes still earn a typed figure."""

QUICK_TOPIC = True

import unittest

from sim.engine import data, node_output, node_revenue_census, validate_production
from sim.labour.labour_market import production_data

CHARCOAL = {"outputs": {"charcoal_kg": 1000.0}, "inputs": {"wood_kg": 4000.0}, "labour_hours": {"labourer": 30.0},
            "requires_node": None, "operated_by": ["burner"]}
GOODS = {"charcoal_kg": 4.0, "wood_kg": 0.5}


class OperatedEntries(unittest.TestCase):

    def test_an_entry_is_found_through_the_node_that_operates_it(self):
        production = {"charcoal_kg": CHARCOAL}
        self.assertEqual(node_output.entries_gated_by("burner", production), [CHARCOAL])
        self.assertEqual(node_output.entries_gated_by("someone_else", production), [])

    def test_an_entry_gated_and_operated_by_one_node_is_listed_once(self):
        entry = dict(CHARCOAL, requires_node="burner")
        self.assertEqual(node_output.entries_gated_by("burner", {"charcoal_kg": entry}), [entry])

    def test_an_operating_node_earns_what_its_staff_turn_out(self):
        node = {"id": "burner", "sch": 0.0, "art": 1.0}
        baskets = node_output.output_baskets(node, {"charcoal_kg": CHARCOAL}, GOODS)
        self.assertIsNotNone(baskets)
        self.assertGreater(baskets.outputs["charcoal_kg"], 0.0)
        self.assertAlmostEqual(baskets.purchases["wood_kg"], 4.0 * baskets.outputs["charcoal_kg"])

    def test_an_operator_must_be_a_node_in_the_tree(self):
        problems = validate_production.check_operated_by("charcoal_kg", CHARCOAL, {"anvil"})
        self.assertEqual(len(problems), 1)
        self.assertEqual(validate_production.check_operated_by("charcoal_kg", CHARCOAL, {"burner"}), [])
        self.assertEqual(len(validate_production.check_operated_by("x", {"operated_by": "burner"}, {"burner"})), 1)


class Census(unittest.TestCase):

    def test_counts_split_nodes_with_a_typed_revenue_by_basis(self):
        nodes = {"a": {"_revenue_basis": "output"},
                 "b": {"_revenue_basis": "authored", "_src": "x.json"},
                 "c": {"_revenue_basis": "authored", "_src": "x.json", "_upkeep_basis": "authored"},
                 "d": {"_revenue_basis": None}}
        counts = node_revenue_census.basis_counts(nodes)
        self.assertEqual((counts["output"], counts["authored"], counts["knowledge"]), (1, 2, 0))
        self.assertTrue(node_revenue_census.format_lines(counts))
        self.assertEqual(node_revenue_census.typed_figures_by_file(nodes)["x.json"],
                         {"rev_hours": 2, "up_hours": 1})


class RealData(unittest.TestCase):

    def test_every_operator_named_in_the_data_exists_and_earns_from_output(self):
        _tree, _document, nodes, _wages, _goods = data.load()
        operated = {node_id for entry in production_data().values() for node_id in entry.get("operated_by") or []}
        self.assertTrue(operated)
        for node_id in sorted(operated):
            self.assertIn(node_id, nodes)
            self.assertEqual(nodes[node_id].get("_revenue_basis"), "output", node_id)


if __name__ == "__main__":
    unittest.main()
