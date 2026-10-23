"""VALIDATION of the shipped tree: capital is derived, never typed, and every output node is operated by the entries it runs."""
import glob
import json
import os
import unittest

from sim.engine import data, node_capital, node_revenue, validate_node_money
from sim.labour.labour_market import production_data

BRANCH_DIRECTORY = os.path.join(data.ROOT, "data", "branches")


class Validation(unittest.TestCase):

    def test_typed_revenue_is_an_error_and_the_real_tree_has_none(self):
        self.assertEqual(len(validate_node_money.check_no_typed_revenue({"x": {"_rev_hours_authored": 5.0}})), 1)
        _tree, _document, nodes, _wages, _goods = data.load()
        self.assertEqual(validate_node_money.check_node_money(nodes, production_data()), [])


class BranchDataStatesNoMoney(unittest.TestCase):

    def test_no_branch_node_types_a_capital_revenue_or_positive_upkeep(self):
        typed = []
        for path in sorted(glob.glob(os.path.join(BRANCH_DIRECTORY, "[0-9]*.json"))):
            with open(path) as handle:
                typed += [node["id"] for node in json.load(handle) if isinstance(node, dict)
                          and ("cap_hours" in node or node.get("rev_hours") or node.get("up_hours"))]
        self.assertEqual(typed, [])


class OutputNodesTypeNoFigure(unittest.TestCase):

    def test_a_node_that_earns_from_output_types_no_revenue_or_upkeep(self):
        _tree, _document, nodes, _wages, _goods = data.load()
        output = {node_id for node_id, node in nodes.items() if node.get("_revenue_basis") == "output"}
        self.assertGreater(len(output), 20)
        # a plant none of whose lines adds what its staff cost at these prices runs nothing, so its baskets are
        # empty and it earns nothing (558: charcoal_industrial, whose burner is dearer than the by-product route)
        idle = {node_id for node_id in output if not nodes[node_id]["_output_per_year"]
                and not nodes[node_id]["_energy_sold_per_year"]}
        self.assertLessEqual(idle, {"charcoal_industrial", "en_charcoal_burning"})
        for node_id in output - idle:
            self.assertGreater(nodes[node_id]["_upkeep_hours_parts"]["staff"] + nodes[node_id]["rev_hours"], 0.0, node_id)

    def test_each_output_node_is_named_as_an_operator_by_the_entries_it_runs(self):
        _tree, _document, nodes, _wages, _goods = data.load()
        operated = {name for entry in production_data().values() for name in entry.get("operated_by") or []}
        output = {node_id for node_id, node in nodes.items() if node.get("_revenue_basis") == "output"}
        self.assertEqual(sorted(output - operated), [])


class DerivedOnTheLoadedTree(unittest.TestCase):

    def setUp(self):
        _tree, _document, self.nodes, self.wages, self.goods = data.load()
        self.rate = data.starting_schedule().money_per_labour_hour

    def test_every_node_states_how_its_capital_was_found(self):
        for node_id, node in self.nodes.items():
            self.assertIn(node.get("_capital_basis"), ("derived", "authored"), node_id)
            self.assertGreaterEqual(node["cap_hours"], 0.0, node_id)

    def test_a_staffed_plant_node_carries_its_plant_and_tooling(self):
        blast = self.nodes["blast_furnace"]
        plant = blast["_upkeep_hours_parts"]["plant_build_hours"]
        self.assertGreater(plant, 0.0)
        self.assertAlmostEqual(blast["cap_hours"], node_capital.capital_hours(blast, plant),
                               delta=1e-6 * blast["cap_hours"])

    def test_capital_is_priced_in_the_coin_from_the_derived_hours(self):
        for node in self.nodes.values():
            self.assertAlmostEqual(node["cap"], node["cap_hours"] * self.rate, delta=1e-9 * (1 + node["cap"]))

    def test_the_derivation_leaves_a_stated_capital_alone(self):
        node = dict(self.nodes["blast_furnace"])
        for field in node_revenue.DERIVED_FIELDS:
            node.pop(field, None)
        node.pop("_cap_hours_authored", None)
        node["cap_hours"] = 77.0
        node_revenue.apply_revenue([node], self.goods, self.wages, self.rate)
        self.assertEqual((node["cap_hours"], node["_capital_basis"]), (77.0, "authored"))



if __name__ == "__main__":
    unittest.main()
