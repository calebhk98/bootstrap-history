"""Node revenue follows what a node produces, at solved prices.

A node that gates production entries earns its yearly output (limited by the
plant's capacity and by the staff the node holds) less the inputs and energy it
buys. A node that is only knowledge earns nothing. Everything else keeps its
authored figure, labelled as such."""
import copy
import unittest

from sim.engine import data, node_output, node_revenue, node_revenue_market
from sim.world.labour_market import production_data


class NodeRevenue(unittest.TestCase):

    def setUp(self):
        _tree, _document, self.nodes, self.wages, self.goods = data.load()
        self.rate = data.starting_schedule().money_per_labour_hour

    def derived(self):
        return {node_id: node for node_id, node in self.nodes.items()
                if node.get("_revenue_basis") == "output"}

    def test_every_node_with_authored_revenue_states_its_basis(self):
        for node_id, node in self.nodes.items():
            if node["_rev_hours_authored"] > 0:
                self.assertIn(node.get("_revenue_basis"), ("output", "authored", "knowledge"), node_id)

    def test_many_material_makers_earn_from_output(self):
        self.assertGreater(len(self.derived()), 20)

    def test_output_revenue_is_output_value_less_purchases(self):
        for node_id, node in self.derived().items():
            sold = sum(quantity * self.goods[material]
                       for material, quantity in node["_output_per_year"].items())
            bought = sum(quantity * self.goods.get(material, 0.0)
                         for material, quantity in node["_purchases_per_year"].items())
            self.assertAlmostEqual(node["rev_hours"], max(0.0, sold - bought) / self.rate,
                                   delta=1e-6 * max(1.0, node["rev_hours"]), msg=node_id)

    def test_output_revenue_does_not_read_the_authored_figure(self):
        changed = copy.deepcopy(self.nodes)
        for node in changed.values():
            node["rev_hours"] = 1e9
        node_revenue.apply_revenue(changed.values(), self.goods, self.wages, self.rate)
        for node_id, node in self.derived().items():
            self.assertAlmostEqual(changed[node_id]["rev_hours"], node["rev_hours"],
                                   delta=1e-9 * max(1.0, node["rev_hours"]), msg=node_id)

    def test_output_is_held_to_plant_capacity(self):
        checked = 0
        for node_id, node in self.derived().items():
            for entry in production_data().values():
                if entry.get("requires_node") != node_id:
                    continue
                dominant = max(entry["outputs"], key=entry["outputs"].get)
                for capital in entry.get("capital") or []:
                    made = node["_output_per_year"].get(dominant)
                    if made is not None:
                        self.assertLessEqual(made, capital["annual_output_at_basis"] * (1 + 1e-9),
                                             "%s %s" % (node_id, dominant))
                        checked += 1
        self.assertGreater(checked, 0)

    def test_blast_furnace_pig_iron_is_bounded_by_its_stack(self):
        node = self.nodes["blast_furnace"]
        self.assertEqual(node["_revenue_basis"], "output")
        self.assertLessEqual(node["_output_per_year"]["pig_iron_kg"], 400000.0 * (1 + 1e-9))
        self.assertGreater(node["_output_per_year"]["pig_iron_kg"], 0.0)

    def test_declared_output_bounds_total_tonnes(self):
        for node_id, node in self.derived().items():
            declared = node.get("annual_output_t")
            if declared:
                self.assertLessEqual(sum(node["_output_per_year"].values()) / 1000.0,
                                     declared * (1 + 1e-9), node_id)

    def test_knowledge_nodes_earn_nothing(self):
        found = [node_id for node_id, node in self.nodes.items() if node.get("_revenue_basis") == "knowledge"]
        self.assertGreater(len(found), 5)
        for node_id in found:
            self.assertEqual(self.nodes[node_id]["rev_hours"], 0.0, node_id)
            self.assertEqual(self.nodes[node_id]["kind"], "SCIENCE", node_id)

    def test_authored_revenue_is_kept_and_labelled_for_services_and_equipment(self):
        kept = [n for n in self.nodes.values()
                if n.get("_revenue_basis") == "authored" and n["rev_hours"] > 0]
        self.assertGreater(len(kept), 100)

    def test_market_factor_follows_the_output_and_input_price_ratios(self):
        node = {"_output_per_year": {"a": 10.0}, "_purchases_per_year": {"b": 5.0}}
        goods = {"a": 2.0, "b": 2.0}
        # net at long-run prices: 20 - 10 = 10; at a=2x, b=1x: 40 - 10 = 30
        factor = node_revenue_market.market_factor(node, goods, {"a": 2.0}.get)
        self.assertAlmostEqual(factor, 3.0)

    def test_market_factor_is_one_for_authored_nodes_and_flat_markets(self):
        self.assertEqual(node_revenue_market.market_factor({}, {}, lambda material: 2.0), 1.0)
        node = {"_output_per_year": {"a": 10.0}, "_purchases_per_year": {}}
        self.assertEqual(node_revenue_market.market_factor(node, {"a": 1.0}, lambda material: None), 1.0)

    def test_output_baskets_return_none_without_a_physical_basis(self):
        node = {"id": "nothing_gates_this", "sch": 0, "art": 0}
        self.assertIsNone(node_output.output_baskets(node, production_data(), self.goods))


if __name__ == "__main__":
    unittest.main()
