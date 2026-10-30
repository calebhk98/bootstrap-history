"""VALIDATION of the shipped tree: what apply_revenue derives for the nodes that earn from output. The rules on hand-written baskets
are test_node_revenue_rules."""
import copy
import unittest

from sim.prices import energy_prices

from sim.engine import data
from sim.production import node_revenue
from sim.labour.labour_market import production_data


class NodeRevenue(unittest.TestCase):

    def setUp(self):
        _tree, self.document, self.nodes, self.wages, self.goods = data.load()
        self.rate = data.starting_schedule().money_per_labour_hour

    def derived(self):
        return {node_id: node for node_id, node in self.nodes.items()
                if node.get("_revenue_basis") == "output"}

    def test_only_output_earns(self):
        for node_id, node in self.nodes.items():
            if node.get("_revenue_basis") != "output":
                self.assertEqual(node["rev_hours"], 0.0, node_id)

    def test_many_material_makers_earn_from_output(self):
        self.assertGreater(len(self.derived()), 20)

    def test_output_revenue_does_not_read_the_authored_figure(self):
        changed = copy.deepcopy(self.nodes)
        for node in changed.values():
            node["rev_hours"] = 1e9
        energy = energy_prices.graded(data.load_civ()["starting_techs"], self.document, self.goods)
        node_revenue.apply_revenue(changed.values(), self.goods, self.wages, self.rate, energy)
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

    def test_declared_output_bounds_total_tonnes(self):
        for node_id, node in self.derived().items():
            declared = node.get("annual_output_t")
            if declared:
                self.assertLessEqual(sum(node["_output_per_year"].values()) / 1000.0,
                                     declared * (1 + 1e-9), node_id)


if __name__ == "__main__":
    unittest.main()
