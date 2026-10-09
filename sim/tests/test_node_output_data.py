"""A node that makes a material states what bounds its yearly output, and why.

`node_output` derives a node's revenue from the plant its entries state, the
staff it holds, or a declared `annual_output_t`. These rules keep that data
honest: a declaration names a product (it gates an entry) and carries its
basis, and a gated node that makes something is bounded by one of the three
rather than falling back to an authored revenue figure."""

QUICK_TOPIC = True

import unittest

from sim.engine import data, node_output, validate_node_money
from sim.labour.labour_market import production_data

class NodeOutputData(unittest.TestCase):

    def setUp(self):
        _tree, _document, self.nodes, _wages, _goods = data.load()
        self.production = production_data()

    def test_a_declared_output_states_its_basis(self):
        for node_id, node in self.nodes.items():
            if node.get("annual_output_t"):
                basis = node.get("annual_output_basis") or ""
                self.assertGreaterEqual(len(basis), 50, "%s declares annual_output_t without a basis" % node_id)

    def test_a_declared_output_names_a_product(self):
        for node_id, node in self.nodes.items():
            if node.get("annual_output_t"):
                self.assertTrue(node_output.entries_gated_by(node_id, self.production),
                                "%s declares annual_output_t but gates no production entry" % node_id)

    def test_the_real_data_states_a_bound_for_every_operated_maker(self):
        self.assertEqual(validate_node_money.check_node_money(self.nodes, self.production), [])


if __name__ == "__main__":
    unittest.main()
