"""Researching a technique that gates production changes the derived figures of the nodes that use it
(Complaints/317): the Sim re-derives when its held gate set changes, and a save keeps the result."""
import os
import random
import tempfile
import unittest

from sim import simulator
from sim.engine import node_revenue, prices
from sim.engine.saveload import load_state, save_state

CIVILISATION = "rome_100ad"


def make_sim():
    _tree, _prices, nodes, _wages, _goods = simulator.load()
    sim = simulator.Sim(nodes, [], random.Random(1), events=False, manual=True,
                        civ=simulator.load_civ(CIVILISATION))
    sim.goal, sim.done_year = sorted(nodes)[0], {}
    return sim


def research(sim, tech_ids):
    for tech_id in tech_ids:
        sim.state.projects.done.add(tech_id)
    sim._done_changed()


def figures(sim):
    return {node_id: node.get("rev_hours") for node_id, node in sim.nodes.items()}


class RederivesOnResearch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sim = make_sim()
        cls.start = set(cls.sim.state.projects.done)
        cls.before = figures(cls.sim)
        cls.learned = sorted(prices.all_gate_nodes() - cls.start)
        research(cls.sim, cls.learned)
        node_revenue.derivation_calls.clear()
        cls.sim.refresh_derived_nodes()
        cls.derivations = len(node_revenue.derivation_calls)
        cls.after = figures(cls.sim)

    def test_a_new_gate_set_derives_once_and_moves_a_dependent_figure(self):
        self.assertLessEqual(self.derivations, 1)
        self.assertTrue([node_id for node_id in self.before if self.before[node_id] != self.after[node_id]])

    def test_money_fields_follow_the_hours(self):
        rate = self.sim.labour.money_per_labour_hour()
        for node_id, node in self.sim.nodes.items():
            self.assertAlmostEqual(node["rev"], node["rev_hours"] * rate, delta=1e-6 * max(1.0, node["rev"]), msg=node_id)

    def test_nothing_is_derived_again_while_the_gate_set_is_unchanged(self):
        node_revenue.derivation_calls.clear()
        research(self.sim, ["a_tech_that_gates_no_technique"])
        self.sim.refresh_derived_nodes()
        self.assertEqual(node_revenue.derivation_calls, [])

    def test_a_loaded_save_has_the_figures_of_the_techniques_it_holds(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "game.json")
            save_state(self.sim, path)
            revived = make_sim()
            load_state(revived, path)
        self.assertEqual(figures(revived), self.after)


if __name__ == "__main__":
    unittest.main()
