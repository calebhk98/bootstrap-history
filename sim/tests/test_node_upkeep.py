"""A node that makes something pays for what it takes to keep making it: its staff and its plant.

Upkeep follows the same entries as revenue: the hours the lines work, at the civilisation's wages
for each trade, plus a share of what the node cost to build (labelled by kind of node). Inputs are
netted in revenue, so they are not charged again here. Nodes with no physical output keep their
authored upkeep, labelled."""
import copy
import unittest

from sim.engine import data, energy_prices, node_revenue, node_upkeep
from sim.labour.labour_market import production_data


class NodeUpkeep(unittest.TestCase):

    def setUp(self):
        _tree, self.document, self.nodes, self.wages, self.goods = data.load()
        self.rate = data.starting_schedule().money_per_labour_hour

    def derived(self):
        return {node_id: node for node_id, node in self.nodes.items()
                if node.get("_upkeep_basis") == "derived"}

    def test_every_node_with_upkeep_states_its_basis(self):
        for node_id, node in self.nodes.items():
            if node["up_hours"] > 0:
                self.assertIn(node.get("_upkeep_basis"), ("derived", "default", "programme", "staff", "authored"), node_id)

    def test_every_output_node_has_derived_upkeep(self):
        output = [node_id for node_id, node in self.nodes.items() if node.get("_revenue_basis") == "output"]
        self.assertGreater(len(output), 20)
        for node_id in output:
            self.assertEqual(self.nodes[node_id]["_upkeep_basis"], "derived", node_id)

    def test_derived_upkeep_is_staff_wages_plus_plant_maintenance(self):
        for node_id, node in self.derived().items():
            staff = sum(self.wages[trade] * hours
                        for trade, hours in node["_labour_hours_per_year"].items()) / self.rate
            parts = node["_upkeep_hours_parts"]
            plant = node_upkeep.maintenance_hours(node, parts["plant_build_hours"], parts["plant_wear_hours"])
            self.assertAlmostEqual(node["up_hours"], staff + plant,
                                   delta=1e-6 * max(1.0, node["up_hours"]), msg=node_id)
            self.assertAlmostEqual(node["_upkeep_hours_parts"]["staff"], staff,
                                   delta=1e-6 * max(1.0, staff), msg=node_id)
            if node["_labour_hours_per_year"]:
                self.assertGreater(node["up_hours"], 0.0, node_id)

    def test_plant_is_the_capital_the_entries_state_priced_at_solved_prices(self):
        blast = self.nodes["blast_furnace"]
        capital = [good for entry in production_data().values() if entry.get("requires_node") == "blast_furnace"
                   for good in entry.get("capital") or []]
        self.assertGreater(len(capital), 1)
        build = sum(self.goods.get(material, 0.0) * quantity
                    for good in capital for material, quantity in good["build_materials"].items())
        build += sum(self.wages[trade] * hours
                     for good in capital for trade, hours in good.get("build_labour_hours", {}).items())
        self.assertAlmostEqual(blast["_upkeep_hours_parts"]["plant_build_hours"], build / self.rate,
                               delta=1e-6 * build / self.rate)

    def test_an_entry_that_states_no_capital_keeps_no_plant_up(self):
        capital_light = [node for node in self.derived().values()
                         if node["_upkeep_hours_parts"]["plant_build_hours"] == 0.0]
        for node in capital_light:      # every output-earning node now states a plant, so this may be empty
            self.assertEqual(node["_upkeep_hours_parts"]["plant"], 0.0, node["id"])

    def test_derived_upkeep_does_not_read_the_authored_figure(self):
        changed = copy.deepcopy(self.nodes)
        for node in changed.values():
            node["up_hours"] = 1e9
            node["_up_hours_authored"] = 1e9
        energy = energy_prices.graded(data.load_civ()["starting_techs"], self.document, self.goods)
        node_revenue.apply_revenue(changed.values(), self.goods, self.wages, self.rate, energy)
        for node_id, node in self.derived().items():
            self.assertAlmostEqual(changed[node_id]["up_hours"], node["up_hours"],
                                   delta=1e-9 * max(1.0, node["up_hours"]), msg=node_id)

    def test_no_node_types_a_positive_upkeep(self):
        self.assertEqual([node["id"] for node in self.nodes.values()
                          if node.get("_upkeep_basis") == "authored"], [])

    def test_a_programme_costs_what_its_labour_and_consumables_cost(self):
        node = {"annual_labour_hours": {"labourer": 10.0}, "annual_consumables": {"wheat_kg": 100.0}}
        wages, goods = {"labourer": 2.0}, {"wheat_kg": 0.5}
        self.assertAlmostEqual(node_upkeep.programme_spending_hours(node, goods, wages, 2.0), (20.0 + 50.0) / 2.0)

    def test_the_maintenance_share_is_a_declared_fraction_of_the_build_cost(self):
        for kind in ("INFRASTRUCTURE", "ENGINEERING", "RESOURCE", None):
            hours = node_upkeep.maintenance_hours({"kind": kind}, 1000.0)
            self.assertGreater(hours, 0.0)
            self.assertLess(hours, 100.0)

    def test_no_derived_node_runs_at_a_loss_before_the_market_moves(self):
        losing = [node_id for node_id, node in self.derived().items()
                  if node["rev_hours"] < node["up_hours"] * (1 - 1e-9)]
        self.assertEqual(losing, [])

    def test_plant_upkeep_is_never_more_than_the_wear_the_price_already_charges(self):
        for node_id, node in self.derived().items():
            parts = node["_upkeep_hours_parts"]
            self.assertLessEqual(parts["plant"], parts["plant_wear_hours"] * (1 + 1e-9), node_id)

    def test_maintenance_is_capped_at_the_wear(self):
        self.assertEqual(node_upkeep.maintenance_hours({"kind": "ENGINEERING"}, 1000.0, 5.0), 5.0)
        self.assertGreater(node_upkeep.maintenance_hours({"kind": "ENGINEERING"}, 1000.0, 1e9), 5.0)


if __name__ == "__main__":
    unittest.main()
