"""Complaint 504: a node that makes the same good as an existing recipe is linked to that recipe.

The twin nodes below used to gate nothing, so opened they cost upkeep and sold nothing. Each now
operates the entry for its good, and the data derives an output-based revenue for it."""

QUICK_TOPIC = True

import unittest

from sim.engine import data, validate_unlinked_producers
from sim.production import node_output
from sim.labour.labour_market import production_data

LINKED = {"lead_metallurgy": "lead_kg", "mt2_zinc_by_retort": "zinc_kg", "pwr_coking": "carbon_kg"}


class TwinNodesEarn(unittest.TestCase):

    def setUp(self):
        _tree, _document, self.nodes, _wages, _goods = data.load()
        self.production = production_data()

    def test_each_twin_operates_the_entry_for_its_good(self):
        for node_id, good in LINKED.items():
            made = {material for entry in node_output.entries_gated_by(node_id, self.production)
                    for material in entry["outputs"]}
            self.assertIn(good, made, node_id)

    def test_each_twin_earns_from_output(self):
        for node_id in LINKED:
            node = self.nodes[node_id]
            self.assertEqual(node.get("_revenue_basis"), "output", node_id)
            self.assertGreater(node["rev"], 0.0, node_id)

    def test_the_measurement_counts_only_nodes_that_run_nothing(self):
        unlinked = {node["id"] for node in validate_unlinked_producers.unlinked_nodes(self.nodes, self.production)}
        self.assertFalse(unlinked & set(LINKED))
        for node_id in unlinked:
            self.assertFalse(node_output.entries_gated_by(node_id, self.production))


if __name__ == "__main__":
    unittest.main()
