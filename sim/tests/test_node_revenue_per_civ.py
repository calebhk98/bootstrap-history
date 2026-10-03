"""Derived revenue and upkeep are priced for the civilisation playing, from what it can make and buy.

Complaints/310: the baskets were solved once at the reference civilisation's techniques and shared."""
import random
import unittest

from sim import simulator
from sim.engine import data, node_revenue


def sim_for(civilization_id):
    _tree, _prices, nodes, _wages, _goods = simulator.load()
    return simulator.Sim(nodes, [], random.Random(1), events=False, manual=True,
                         civ=simulator.load_civ(civilization_id))


class PerCivilisation(unittest.TestCase):

    def test_a_sim_carries_the_derivation_of_its_own_civilisation(self):
        civilization_id = "han_china_100ad"
        _tree, _document, own, _wages, _goods = data.load(civilization_id=civilization_id)
        rate = data.starting_schedule(civilization_id).money_per_labour_hour
        sim = sim_for(civilization_id)
        compared = 0
        for node_id, node in own.items():
            if node.get("_revenue_basis") != "output":
                continue
            self.assertEqual(sim.nodes[node_id]["_revenue_basis"], "output", node_id)
            self.assertAlmostEqual(sim.nodes[node_id]["rev"], node["rev_hours"] * rate,
                                   delta=1e-6 * max(1.0, node["rev"]), msg=node_id)
            self.assertAlmostEqual(sim.nodes[node_id]["up"], node["up_hours"] * rate,
                                   delta=1e-6 * max(1.0, node["up"]), msg=node_id)
            compared += 1
        self.assertGreater(compared, 20)

    def test_two_civilisations_do_not_share_a_derived_figure_when_their_prices_differ(self):
        rome, han = sim_for("rome_100ad"), sim_for("han_china_100ad")
        rome_hours = {node_id: node["rev"] / rome.labour.money_per_labour_hour()
                      for node_id, node in rome.nodes.items() if node.get("_revenue_basis") == "output"}
        han_hours = {node_id: han.nodes[node_id]["rev"] / han.labour.money_per_labour_hour() for node_id in rome_hours}
        self.assertTrue(any(abs(rome_hours[node_id] - han_hours[node_id]) > 1e-6 * max(1.0, rome_hours[node_id])
                            for node_id in rome_hours))

    def test_the_reference_civilisation_reuses_the_tree_it_was_loaded_with(self):
        _tree, _prices, nodes, _wages, _goods = simulator.load()
        reference = simulator.load_civ()
        sim = simulator.Sim(nodes, [], random.Random(1), events=False, manual=True, civ=reference)
        self.assertEqual(sim.nodes["blast_furnace"]["rev_hours"], nodes["blast_furnace"]["rev_hours"])

    def test_the_derivation_is_cached_on_what_it_depends_on(self):
        civilization_id = "han_china_100ad"
        sim_for(civilization_id)
        node_revenue.derivation_calls.clear()
        sim_for(civilization_id)
        self.assertEqual(node_revenue.derivation_calls, [], "a second sim of the same civilisation re-derived")

    def test_a_node_the_civilisation_cannot_derive_keeps_its_authored_basis(self):
        sim = sim_for("han_china_100ad")
        for node_id, node in sim.nodes.items():
            self.assertIn(node.get("_revenue_basis", "authored"), ("output", "authored", "knowledge"), node_id)


if __name__ == "__main__":
    unittest.main()
