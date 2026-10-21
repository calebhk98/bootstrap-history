"""Scenario: a Sim of a civilisation carries that civilisation's derived revenue and upkeep (Complaints/310). The rules
are in test_node_revenue_per_civ."""
import random
import unittest

from sim import simulator
from sim.engine import data
from sim.tests.harness import build_unopened


class SimCarriesItsCivilisation(unittest.TestCase):

    def test_a_sim_carries_the_derivation_of_its_own_civilisation(self):
        civilization_id = "han_china_100ad"
        _tree, _document, own, _wages, _goods = data.load(civilization_id=civilization_id)
        rate = data.starting_schedule(civilization_id).money_per_labour_hour
        _tree, _prices, nodes, _wages, _goods = simulator.load()
        sim = build_unopened(lambda: simulator.Sim(nodes, [], random.Random(1), events=False, manual=True,
                                                   civ=simulator.load_civ(civilization_id)))
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

    def test_the_reference_civilisation_reuses_the_tree_it_was_loaded_with(self):
        _tree, _prices, nodes, _wages, _goods = simulator.load()
        reference = simulator.load_civ()
        sim = build_unopened(lambda: simulator.Sim(nodes, [], random.Random(1), events=False, manual=True, civ=reference))
        self.assertEqual(sim.nodes["blast_furnace"]["rev_hours"], nodes["blast_furnace"]["rev_hours"])


if __name__ == "__main__":
    unittest.main()
