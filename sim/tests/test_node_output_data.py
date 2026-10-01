"""A node that makes a material states what bounds its yearly output, and why.

`node_output` derives a node's revenue from the plant its entries state, the
staff it holds, or a declared `annual_output_t`. These rules keep that data
honest: a declaration names a product (it gates an entry) and carries its
basis, and a gated node that makes something is bounded by one of the three
rather than falling back to an authored revenue figure."""
import unittest

from sim.engine import data, node_output
from sim.world.labour_market import production_data

# Gated nodes whose lines the three bounds cannot yet reach: extraction (a deposit or a parent
# stream sets the output), lines whose basis unit is not a kilogram (the declared figure is in
# tonnes), and lines that split one declared total across unrelated products. Complaints/520.
STILL_UNBOUNDED = {
    "analytical_chemistry", "electrolysis_industrial", "in2_claude_cycle_air_liquefaction",
    "in2_linde_cycle_expansion_engine", "in2_ultracentrifuge", "med_opium_mandrake",
    "met_froth_flotation", "pwr_coal_seam", "pwr_nuclear_fission", "pwr_peat",
}


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

    def test_a_gated_maker_is_bounded_by_plant_staff_or_declaration(self):
        unbounded = set()
        for node_id, node in self.nodes.items():
            if node.get("_rev_hours_authored", 0.0) > 0 and node.get("_revenue_basis") == "authored" \
                    and node_output.entries_gated_by(node_id, self.production):
                unbounded.add(node_id)
        self.assertLessEqual(unbounded, STILL_UNBOUNDED, "newly unbounded: %s" % sorted(unbounded - STILL_UNBOUNDED))
        self.assertFalse(STILL_UNBOUNDED - unbounded, "now bounded, remove from STILL_UNBOUNDED: %s"
                         % sorted(STILL_UNBOUNDED - unbounded))


if __name__ == "__main__":
    unittest.main()
