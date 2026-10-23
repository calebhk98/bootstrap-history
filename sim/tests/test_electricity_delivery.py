"""Electricity is generated at a busbar and delivered at a meter, and the line between costs something.

Generators make `electricity_generated_mj`; a delivery entry turns it into `electrical_mj` (energy at the
customer's meter, the carrier every consumer draws) with the loss a conductor's resistance sets and the
line plant it runs in. The tests assert relationships, never a dated price. The entries' data and physics are test_electricity_delivery_data."""
import copy
import unittest

from sim.engine import data, node_output, prices as price_solver
from sim.labour.labour_market import production_data

TWO_WIRE = "electrical_mj_main_two_wire"
THREE_WIRE = "electrical_mj_main_three_wire"
DELIVERY_KEYS = (TWO_WIRE, THREE_WIRE)


class Delivery(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        _tree, cls.document, _nodes, _wages, _goods = data.load()
        cls.production = production_data()

    def solve(self, entries, held=None):
        held = price_solver.all_gate_nodes(entries) if held is None else held
        goods, _provenance = price_solver.priced_goods_table(held, self.document, production_entries=entries)
        return goods

    def modified(self, change):
        entries = copy.deepcopy(self.production)
        change(entries)
        return entries

    def held_without(self, entries, node_id):
        return price_solver.all_gate_nodes(entries) - {node_id}

    def test_delivered_energy_costs_more_than_generated_by_the_loss_and_the_plant(self):
        goods = self.solve(self.production)
        generated, delivered = goods["electricity_generated_mj"], goods["electrical_mj"]
        lossiest_floor = min(generated * self.production[key]["inputs"]["electricity_generated_mj"]
                             / self.production[key]["outputs"]["electrical_mj"] for key in DELIVERY_KEYS)
        self.assertGreater(delivered, lossiest_floor)

    def test_delivered_price_rises_with_the_loss(self):
        base = self.solve(self.production)["electrical_mj"]

        def longer(entries):
            entries[TWO_WIRE]["inputs"]["electricity_generated_mj"] *= 1.5
            entries[THREE_WIRE]["inputs"]["electricity_generated_mj"] *= 1.5
        self.assertGreater(self.solve(self.modified(longer))["electrical_mj"], base)

    def test_holding_the_three_wire_node_lowers_the_delivered_price(self):
        entries = self.production
        held = price_solver.all_gate_nodes(entries)
        node_id = entries[THREE_WIRE]["requires_node"]
        with_node = self.solve(entries, held)["electrical_mj"]
        without = self.solve(entries, held - {node_id})["electrical_mj"]
        self.assertLess(with_node, without)

    def test_raising_the_generator_price_raises_a_consumer_by_its_electrical_share(self):
        base = self.solve(self.production)

        def dearer(entries):
            entries["electrical_mj_dynamo"]["labour_hours"]["electrician"] *= 1000.0
            entries["electrical_mj_photovoltaic"]["capital"][0]["annual_output_at_basis"] /= 1000.0
        dear = self.solve(self.modified(dearer))
        self.assertGreater(dear["electrical_mj"], base["electrical_mj"])
        self.assertGreater(dear["aluminium_kg"], base["aluminium_kg"])
        electrical_share = base["electrical_mj"] * self.production["aluminium_kg"]["electrical_mj"] / base["aluminium_kg"]
        self.assertLess(dear["aluminium_kg"] / base["aluminium_kg"], 1.0 + electrical_share * (
            dear["electrical_mj"] / base["electrical_mj"] - 1.0) + 1e-9)

    def test_the_three_wire_node_gates_the_three_wire_entry_and_earns_through_it(self):
        node_id = self.production[THREE_WIRE]["requires_node"]
        self.assertEqual(node_id, "el2_three_wire_distribution_system")
        self.assertIn(self.production[THREE_WIRE], node_output.entries_gated_by(node_id, self.production))
        _tree, _document, nodes, _wages, _goods = data.load()
        self.assertEqual(nodes[node_id]["_revenue_basis"], "output")


if __name__ == "__main__":
    unittest.main()
